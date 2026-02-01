//! Type definitions for Knowledge Packs

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

/// Pack header structure (64 bytes)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackHeader {
    /// Magic number: "U32K"
    pub magic: [u8; 4],
    /// Pack format version (current: 1)
    pub version: u8,
    /// Flags: bit 0 = compression, bit 1 = encrypted
    pub flags: u8,
    /// Reserved for future use
    pub reserved: [u8; 2],
    /// Size of metadata section in bytes
    pub metadata_size: u32,
    /// Size of data section in bytes
    pub data_size: u32,
    /// SHA256 checksum of entire file (except this header)
    pub checksum: [u8; 32],
}

impl Default for PackHeader {
    fn default() -> Self {
        Self {
            magic: *b"U32K",
            version: 1,
            flags: 0,
            reserved: [0; 2],
            metadata_size: 0,
            data_size: 0,
            checksum: [0; 32],
        }
    }
}

/// Compression algorithm
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CompressionAlgo {
    None = 0,
    Gzip = 1,
    Zstd = 2,
}

impl CompressionAlgo {
    pub fn from_u8(v: u8) -> Option<Self> {
        match v {
            0 => Some(CompressionAlgo::None),
            1 => Some(CompressionAlgo::Gzip),
            2 => Some(CompressionAlgo::Zstd),
            _ => None,
        }
    }
}

/// File entry in pack
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackFile {
    /// Relative path within pack
    pub path: String,
    /// File size in bytes
    pub size: u64,
    /// SHA256 hash of file
    pub hash: String,
    /// Compression algorithm used
    pub compression: CompressionAlgo,
    /// File permissions (Unix style)
    pub mode: u32,
}

/// Compatibility constraints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Compatibility {
    /// Minimum Bit-TTT version required
    pub min_version: String,
    /// Maximum Bit-TTT version allowed
    pub max_version: Option<String>,
    /// Target architecture
    pub arch: String,
    /// Operating system
    pub os: Option<String>,
}

/// Pack metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackMetadata {
    /// Unique pack identifier
    pub pack_id: String,
    /// Semantic version
    pub version: String,
    /// Display name
    pub name: String,
    /// Author name
    pub author: String,
    /// Description
    pub description: String,
    /// Pack type: soul, weights, dataset, etc.
    pub pack_type: String,
    /// Creation timestamp
    pub created_at: String,
    /// Last update timestamp
    pub updated_at: String,
    /// Compatibility info
    pub compatibility: Compatibility,
    /// Files included in pack
    pub files: Vec<PackFile>,
    /// Total size of pack in bytes
    pub total_size: u64,
    /// SHA256 hash of all data
    pub total_hash: String,
    /// Download URL (optional)
    pub download_url: Option<String>,
    /// License identifier
    pub license: String,
    /// Keywords/tags
    pub tags: Vec<String>,
    /// Custom metadata
    pub metadata: HashMap<String, serde_json::Value>,
}

impl Default for PackMetadata {
    fn default() -> Self {
        Self {
            pack_id: String::new(),
            version: "1.0.0".to_string(),
            name: String::new(),
            author: String::new(),
            description: String::new(),
            pack_type: "unknown".to_string(),
            created_at: Utc::now().to_rfc3339(),
            updated_at: Utc::now().to_rfc3339(),
            compatibility: Compatibility {
                min_version: "0.3.0".to_string(),
                max_version: None,
                arch: std::env::consts::ARCH.to_string(),
                os: Some(std::env::consts::OS.to_string()),
            },
            files: Vec::new(),
            total_size: 0,
            total_hash: String::new(),
            download_url: None,
            license: "MIT".to_string(),
            tags: Vec::new(),
            metadata: HashMap::new(),
        }
    }
}

/// Installation information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackInfo {
    /// Pack metadata
    pub metadata: PackMetadata,
    /// Installation path
    pub install_path: Option<String>,
    /// Installation timestamp
    pub installed_at: Option<String>,
    /// Verification status
    pub verified: bool,
    /// Size on disk
    pub disk_size: u64,
}

impl From<PackMetadata> for PackInfo {
    fn from(metadata: PackMetadata) -> Self {
        Self {
            metadata,
            install_path: None,
            installed_at: None,
            verified: false,
            disk_size: 0,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pack_header_default() {
        let header = PackHeader::default();
        assert_eq!(header.magic, *b"U32K");
        assert_eq!(header.version, 1);
    }

    #[test]
    fn test_compression_algo() {
        assert_eq!(CompressionAlgo::from_u8(0), Some(CompressionAlgo::None));
        assert_eq!(CompressionAlgo::from_u8(1), Some(CompressionAlgo::Gzip));
        assert_eq!(CompressionAlgo::from_u8(2), Some(CompressionAlgo::Zstd));
        assert_eq!(CompressionAlgo::from_u8(99), None);
    }

    #[test]
    fn test_pack_metadata_default() {
        let meta = PackMetadata::default();
        assert_eq!(meta.version, "1.0.0");
        assert_eq!(meta.license, "MIT");
    }
}
