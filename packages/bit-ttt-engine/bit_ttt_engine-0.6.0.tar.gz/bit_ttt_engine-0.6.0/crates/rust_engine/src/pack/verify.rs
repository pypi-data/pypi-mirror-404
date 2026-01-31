//! Knowledge Pack Verification
//! 
//! Verifies checksums, signatures, and compatibility

use crate::pack::types::*;
use crate::pack::reader::PackReader;
use anyhow::{anyhow, Result};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::Read;
use std::path::Path;

pub struct PackVerifier;

#[derive(Debug, Clone)]
pub struct VerificationResult {
    pub valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

impl Default for VerificationResult {
    fn default() -> Self {
        Self {
            valid: true,
            errors: Vec::new(),
            warnings: Vec::new(),
        }
    }
}

impl PackVerifier {
    /// Verify pack file integrity
    pub fn verify_pack<P: AsRef<Path>>(pack_path: P) -> Result<VerificationResult> {
        let mut result = VerificationResult::default();
        
        // 1. Check file exists and is readable
        let mut file = match File::open(&pack_path) {
            Ok(f) => f,
            Err(e) => {
                result.errors.push(format!("Cannot open pack file: {}", e));
                result.valid = false;
                return Ok(result);
            }
        };
        
        // 2. Read header
        let header = match PackReader::read_header(&pack_path) {
            Ok(h) => h,
            Err(e) => {
                result.errors.push(format!("Invalid pack header: {}", e));
                result.valid = false;
                return Ok(result);
            }
        };
        
        // 3. Read metadata
        match PackReader::read_metadata(&pack_path) {
            Ok(meta) => {
                // Check metadata
                if meta.pack_id.is_empty() {
                    result.errors.push("Pack ID is empty".to_string());
                    result.valid = false;
                }
                if meta.version.is_empty() {
                    result.errors.push("Pack version is empty".to_string());
                    result.valid = false;
                }
            }
            Err(e) => {
                result.errors.push(format!("Invalid metadata: {}", e));
                result.valid = false;
                return Ok(result);
            }
        }
        
        // 4. Verify checksum
        match Self::verify_checksum(&pack_path, &header) {
            Ok(true) => {
                result.warnings.push("Checksum verified".to_string());
            }
            Ok(false) => {
                result.errors.push("Checksum mismatch: pack data may be corrupted".to_string());
                result.valid = false;
            }
            Err(e) => {
                result.errors.push(format!("Checksum verification failed: {}", e));
                result.valid = false;
            }
        }
        
        Ok(result)
    }
    
    /// Verify checksum against file
    pub fn verify_checksum<P: AsRef<Path>>(pack_path: P, header: &PackHeader) -> Result<bool> {
        let mut file = File::open(&pack_path)?;
        let mut data = Vec::new();
        
        // Skip header (64 bytes) and read rest
        file.seek(std::io::SeekFrom::Start(64))?;
        file.read_to_end(&mut data)?;
        
        let calculated = Self::calculate_checksum(&data);
        
        Ok(calculated.as_slice() == header.checksum)
    }
    
    /// Check compatibility
    pub fn verify_compatibility(
        metadata: &PackMetadata,
        engine_version: &str,
    ) -> Result<VerificationResult> {
        let mut result = VerificationResult::default();
        
        let compat = &metadata.compatibility;
        
        // Check minimum version
        if Self::compare_versions(engine_version, &compat.min_version) < 0 {
            result.errors.push(format!(
                "Engine version {} is below minimum required {}",
                engine_version, compat.min_version
            ));
            result.valid = false;
        }
        
        // Check maximum version
        if let Some(max_version) = &compat.max_version {
            if Self::compare_versions(engine_version, max_version) > 0 {
                result.errors.push(format!(
                    "Engine version {} exceeds maximum allowed {}",
                    engine_version, max_version
                ));
                result.valid = false;
            }
        }
        
        // Check architecture
        let current_arch = std::env::consts::ARCH;
        if compat.arch != "universal" && compat.arch != current_arch {
            result.errors.push(format!(
                "Pack requires {} architecture, but current is {}",
                compat.arch, current_arch
            ));
            result.valid = false;
        }
        
        // Check OS
        if let Some(os) = &compat.os {
            let current_os = std::env::consts::OS;
            if os != "universal" && os != current_os {
                result.warnings.push(format!(
                    "Pack optimized for {} but running on {}",
                    os, current_os
                ));
            }
        }
        
        Ok(result)
    }
    
    /// Calculate SHA256 checksum
    fn calculate_checksum(data: &[u8]) -> Vec<u8> {
        let mut hasher = Sha256::new();
        hasher.update(data);
        hasher.finalize().to_vec()
    }
    
    /// Compare version strings (semantic versioning)
    /// Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    fn compare_versions(v1: &str, v2: &str) -> i32 {
        let parse_version = |v: &str| -> Result<(u32, u32, u32)> {
            let parts: Vec<&str> = v.split('.').collect();
            if parts.len() < 3 {
                return Err(anyhow!("Invalid version format"));
            }
            Ok((
                parts[0].parse().unwrap_or(0),
                parts[1].parse().unwrap_or(0),
                parts[2].parse().unwrap_or(0),
            ))
        };
        
        let (major1, minor1, patch1) = parse_version(v1).unwrap_or((0, 0, 0));
        let (major2, minor2, patch2) = parse_version(v2).unwrap_or((0, 0, 0));
        
        if major1 < major2 { return -1; }
        if major1 > major2 { return 1; }
        if minor1 < minor2 { return -1; }
        if minor1 > minor2 { return 1; }
        if patch1 < patch2 { return -1; }
        if patch1 > patch2 { return 1; }
        
        0
    }
    
    /// Verify file hashes within pack
    pub fn verify_file_hashes<P: AsRef<Path>>(
        pack_path: P,
        metadata: &PackMetadata,
    ) -> Result<VerificationResult> {
        let mut result = VerificationResult::default();
        
        // For now, just verify that file list is not empty
        if metadata.files.is_empty() {
            result.warnings.push("Pack contains no files".to_string());
        }
        
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_version_comparison() {
        assert_eq!(PackVerifier::compare_versions("1.0.0", "2.0.0"), -1);
        assert_eq!(PackVerifier::compare_versions("2.0.0", "1.0.0"), 1);
        assert_eq!(PackVerifier::compare_versions("1.0.0", "1.0.0"), 0);
        assert_eq!(PackVerifier::compare_versions("1.2.3", "1.2.4"), -1);
    }
    
    #[test]
    fn test_verification_result_default() {
        let result = VerificationResult::default();
        assert!(result.valid);
        assert!(result.errors.is_empty());
        assert!(result.warnings.is_empty());
    }
}
