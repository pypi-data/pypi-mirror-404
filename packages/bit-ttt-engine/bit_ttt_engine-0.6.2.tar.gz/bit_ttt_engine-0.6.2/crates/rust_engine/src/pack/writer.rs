//! Knowledge Pack Writer
//! 
//! Creates and writes .u32k pack files with metadata and compression

use crate::pack::types::*;
use anyhow::{anyhow, Result};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::Write;
use std::path::Path;

pub struct PackWriter;

impl PackWriter {
    /// Create a new pack file
    pub fn create<P: AsRef<Path>>(
        pack_path: P,
        metadata: &PackMetadata,
        data: &[u8],
        compression: CompressionAlgo,
    ) -> Result<()> {
        let mut file = File::create(pack_path)?;
        
        // Serialize metadata to JSON
        let metadata_json = serde_json::to_string(metadata)?;
        let metadata_bytes = metadata_json.as_bytes();
        
        // Compress data if requested
        let (compressed_data, actual_compression) = match compression {
            CompressionAlgo::None => (data.to_vec(), CompressionAlgo::None),
            CompressionAlgo::Gzip => {
                let mut encoder = flate2::write::GzEncoder::new(Vec::new(), flate2::Compression::default());
                encoder.write_all(data)?;
                let compressed = encoder.finish()?;
                (compressed, CompressionAlgo::Gzip)
            }
            CompressionAlgo::Zstd => {
                let compressed = zstd::encode_all(data, 3)?;
                (compressed, CompressionAlgo::Zstd)
            }
        };
        
        // Compress metadata if applicable
        let compressed_metadata = match compression {
            CompressionAlgo::None => metadata_bytes.to_vec(),
            CompressionAlgo::Gzip => {
                let mut encoder = flate2::write::GzEncoder::new(Vec::new(), flate2::Compression::default());
                encoder.write_all(metadata_bytes)?;
                encoder.finish()?
            }
            CompressionAlgo::Zstd => {
                zstd::encode_all(metadata_bytes, 3)?
            }
        };
        
        // Calculate checksums
        let data_checksum = Self::calculate_checksum(&compressed_data);
        let metadata_checksum = Self::calculate_checksum(&compressed_metadata);
        
        // Create header
        let mut header = PackHeader::default();
        header.version = 1;
        header.flags = match actual_compression {
            CompressionAlgo::None => 0x00,
            CompressionAlgo::Gzip => 0x01,
            CompressionAlgo::Zstd => 0x02,
        };
        header.metadata_size = compressed_metadata.len() as u32;
        header.data_size = compressed_data.len() as u32;
        
        // Calculate full checksum (metadata + data)
        let mut combined = Vec::new();
        combined.extend_from_slice(&compressed_metadata);
        combined.extend_from_slice(&compressed_data);
        let full_checksum = Self::calculate_checksum(&combined);
        header.checksum.copy_from_slice(&full_checksum);
        
        // Write header (64 bytes)
        file.write_all(&header.magic)?;
        file.write_all(&[header.version])?;
        file.write_all(&[header.flags])?;
        file.write_all(&header.reserved)?;
        file.write_all(&header.metadata_size.to_le_bytes())?;
        file.write_all(&header.data_size.to_le_bytes())?;
        file.write_all(&header.checksum)?;
        
        // Write metadata
        file.write_all(&compressed_metadata)?;
        
        // Write data
        file.write_all(&compressed_data)?;
        
        Ok(())
    }
    
    /// Create pack from directory
    pub fn create_from_directory<P: AsRef<Path>, Q: AsRef<Path>>(
        pack_path: P,
        source_dir: Q,
        metadata: &PackMetadata,
        compression: CompressionAlgo,
    ) -> Result<()> {
        // Create tar archive of directory
        let tar_data = Self::directory_to_tar(&source_dir)?;
        
        // Create pack with tar data
        Self::create(pack_path, metadata, &tar_data, compression)?;
        
        Ok(())
    }
    
    /// Convert directory to tar format
    fn directory_to_tar<P: AsRef<Path>>(source_dir: P) -> Result<Vec<u8>> {
        let source_path = source_dir.as_ref();
        let mut tar_data = Vec::new();
        
        // Create tar encoder
        let mut tar = tar::Builder::new(&mut tar_data);
        
        // Add all files from directory
        tar.append_dir_all(".", source_path)?;
        tar.finish()?;
        
        Ok(tar_data)
    }
    
    /// Calculate SHA256 checksum
    fn calculate_checksum(data: &[u8]) -> Vec<u8> {
        let mut hasher = Sha256::new();
        hasher.update(data);
        hasher.finalize().to_vec()
    }
    
    /// Update pack metadata (creates new version)
    pub fn update_metadata<P: AsRef<Path>>(
        pack_path: P,
        new_metadata: &PackMetadata,
    ) -> Result<()> {
        // This would re-create the entire pack with new metadata
        // For now, this is a placeholder
        Err(anyhow!("Pack update not yet implemented"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_checksum_calculation() {
        let data = b"test data";
        let checksum = PackWriter::calculate_checksum(data);
        assert_eq!(checksum.len(), 32); // SHA256 produces 32 bytes
    }
    
    #[test]
    fn test_header_creation() {
        let mut header = PackHeader::default();
        header.data_size = 1024;
        header.metadata_size = 512;
        
        assert_eq!(header.magic, *b"U32K");
        assert_eq!(header.version, 1);
        assert_eq!(header.data_size, 1024);
    }
}
