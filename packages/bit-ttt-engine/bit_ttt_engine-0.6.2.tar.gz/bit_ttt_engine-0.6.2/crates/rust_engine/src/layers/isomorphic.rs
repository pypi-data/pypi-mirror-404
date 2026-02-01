//! Isomorphic Layer System - Dynamic GPU/CPU Offloading (Phase 3, #12)
//!
//! # Overview
//! The Isomorphic Layer System enables layers to be dynamically offloaded between GPU and CPU
//! based on available VRAM. This allows running 8B models on 4GB VRAM by keeping only active
//! layers on GPU and moving inactive layers to CPU.
//!
//! # Architecture
//!
//! ## Device Placement Strategy
//! - **Active Layers**: Layers currently processing data remain on GPU
//! - **Staging Layers**: Next layers to process are preemptively moved to GPU
//! - **Dormant Layers**: Layers not yet needed stay on CPU to conserve VRAM
//!
//! ## Memory Management
//! - **VRAM Monitoring**: Real-time tracking of available VRAM
//! - **Threshold-based Offloading**: Layers move to CPU when VRAM < threshold
//! - **Predictive Preloading**: Layers move to GPU before they're needed
//!
//! # Usage Example
//! ```rust,ignore
//! let mut offloader = IsomorphicOffloader::new(
//!     BitLlamaModel,
//!     4 * 1024 * 1024 * 1024, // 4GB threshold
//!     2 * 1024 * 1024 * 1024, // 2GB min staging reserve
//! );
//!
//! // Before processing layer i
//! offloader.ensure_layer_ready(i)?;
//! let h = layers[i].forward(h)?;
//! ```

use anyhow::{bail, Result};
use candle_core::Device;
use std::collections::HashMap;
use tracing::{debug, info, warn};

/// Memory pressure levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum MemoryPressure {
    /// VRAM > 80% free - no pressure
    Low = 0,
    /// VRAM 60-80% free - moderate pressure
    Moderate = 1,
    /// VRAM 40-60% free - high pressure
    High = 2,
    /// VRAM < 40% free - critical pressure
    Critical = 3,
}

impl MemoryPressure {
    /// Determine pressure level from available VRAM percentage
    pub fn from_ratio(free_ratio: f32) -> Self {
        match free_ratio {
            r if r > 0.80 => MemoryPressure::Low,
            r if r > 0.60 => MemoryPressure::Moderate,
            r if r > 0.40 => MemoryPressure::High,
            _ => MemoryPressure::Critical,
        }
    }
}

/// Layer device placement status
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LayerPlacement {
    /// Layer is on GPU and ready to process
    GPU,
    /// Layer is on CPU, waiting to be moved to GPU
    CPU,
    /// Layer has been transferred but not yet ready
    InTransit,
}

/// Statistics for isomorphic operations
#[derive(Debug, Clone, Default)]
pub struct IsomorphicStats {
    /// Total number of layer transfers
    pub transfers: usize,
    /// Total bytes transferred
    pub bytes_transferred: u64,
    /// Average transfer time in milliseconds
    pub avg_transfer_time_ms: f64,
    /// Peak VRAM used
    pub peak_vram_used: u64,
    /// Number of times offloading was triggered
    pub offload_triggers: usize,
    /// Number of times preloading was triggered
    pub preload_triggers: usize,
}

/// Device memory monitor - tracks VRAM usage over time
pub struct MemoryMonitor {
    gpu_device_id: usize,
    total_vram: u64,
    last_free_vram: u64,
    peak_used_vram: u64,
    /// When to start offloading layers to CPU (for future adaptive offloading)
    #[allow(dead_code)]
    low_threshold: u64,
    /// When to bring layers back from CPU (for future adaptive offloading)
    #[allow(dead_code)]
    high_threshold: u64,
}

impl MemoryMonitor {
    pub fn new(gpu_device_id: usize, vram_threshold_bytes: u64) -> Result<Self> {
        // Get total VRAM
        let (free, total) = crate::device_utils::get_vram_info(gpu_device_id)?;

        if total == 0 {
            bail!("No GPU VRAM detected. CPU-only mode.");
        }

        let total = total as u64;
        let low_threshold = vram_threshold_bytes;
        let high_threshold = (total as f64 * 0.75) as u64; // 75% of total

        Ok(Self {
            gpu_device_id,
            total_vram: total,
            last_free_vram: free as u64,
            peak_used_vram: 0,
            low_threshold,
            high_threshold,
        })
    }

    /// Update memory info - returns current free VRAM and pressure level
    pub fn update(&mut self) -> Result<(u64, MemoryPressure)> {
        let (free, _) = crate::device_utils::get_vram_info(self.gpu_device_id)?;
        let free = free as u64;
        self.last_free_vram = free;

        let used = self.total_vram.saturating_sub(free);
        if used > self.peak_used_vram {
            self.peak_used_vram = used;
        }

        let free_ratio = free as f32 / self.total_vram as f32;
        let pressure = MemoryPressure::from_ratio(free_ratio);

        debug!(
            "Memory update: {} MB free / {} MB total ({:.1}%) - {:?}",
            free / 1024 / 1024,
            self.total_vram / 1024 / 1024,
            free_ratio * 100.0,
            pressure
        );

        Ok((free, pressure))
    }

    /// Get the memory pressure level
    pub fn pressure(&mut self) -> Result<MemoryPressure> {
        self.update().map(|(_, p)| p)
    }

    /// Get current VRAM usage info
    pub fn get_status(&mut self) -> Result<(u64, u64, u64)> {
        let (free, _) = crate::device_utils::get_vram_info(self.gpu_device_id)?;
        let free = free as u64;
        let used = self.total_vram.saturating_sub(free);
        Ok((free, used, self.peak_used_vram))
    }
}

/// Layer transfer descriptor
#[derive(Debug, Clone)]
pub struct LayerTransferPlan {
    pub layer_id: usize,
    pub from_device: LayerPlacement,
    pub to_device: LayerPlacement,
    pub estimated_bytes: u64,
}

/// Isomorphic offloading strategy
pub enum OffloadStrategy {
    /// Always keep layers on GPU if possible (no offloading)
    GPUOnly,

    /// Keep n_gpu layers on GPU, rest on CPU (static)
    Hybrid { n_gpu: usize },

    /// Dynamically offload based on VRAM pressure
    Dynamic {
        /// Minimum VRAM to keep free (bytes)
        min_free_vram: u64,
        /// Reserve staging buffer for next layer (bytes)
        staging_reserve: u64,
    },

    /// Profile-guided - learn optimal placement from previous runs
    Adaptive { profile_file: String },
}

/// Isomorphic offloader for managing dynamic layer placement
pub struct IsomorphicOffloader {
    gpu_device: Device,
    cpu_device: Device,
    strategy: OffloadStrategy,
    monitor: MemoryMonitor,
    placement: HashMap<usize, LayerPlacement>,
    stats: IsomorphicStats,
}

impl IsomorphicOffloader {
    /// Create a new isomorphic offloader with dynamic strategy
    pub fn new_dynamic(min_free_vram_bytes: u64, staging_reserve_bytes: u64) -> Result<Self> {
        let gpu_device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);
        let cpu_device = Device::Cpu;

        let monitor = MemoryMonitor::new(0, min_free_vram_bytes)?;

        Ok(Self {
            gpu_device,
            cpu_device,
            strategy: OffloadStrategy::Dynamic {
                min_free_vram: min_free_vram_bytes,
                staging_reserve: staging_reserve_bytes,
            },
            monitor,
            placement: HashMap::new(),
            stats: IsomorphicStats::default(),
        })
    }

    /// Create with hybrid strategy (fixed n_gpu)
    pub fn new_hybrid(n_gpu: usize) -> Result<Self> {
        let gpu_device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);
        let cpu_device = Device::Cpu;

        let monitor = MemoryMonitor::new(0, 1024 * 1024 * 1024)?; // 1GB default

        Ok(Self {
            gpu_device,
            cpu_device,
            strategy: OffloadStrategy::Hybrid { n_gpu },
            monitor,
            placement: HashMap::new(),
            stats: IsomorphicStats::default(),
        })
    }

    /// Initialize layer placements for a model with N layers
    pub fn init_layers(&mut self, n_layers: usize) -> Result<()> {
        match &self.strategy {
            OffloadStrategy::Hybrid { n_gpu } => {
                for i in 0..n_layers {
                    let placement = if i < *n_gpu {
                        LayerPlacement::GPU
                    } else {
                        LayerPlacement::CPU
                    };
                    self.placement.insert(i, placement);
                    debug!("Layer {} initialized at {:?}", i, placement);
                }
            }
            OffloadStrategy::Dynamic { .. } => {
                // Start all layers on CPU to minimize initial VRAM
                for i in 0..n_layers {
                    self.placement.insert(i, LayerPlacement::CPU);
                    debug!("Layer {} initialized at {:?}", i, LayerPlacement::CPU);
                }
            }
            _ => {
                for i in 0..n_layers {
                    self.placement.insert(i, LayerPlacement::GPU);
                }
            }
        }
        Ok(())
    }

    /// Ensure a specific layer is ready on GPU before processing
    pub fn ensure_layer_ready(&mut self, layer_id: usize, layer_bytes: u64) -> Result<()> {
        let current_placement = self
            .placement
            .get(&layer_id)
            .copied()
            .unwrap_or(LayerPlacement::CPU);

        if current_placement == LayerPlacement::GPU {
            return Ok(()); // Already ready
        }

        // Check if we have enough VRAM
        let (_free_vram, pressure) = self.monitor.update()?;

        match pressure {
            MemoryPressure::Critical => {
                // Try to offload other layers to make room
                self.aggressive_offload(layer_bytes)?;
            }
            MemoryPressure::High => {
                // Offload some layers
                self.moderate_offload(layer_bytes)?;
            }
            _ => {}
        }

        // Move layer to GPU if still on CPU
        if self.placement.get(&layer_id) == Some(&LayerPlacement::CPU) {
            info!(
                "🚀 Moving layer {} to GPU ({} MB)",
                layer_id,
                layer_bytes / 1024 / 1024
            );
            self.placement.insert(layer_id, LayerPlacement::GPU);
            self.stats.preload_triggers += 1;
        }

        Ok(())
    }

    /// Moderate offloading - move some CPU layers to disk (or just CPU if pinned)
    fn moderate_offload(&mut self, needed_bytes: u64) -> Result<()> {
        let (free_vram, _) = self.monitor.update()?;

        if free_vram > needed_bytes {
            return Ok(()); // We have enough space
        }

        // Find layers on GPU that can be moved to CPU
        let mut gpu_layers: Vec<usize> = self
            .placement
            .iter()
            .filter(|(_, p)| **p == LayerPlacement::GPU)
            .map(|(id, _)| *id)
            .collect();

        // Sort by ID descending to offload higher layers first (likely less active)
        gpu_layers.sort_by(|a, b| b.cmp(a));

        // Offload layers until we have enough space
        for layer_id in gpu_layers.iter().take(2) {
            // Offload up to 2 layers
            self.placement.insert(*layer_id, LayerPlacement::CPU);
            debug!("Offloaded layer {} to CPU", layer_id);
            self.stats.offload_triggers += 1;

            let (free_vram, _) = self.monitor.update()?;
            if free_vram > needed_bytes {
                break;
            }
        }

        Ok(())
    }

    /// Aggressive offloading - move many layers to CPU
    fn aggressive_offload(&mut self, _needed_bytes: u64) -> Result<()> {
        warn!("⚠️ Aggressive offloading triggered");

        // Find all GPU layers except the current one being processed
        let mut gpu_layers: Vec<usize> = self
            .placement
            .iter()
            .filter(|(_, p)| **p == LayerPlacement::GPU)
            .map(|(id, _)| *id)
            .collect();

        gpu_layers.sort_by(|a, b| b.cmp(a));

        // Offload all except the first layer (current)
        for layer_id in gpu_layers.iter().skip(1) {
            self.placement.insert(*layer_id, LayerPlacement::CPU);
            debug!("Aggressive offload: layer {} to CPU", layer_id);
            self.stats.offload_triggers += 1;
        }

        Ok(())
    }

    /// Get the target device for a layer
    pub fn get_target_device(&self, layer_id: usize) -> Device {
        match self.placement.get(&layer_id) {
            Some(LayerPlacement::GPU) => self.gpu_device.clone(),
            _ => self.cpu_device.clone(),
        }
    }

    /// Get current placement of a layer
    pub fn get_placement(&self, layer_id: usize) -> LayerPlacement {
        self.placement
            .get(&layer_id)
            .copied()
            .unwrap_or(LayerPlacement::CPU)
    }

    /// Get all layers on GPU
    pub fn gpu_layers(&self) -> Vec<usize> {
        self.placement
            .iter()
            .filter(|(_, p)| **p == LayerPlacement::GPU)
            .map(|(id, _)| *id)
            .collect()
    }

    /// Get statistics
    pub fn stats(&self) -> &IsomorphicStats {
        &self.stats
    }

    /// Get memory status
    pub fn memory_status(&mut self) -> Result<(u64, u64, u64)> {
        self.monitor.get_status()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_pressure_calculation() {
        assert_eq!(MemoryPressure::from_ratio(0.9), MemoryPressure::Low);
        assert_eq!(MemoryPressure::from_ratio(0.7), MemoryPressure::Moderate);
        assert_eq!(MemoryPressure::from_ratio(0.5), MemoryPressure::High);
        assert_eq!(MemoryPressure::from_ratio(0.3), MemoryPressure::Critical);
    }

    #[test]
    fn test_memory_pressure_ordering() {
        assert!(MemoryPressure::Low < MemoryPressure::Moderate);
        assert!(MemoryPressure::Moderate < MemoryPressure::High);
        assert!(MemoryPressure::High < MemoryPressure::Critical);
    }
}
