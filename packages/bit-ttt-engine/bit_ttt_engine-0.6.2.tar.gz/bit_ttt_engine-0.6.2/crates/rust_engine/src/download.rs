//! Fast Parallel Downloader with Resume Support
//!
//! High-speed file downloads using:
//! - Parallel chunk downloads (HTTP Range)
//! - Automatic resume from interruption
//! - Progress tracking
//! - HuggingFace Hub integration

use anyhow::{anyhow, Result};
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Download configuration
#[derive(Clone)]
pub struct DownloadConfig {
    /// Number of parallel connections
    pub num_connections: usize,
    /// Chunk size for progress updates (bytes)
    pub chunk_size: usize,
    /// Connection timeout
    pub timeout: Duration,
    /// Enable resume from partial download
    pub resume: bool,
    /// Show progress
    pub show_progress: bool,
}

impl Default for DownloadConfig {
    fn default() -> Self {
        Self {
            num_connections: 8,
            chunk_size: 1024 * 1024, // 1MB
            timeout: Duration::from_secs(300),
            resume: true,
            show_progress: true,
        }
    }
}

/// Progress callback type
pub type ProgressCallback = Box<dyn Fn(u64, u64) + Send + Sync>;

/// Fast parallel downloader
pub struct FastDownloader {
    config: DownloadConfig,
    client: reqwest::blocking::Client,
}

impl FastDownloader {
    /// Create new downloader with default config
    pub fn new() -> Result<Self> {
        Self::with_config(DownloadConfig::default())
    }

    /// Create downloader with custom config
    pub fn with_config(config: DownloadConfig) -> Result<Self> {
        let client = reqwest::blocking::Client::builder()
            .timeout(config.timeout)
            .redirect(reqwest::redirect::Policy::limited(10))
            .build()?;

        Ok(Self { config, client })
    }

    /// Download a file with parallel connections
    pub fn download(&self, url: &str, dest: &Path) -> Result<()> {
        self.download_with_progress(url, dest, None)
    }

    /// Download with progress callback
    pub fn download_with_progress(
        &self,
        url: &str,
        dest: &Path,
        progress: Option<ProgressCallback>,
    ) -> Result<()> {
        // Get file size
        let total_size = self.get_content_length(url)?;

        if self.config.show_progress {
            println!(
                "📥 Downloading: {} ({:.2} MB)",
                url.split('/').next_back().unwrap_or("file"),
                total_size as f64 / 1024.0 / 1024.0
            );
        }

        // Check for existing partial download
        let start_byte = if self.config.resume && dest.exists() {
            let existing_size = std::fs::metadata(dest)?.len();
            if existing_size >= total_size {
                if self.config.show_progress {
                    println!("✅ File already complete");
                }
                return Ok(());
            }
            if self.config.show_progress {
                println!(
                    "🔄 Resuming from {:.2} MB",
                    existing_size as f64 / 1024.0 / 1024.0
                );
            }
            existing_size
        } else {
            0
        };

        // For small files or single connection, use simple download
        if total_size < 10 * 1024 * 1024 || self.config.num_connections == 1 {
            return self.simple_download(url, dest, start_byte, total_size, progress);
        }

        // Parallel download
        self.parallel_download(url, dest, start_byte, total_size, progress)
    }

    /// Simple single-connection download with resume
    fn simple_download(
        &self,
        url: &str,
        dest: &Path,
        start_byte: u64,
        total_size: u64,
        progress: Option<ProgressCallback>,
    ) -> Result<()> {
        let mut request = self.client.get(url);

        if start_byte > 0 {
            request = request.header("Range", format!("bytes={}-", start_byte));
        }

        let mut response = request.send()?;

        if !response.status().is_success() && response.status().as_u16() != 206 {
            return Err(anyhow!("HTTP error: {}", response.status()));
        }

        let mut file = if start_byte > 0 {
            OpenOptions::new().append(true).open(dest)?
        } else {
            File::create(dest)?
        };

        let mut downloaded = start_byte;
        let mut buffer = vec![0u8; self.config.chunk_size];
        let start_time = Instant::now();
        let mut last_print = Instant::now();

        loop {
            let bytes_read = response.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }

            file.write_all(&buffer[..bytes_read])?;
            downloaded += bytes_read as u64;

            if let Some(ref cb) = progress {
                cb(downloaded, total_size);
            }

            // Print progress every 500ms
            if self.config.show_progress && last_print.elapsed() > Duration::from_millis(500) {
                let elapsed = start_time.elapsed().as_secs_f64();
                let speed = (downloaded - start_byte) as f64 / elapsed / 1024.0 / 1024.0;
                let percent = downloaded as f64 / total_size as f64 * 100.0;
                print!("\r  Progress: {:.1}% ({:.2} MB/s)    ", percent, speed);
                std::io::stdout().flush()?;
                last_print = Instant::now();
            }
        }

        if self.config.show_progress {
            let elapsed = start_time.elapsed().as_secs_f64();
            let speed = (downloaded - start_byte) as f64 / elapsed / 1024.0 / 1024.0;
            println!(
                "\r✅ Complete: {:.2} MB in {:.1}s ({:.2} MB/s)    ",
                total_size as f64 / 1024.0 / 1024.0,
                elapsed,
                speed
            );
        }

        Ok(())
    }

    /// Parallel multi-connection download
    fn parallel_download(
        &self,
        url: &str,
        dest: &Path,
        start_byte: u64,
        total_size: u64,
        progress: Option<ProgressCallback>,
    ) -> Result<()> {
        use std::thread;

        let remaining = total_size - start_byte;
        let chunk_size = remaining / self.config.num_connections as u64;

        // Create temp directory for chunks
        let temp_dir = dest
            .parent()
            .unwrap_or(Path::new("."))
            .join(".download_temp");
        std::fs::create_dir_all(&temp_dir)?;

        let downloaded = Arc::new(AtomicU64::new(start_byte));
        let start_time = Instant::now();

        // Spawn download threads
        let handles: Vec<_> = (0..self.config.num_connections)
            .map(|i| {
                let url = url.to_string();
                let temp_dir = temp_dir.clone();
                let downloaded = Arc::clone(&downloaded);
                let chunk_start = start_byte + i as u64 * chunk_size;
                let chunk_end = if i == self.config.num_connections - 1 {
                    total_size - 1
                } else {
                    start_byte + (i as u64 + 1) * chunk_size - 1
                };
                let timeout = self.config.timeout;
                let buffer_size = self.config.chunk_size;

                thread::spawn(move || -> Result<PathBuf> {
                    let client = reqwest::blocking::Client::builder()
                        .timeout(timeout)
                        .build()?;

                    let chunk_path = temp_dir.join(format!("chunk_{}", i));

                    // Check if chunk already exists
                    let existing_size = if chunk_path.exists() {
                        std::fs::metadata(&chunk_path)?.len()
                    } else {
                        0
                    };

                    let actual_start = chunk_start + existing_size;
                    if actual_start > chunk_end {
                        return Ok(chunk_path);
                    }

                    let response = client
                        .get(&url)
                        .header("Range", format!("bytes={}-{}", actual_start, chunk_end))
                        .send()?;

                    if !response.status().is_success() && response.status().as_u16() != 206 {
                        return Err(anyhow!("HTTP error: {}", response.status()));
                    }

                    let mut file = if existing_size > 0 {
                        OpenOptions::new().append(true).open(&chunk_path)?
                    } else {
                        File::create(&chunk_path)?
                    };

                    let mut reader = response;
                    let mut buffer = vec![0u8; buffer_size];

                    loop {
                        let bytes_read = reader.read(&mut buffer)?;
                        if bytes_read == 0 {
                            break;
                        }
                        file.write_all(&buffer[..bytes_read])?;
                        downloaded.fetch_add(bytes_read as u64, Ordering::Relaxed);
                    }

                    Ok(chunk_path)
                })
            })
            .collect();

        // Wait for all downloads (no separate progress thread for simplicity)
        let num_connections = self.config.num_connections;
        let mut chunk_paths = Vec::new();
        let show_progress = self.config.show_progress;

        for handle in handles {
            // Show progress while waiting
            if show_progress {
                let current = downloaded.load(Ordering::Relaxed);
                let elapsed = start_time.elapsed().as_secs_f64();
                let speed = if elapsed > 0.0 {
                    current as f64 / elapsed / 1024.0 / 1024.0
                } else {
                    0.0
                };
                let percent = current as f64 / total_size as f64 * 100.0;
                print!(
                    "\r  Progress: {:.1}% ({:.2} MB/s) [{} connections]    ",
                    percent, speed, num_connections
                );
                let _ = std::io::stdout().flush();
            }

            let chunk_path = handle.join().map_err(|_| anyhow!("Thread panicked"))??;
            chunk_paths.push(chunk_path);
        }

        // Merge chunks
        if self.config.show_progress {
            print!("\r  Merging chunks...                                    ");
            std::io::stdout().flush()?;
        }

        let mut output = if start_byte > 0 {
            OpenOptions::new().append(true).open(dest)?
        } else {
            File::create(dest)?
        };

        for chunk_path in &chunk_paths {
            let mut chunk = File::open(chunk_path)?;
            std::io::copy(&mut chunk, &mut output)?;
        }

        // Cleanup temp files
        std::fs::remove_dir_all(&temp_dir)?;

        if self.config.show_progress {
            let elapsed = start_time.elapsed().as_secs_f64();
            let speed = total_size as f64 / elapsed / 1024.0 / 1024.0;
            println!(
                "\r✅ Complete: {:.2} MB in {:.1}s ({:.2} MB/s)                    ",
                total_size as f64 / 1024.0 / 1024.0,
                elapsed,
                speed
            );
        }

        if let Some(cb) = progress {
            cb(total_size, total_size);
        }

        Ok(())
    }

    /// Get content length and resolve final URL (after redirects)
    fn get_content_length(&self, url: &str) -> Result<u64> {
        let response = self.client.head(url).send()?;

        if !response.status().is_success() {
            return Err(anyhow!("HTTP error: {}", response.status()));
        }

        response
            .headers()
            .get("content-length")
            .and_then(|v| v.to_str().ok())
            .and_then(|v| v.parse().ok())
            .ok_or_else(|| anyhow!("Cannot determine file size"))
    }

    /// Resolve final URL after redirects
    #[allow(dead_code)]
    fn resolve_url(&self, url: &str) -> Result<String> {
        let response = self.client.head(url).send()?;

        if !response.status().is_success() {
            return Err(anyhow!("HTTP error: {}", response.status()));
        }

        Ok(response.url().to_string())
    }

    /// Check if server supports range requests
    #[allow(dead_code)]
    fn supports_range(&self, url: &str) -> Result<bool> {
        let response = self.client.head(url).send()?;
        Ok(response
            .headers()
            .get("accept-ranges")
            .map(|v| v.to_str().unwrap_or("") == "bytes")
            .unwrap_or(false))
    }
}

/// Download from HuggingFace Hub
pub struct HfDownloader {
    downloader: FastDownloader,
    base_url: String,
}

impl HfDownloader {
    pub fn new() -> Result<Self> {
        Ok(Self {
            downloader: FastDownloader::new()?,
            base_url: std::env::var("HF_ENDPOINT")
                .unwrap_or_else(|_| "https://huggingface.co".to_string()),
        })
    }

    /// Download a model file from HuggingFace
    pub fn download_file(
        &self,
        repo_id: &str,
        filename: &str,
        dest_dir: &Path,
        revision: Option<&str>,
    ) -> Result<PathBuf> {
        let revision = revision.unwrap_or("main");
        let url = format!(
            "{}/{}/resolve/{}/{}",
            self.base_url, repo_id, revision, filename
        );

        let dest_path = dest_dir.join(filename);
        if let Some(parent) = dest_path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        self.downloader.download(&url, &dest_path)?;
        Ok(dest_path)
    }

    /// Download multiple files from a repo
    pub fn download_repo(
        &self,
        repo_id: &str,
        files: &[&str],
        dest_dir: &Path,
        revision: Option<&str>,
    ) -> Result<Vec<PathBuf>> {
        let mut paths = Vec::new();

        println!("📦 Downloading {} files from {}", files.len(), repo_id);

        for (i, filename) in files.iter().enumerate() {
            println!("\n[{}/{}] {}", i + 1, files.len(), filename);
            let path = self.download_file(repo_id, filename, dest_dir, revision)?;
            paths.push(path);
        }

        println!("\n✅ All files downloaded to {:?}", dest_dir);
        Ok(paths)
    }
}

impl Default for FastDownloader {
    fn default() -> Self {
        Self::new().expect("Failed to create downloader")
    }
}

impl Default for HfDownloader {
    fn default() -> Self {
        Self::new().expect("Failed to create HF downloader")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    #[test]
    fn test_download_config_default() {
        let config = DownloadConfig::default();
        assert_eq!(config.num_connections, 8);
        assert!(config.resume);
    }

    #[test]
    #[ignore] // Requires network
    fn test_simple_download() {
        let downloader = FastDownloader::new().unwrap();
        let dest = temp_dir().join("test_download.txt");

        // Small test file
        let url = "https://huggingface.co/gpt2/resolve/main/config.json";
        downloader.download(url, &dest).unwrap();

        assert!(dest.exists());
        std::fs::remove_file(&dest).ok();
    }
}
