//! Scheduler - Continuous Batching Request Scheduler
//!
//! Manages multiple inference requests with dynamic batching.
//! Supports adding/removing requests mid-inference.
//!
//! # Architecture
//! - FIFO queue for pending requests
//! - Active batch with configurable max size
//! - Preemption support for priority requests (future)

use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

/// Unique request identifier
pub type RequestId = u64;

/// Request state
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RequestState {
    /// Waiting in queue
    Pending,
    /// Currently being processed
    Running,
    /// Completed successfully
    Completed,
    /// Failed with error
    Failed,
    /// Cancelled by user
    Cancelled,
}

/// Request priority (higher = more urgent)
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Default)]
pub enum Priority {
    Low = 0,
    #[default]
    Normal = 1,
    High = 2,
}

/// Inference request
#[derive(Debug, Clone)]
pub struct Request {
    /// Unique identifier
    pub id: RequestId,
    /// Input token IDs
    pub input_ids: Vec<u32>,
    /// Maximum tokens to generate
    pub max_tokens: usize,
    /// Tokens generated so far
    pub generated_tokens: Vec<u32>,
    /// Request priority
    pub priority: Priority,
    /// Current state
    pub state: RequestState,
    /// Creation time
    pub created_at: Instant,
    /// Sequence ID in block manager (if running)
    pub seq_id: Option<usize>,
}

impl Request {
    pub fn new(input_ids: Vec<u32>, max_tokens: usize) -> Self {
        static NEXT_ID: AtomicU64 = AtomicU64::new(0);
        Self {
            id: NEXT_ID.fetch_add(1, Ordering::SeqCst),
            input_ids,
            max_tokens,
            generated_tokens: Vec::new(),
            priority: Priority::Normal,
            state: RequestState::Pending,
            created_at: Instant::now(),
            seq_id: None,
        }
    }

    pub fn with_priority(mut self, priority: Priority) -> Self {
        self.priority = priority;
        self
    }

    /// Total sequence length (input + generated)
    pub fn seq_len(&self) -> usize {
        self.input_ids.len() + self.generated_tokens.len()
    }

    /// Check if generation is complete
    pub fn is_complete(&self) -> bool {
        self.generated_tokens.len() >= self.max_tokens
    }
}

/// Scheduler configuration
#[derive(Debug, Clone)]
pub struct SchedulerConfig {
    /// Maximum batch size (concurrent requests)
    pub max_batch_size: usize,
    /// Maximum pending queue size
    pub max_queue_size: usize,
    /// Maximum sequence length
    pub max_seq_len: usize,
}

impl Default for SchedulerConfig {
    fn default() -> Self {
        Self {
            max_batch_size: 8,
            max_queue_size: 64,
            max_seq_len: 2048,
        }
    }
}

/// Batch of requests currently being processed
#[derive(Debug, Default)]
pub struct Batch {
    /// Requests in this batch
    pub requests: Vec<Request>,
}

impl Batch {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn is_empty(&self) -> bool {
        self.requests.is_empty()
    }

    pub fn len(&self) -> usize {
        self.requests.len()
    }

    /// Get all request IDs
    pub fn request_ids(&self) -> Vec<RequestId> {
        self.requests.iter().map(|r| r.id).collect()
    }

    /// Get input IDs for all requests (for batched forward)
    /// Returns (batch_input_ids, seq_lens)
    pub fn get_inputs(&self) -> (Vec<Vec<u32>>, Vec<usize>) {
        let inputs: Vec<Vec<u32>> = self
            .requests
            .iter()
            .map(|r| {
                if r.generated_tokens.is_empty() {
                    // Prefill: use input_ids
                    r.input_ids.clone()
                } else {
                    // Decode: use last generated token
                    vec![*r.generated_tokens.last().unwrap()]
                }
            })
            .collect();
        let seq_lens: Vec<usize> = inputs.iter().map(|i| i.len()).collect();
        (inputs, seq_lens)
    }
}

/// Continuous batching scheduler
pub struct Scheduler {
    /// Configuration
    config: SchedulerConfig,
    /// Pending request queue
    pending: VecDeque<Request>,
    /// Currently running batch
    running: Batch,
    /// Completed requests (for retrieval)
    completed: Vec<Request>,
}

impl Scheduler {
    pub fn new(config: SchedulerConfig) -> Self {
        Self {
            config,
            pending: VecDeque::new(),
            running: Batch::new(),
            completed: Vec::new(),
        }
    }

    /// Add a new request to the queue
    /// Returns the request ID
    pub fn add_request(&mut self, request: Request) -> Result<RequestId, String> {
        if self.pending.len() >= self.config.max_queue_size {
            return Err("Queue is full".to_string());
        }
        let id = request.id;
        self.pending.push_back(request);
        Ok(id)
    }

    /// Cancel a pending or running request
    pub fn cancel_request(&mut self, id: RequestId) -> bool {
        // Check pending queue
        if let Some(pos) = self.pending.iter().position(|r| r.id == id) {
            let mut request = self.pending.remove(pos).unwrap();
            request.state = RequestState::Cancelled;
            self.completed.push(request);
            return true;
        }

        // Check running batch
        if let Some(pos) = self.running.requests.iter().position(|r| r.id == id) {
            let mut request = self.running.requests.remove(pos);
            request.state = RequestState::Cancelled;
            self.completed.push(request);
            return true;
        }

        false
    }

    /// Schedule next batch of requests
    /// Moves requests from pending to running
    pub fn schedule(&mut self) -> &Batch {
        // Fill running batch up to max_batch_size
        while self.running.len() < self.config.max_batch_size {
            if let Some(mut request) = self.pending.pop_front() {
                request.state = RequestState::Running;
                self.running.requests.push(request);
            } else {
                break;
            }
        }
        &self.running
    }

    /// Update batch with generated tokens
    /// Moves completed requests to completed queue
    pub fn update_batch(&mut self, generated: Vec<(RequestId, u32)>) {
        for (id, token) in generated {
            if let Some(request) = self.running.requests.iter_mut().find(|r| r.id == id) {
                request.generated_tokens.push(token);

                // Check for completion (max tokens or EOS)
                if request.is_complete() || token == 2 {
                    // 2 = typical EOS token
                    request.state = RequestState::Completed;
                }
            }
        }

        // Move completed requests
        let mut i = 0;
        while i < self.running.requests.len() {
            if self.running.requests[i].state == RequestState::Completed {
                let request = self.running.requests.remove(i);
                self.completed.push(request);
            } else {
                i += 1;
            }
        }
    }

    /// Get completed request by ID (removes from completed list)
    pub fn get_completed(&mut self, id: RequestId) -> Option<Request> {
        if let Some(pos) = self.completed.iter().position(|r| r.id == id) {
            Some(self.completed.remove(pos))
        } else {
            None
        }
    }

    /// Get all completed requests
    pub fn drain_completed(&mut self) -> Vec<Request> {
        std::mem::take(&mut self.completed)
    }

    /// Check if there's work to do
    pub fn has_work(&self) -> bool {
        !self.pending.is_empty() || !self.running.is_empty()
    }

    /// Get statistics
    pub fn stats(&self) -> SchedulerStats {
        SchedulerStats {
            pending_count: self.pending.len(),
            running_count: self.running.len(),
            completed_count: self.completed.len(),
        }
    }
}

/// Scheduler statistics
#[derive(Debug, Clone)]
pub struct SchedulerStats {
    pub pending_count: usize,
    pub running_count: usize,
    pub completed_count: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_creation() {
        let req = Request::new(vec![1, 2, 3], 10);
        assert_eq!(req.input_ids, vec![1, 2, 3]);
        assert_eq!(req.max_tokens, 10);
        assert_eq!(req.state, RequestState::Pending);
        assert!(req.generated_tokens.is_empty());
    }

    #[test]
    fn test_scheduler_add_request() {
        let config = SchedulerConfig::default();
        let mut scheduler = Scheduler::new(config);

        let req = Request::new(vec![1, 2, 3], 10);
        let _id = scheduler.add_request(req).unwrap();

        assert_eq!(scheduler.stats().pending_count, 1);
        assert_eq!(scheduler.stats().running_count, 0);
    }

    #[test]
    fn test_scheduler_schedule() {
        let config = SchedulerConfig {
            max_batch_size: 2,
            ..Default::default()
        };
        let mut scheduler = Scheduler::new(config);

        // Add 3 requests
        scheduler.add_request(Request::new(vec![1], 5)).unwrap();
        scheduler.add_request(Request::new(vec![2], 5)).unwrap();
        scheduler.add_request(Request::new(vec![3], 5)).unwrap();

        // Schedule should move 2 to running
        let batch = scheduler.schedule();
        assert_eq!(batch.len(), 2);
        assert_eq!(scheduler.stats().pending_count, 1);
        assert_eq!(scheduler.stats().running_count, 2);
    }

    #[test]
    fn test_scheduler_update_and_complete() {
        let config = SchedulerConfig::default();
        let mut scheduler = Scheduler::new(config);

        let req = Request::new(vec![1], 2); // max 2 tokens
        let id = scheduler.add_request(req).unwrap();
        scheduler.schedule();

        // Generate 2 tokens
        scheduler.update_batch(vec![(id, 100)]);
        assert_eq!(scheduler.stats().running_count, 1);

        scheduler.update_batch(vec![(id, 101)]);
        assert_eq!(scheduler.stats().running_count, 0);
        assert_eq!(scheduler.stats().completed_count, 1);

        // Retrieve completed
        let completed = scheduler.get_completed(id).unwrap();
        assert_eq!(completed.generated_tokens, vec![100, 101]);
        assert_eq!(completed.state, RequestState::Completed);
    }

    #[test]
    fn test_scheduler_cancel() {
        let config = SchedulerConfig::default();
        let mut scheduler = Scheduler::new(config);

        let req = Request::new(vec![1], 10);
        let id = scheduler.add_request(req).unwrap();

        assert!(scheduler.cancel_request(id));
        assert_eq!(scheduler.stats().pending_count, 0);
        assert_eq!(scheduler.stats().completed_count, 1);

        let cancelled = scheduler.get_completed(id).unwrap();
        assert_eq!(cancelled.state, RequestState::Cancelled);
    }
}
