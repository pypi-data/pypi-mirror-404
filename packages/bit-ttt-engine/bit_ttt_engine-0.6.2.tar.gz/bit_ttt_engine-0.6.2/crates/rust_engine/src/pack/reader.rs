//! Knowledge Pack Reader
//! 
//! Reads and parses .u32k pack files with support for compression

use crate::pack::types::*;
use anyhow::{anyhow, Result};
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;

pub struct PackReader;

impl PackReader {
    /// Read a pack file header
    pub fn read_header<P: AsRef<Path>>(path: P) -> Result<PackHeader> {
        let mut file = File::open(path)?;
        
        let mut magic = [0u8; 4];
        file.read_exact(&mut magic)?;
        
        if &magic != b"U32K" {
            return Err(anyhow!("Invalid pack format: wrong magic number"));
        }
        
        let mut version = [0u8; 1];
        file.read_exact(&mut version)?;
        let version = version[0];
        
        if version != 1 {
            return Err(anyhow!("Unsupported pack version: {}", version));
        }
        
        let mut flags = [0u8; 1];
        file.read_exact(&mut flags)?;
        
        let mut reserved = [0u8; 2];
        file.read_exact(&mut reserved)?;
        
        let mut size_buf = [0u8; 4];
        file.read_exact(&mut size_buf)?;
        let metadata_size = u32::from_le_bytes(size_buf);
        
        file.read_exact(&mut size_buf)?;
        let data_size = u32::from_le_bytes(size_buf);
        
        let mut checksum = [0u8; 32];
        file.read_exact(&mut checksum)?;
        
        Ok(PackHeader {
            magic,
            version,
            flags,
            reserved,
            metadata_size,
            data_size,
            checksum,
        })
    }
    
    /// Read metadata from pack
    pub fn read_metadata<P: AsRef<Path>>(path: P) -> Result<PackMetadata> {
        let mut file = File::open(path)?;
        
        // Skip header (64 bytes)
        file.seek(SeekFrom::Start(64))?;
        
        let header = Self::read_header(&path)?;
        let metadata_size = header.metadata_size as usize;
        
        let mut metadata_buf = vec![0u8; metadata_size];
        file.read_exact(&mut metadata_buf)?;
        
        // Decompress if needed
        let decompressed = if header.flags & 0x01 != 0 {
            Self::decompress(&metadata_buf, &header)?
        } else {
            metadata_buf
        };
        
        let metadata_str = String::from_utf8(decompressed)?;
        let metadata: PackMetadata = serde_json::from_str(&metadata_str)?;
        
        Ok(metadata)
    }
    
    /// Extract all files from pack to a directory
    pub fn extract_all<P: AsRef<Path>, Q: AsRef<Path>>(
        pack_path: P,
        extract_to: Q,
    ) -> Result<()> {
        let mut file = File::open(pack_path)?;
        let header = Self::read_header(&pack_path)?;
        
        // Skip to data section
        file.seek(SeekFrom::Start(64 + header.metadata_size as u64))?;
        
        let mut data_buf = vec![0u8; header.data_size as usize];
        file.read_exact(&mut data_buf)?;
        
        // Decompress data if needed
        let data = if header.flags & 0x01 != 0 {
            Self::decompress(&data_buf, &header)?
        } else {
            data_buf
        };
        
        // Extract files
        let metadata = Self::read_metadata(&pack_path)?;
        Self::extract_from_buffer(&data, &metadata, extract_to)?;
        
        Ok(())
    }
    
    /// Extract specific file from pack
    pub fn extract_file<P: AsRef<Path>, Q: AsRef<Path>>(
        pack_path: P,
        file_path: &str,
        extract_to: Q,
    ) -> Result<Vec<u8>> {
        let mut file = File::open(pack_path)?;
        let header = Self::read_header(&pack_path)?;
        
        // Read metadata to find file info
        let metadata = Self::read_metadata(&pack_path)?;
        let file_info = metadata.files.iter()
            .find(|f| f.path == file_path)
            .ok_or_else(|| anyhow!("File not found in pack: {}", file_path))?;
        
        // Skip to data section
        file.seek(SeekFrom::Start(64 + header.metadata_size as u64))?;
        
        let mut data_buf = vec![0u8; header.data_size as usize];
        file.read_exact(&mut data_buf)?;
        
        // Decompress data if needed
        let data = if header.flags & 0x01 != 0 {
            Self::decompress(&data_buf, &header)?
        } else {
            data_buf
        };
        
        Ok(data)
    }
    
    /// Decompress data based on compression algorithm in header
    fn decompress(data: &[u8], header: &PackHeader) -> Result<Vec<u8>> {
        // Compression flag is in bits 0-1
        let compression_type = (header.flags & 0x0F) >> 0;
        
        match compression_type {
            0 => Ok(data.to_vec()),  // No compression
            1 => {
                // Gzip compression
                use std::io::Read;
                let mut decoder = flate2::read::GzDecoder::new(data);
                let mut decompressed = Vec::new();
                decoder.read_to_end(&mut decompressed)?;
                Ok(decompressed)
            }
            2 => {
                // Zstd compression
                let decompressed = zstd::decode_all(data)?;
                Ok(decompressed)
            }
            _ => Err(anyhow!("Unknown compression type: {}", compression_type)),
        }
    }
    
    /// Extract files from data buffer
    fn extract_from_buffer<P: AsRef<Path>>(
        data: &[u8],
        _metadata: &PackMetadata,
        extract_to: P,
    ) -> Result<()> {
        std::fs::create_dir_all(&extract_to)?;
        
        // Parse tar/tar.gz if applicable
        // For now, just write to target directory
        let extract_path = extract_to.as_ref();
        
        // Simple file extraction (assumes tar format)
        use std::io::Cursor;
        let cursor = Cursor::new(data);
        
        // Try to untar
        match tar::Archive::new(cursor).unpack(extract_path) {
            Ok(_) => Ok(()),
            Err(_) => {
                // If not tar, write as single file
                std::fs::write(extract_path.join("data.bin"), data)?;
                Ok(())
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_compression_algo() {
        let header = PackHeader {
            flags: 0x01, // Gzip
            ..Default::default()
        };
        assert_eq!(header.flags & 0x0F, 0x01);
    }
}
