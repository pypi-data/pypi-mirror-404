//! Knowledge Pack Format Module
//! 
//! Handles reading, writing, and managing .u32k knowledge pack files.
//! Supports compression, checksums, and metadata.

pub mod reader;
pub mod writer;
pub mod verify;
pub mod install;
pub mod types;

pub use reader::PackReader;
pub use writer::PackWriter;
pub use verify::PackVerifier;
pub use install::PackInstaller;
pub use types::{PackMetadata, PackFile, PackHeader, PackInfo};

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Knowledge pack version
pub const PACK_VERSION: u8 = 1;

/// Magic number for pack format
pub const PACK_MAGIC: &[u8; 4] = b"U32K";

/// Default pack directory
pub fn default_pack_dir() -> PathBuf {
    #[cfg(target_os = "windows")]
    {
        let home = std::env::var("USERPROFILE").unwrap_or_else(|_| ".".to_string());
        PathBuf::from(home)
            .join(".clawdbot")
            .join("knowledge-packs")
    }
    #[cfg(not(target_os = "windows"))]
    {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        PathBuf::from(home)
            .join(".clawdbot")
            .join("knowledge-packs")
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackManifest {
    pub version: String,
    pub packs: Vec<PackInfo>,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistryEntry {
    pub pack_id: String,
    pub name: String,
    pub version: String,
    pub url: String,
    pub checksum: String,
    pub size: u64,
    pub description: String,
    pub author: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_pack_dir() {
        let dir = default_pack_dir();
        assert!(dir.to_string_lossy().contains("knowledge-packs"));
    }

    #[test]
    fn test_pack_magic() {
        assert_eq!(PACK_MAGIC, b"U32K");
        assert_eq!(PACK_VERSION, 1);
    }
}
