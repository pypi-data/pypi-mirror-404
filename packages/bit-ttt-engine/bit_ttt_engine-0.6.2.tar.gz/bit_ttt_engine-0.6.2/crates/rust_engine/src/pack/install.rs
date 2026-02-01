//! Knowledge Pack Installation
//! 
//! Handles installation of packs to the filesystem

use crate::pack::types::*;
use crate::pack::reader::PackReader;
use crate::pack::verify::{PackVerifier, VerificationResult};
use anyhow::{anyhow, Result};
use std::fs;
use std::path::{Path, PathBuf};
use chrono::Utc;

pub struct PackInstaller;

#[derive(Debug, Clone)]
pub struct InstallationResult {
    pub success: bool,
    pub pack_info: Option<PackInfo>,
    pub install_path: Option<PathBuf>,
    pub message: String,
    pub errors: Vec<String>,
}

impl PackInstaller {
    /// Install a pack from file
    pub fn install<P: AsRef<Path>>(
        pack_path: P,
        install_dir: Option<P>,
    ) -> Result<InstallationResult> {
        let pack_file = pack_path.as_ref();
        
        // 1. Verify pack integrity
        let verification = PackVerifier::verify_pack(pack_file)?;
        if !verification.valid {
            return Ok(InstallationResult {
                success: false,
                pack_info: None,
                install_path: None,
                message: "Pack verification failed".to_string(),
                errors: verification.errors,
            });
        }
        
        // 2. Read metadata
        let metadata = PackReader::read_metadata(pack_file)?;
        
        // 3. Determine install path
        let base_install_dir = install_dir
            .map(|p| p.as_ref().to_path_buf())
            .unwrap_or_else(|| {
                crate::pack::default_pack_dir()
                    .join("installed")
            });
        
        let target_dir = base_install_dir.join(&metadata.pack_id);
        
        // 4. Check if already installed
        if target_dir.exists() {
            return Ok(InstallationResult {
                success: false,
                pack_info: None,
                install_path: Some(target_dir),
                message: format!("Pack {} already installed", metadata.pack_id),
                errors: vec!["Please uninstall existing version first".to_string()],
            });
        }
        
        // 5. Create installation directory
        fs::create_dir_all(&target_dir)?;
        
        // 6. Extract pack
        match PackReader::extract_all(pack_file, &target_dir) {
            Ok(_) => {}
            Err(e) => {
                // Cleanup on failure
                let _ = fs::remove_dir_all(&target_dir);
                return Ok(InstallationResult {
                    success: false,
                    pack_info: None,
                    install_path: Some(target_dir),
                    message: "Failed to extract pack".to_string(),
                    errors: vec![e.to_string()],
                });
            }
        }
        
        // 7. Create metadata file
        let mut pack_info = PackInfo::from(metadata);
        pack_info.install_path = Some(target_dir.to_string_lossy().to_string());
        pack_info.installed_at = Some(Utc::now().to_rfc3339());
        pack_info.verified = verification.valid;
        
        // Calculate disk size
        pack_info.disk_size = Self::calculate_dir_size(&target_dir)?;
        
        // Write installation manifest
        let manifest_path = target_dir.join("pack.json");
        fs::write(
            manifest_path,
            serde_json::to_string_pretty(&pack_info)?,
        )?;
        
        // 8. Create global manifest entry
        Self::update_global_manifest(&pack_info)?;
        
        Ok(InstallationResult {
            success: true,
            pack_info: Some(pack_info),
            install_path: Some(target_dir),
            message: format!("Successfully installed {}", pack_info.metadata.pack_id),
            errors: Vec::new(),
        })
    }
    
    /// Uninstall a pack
    pub fn uninstall(pack_id: &str) -> Result<InstallationResult> {
        let install_dir = crate::pack::default_pack_dir().join("installed");
        let pack_dir = install_dir.join(pack_id);
        
        if !pack_dir.exists() {
            return Ok(InstallationResult {
                success: false,
                pack_info: None,
                install_path: None,
                message: format!("Pack {} not found", pack_id),
                errors: vec!["Pack not installed".to_string()],
            });
        }
        
        // Read pack info before deletion
        let pack_info_path = pack_dir.join("pack.json");
        let pack_info: Option<PackInfo> = if pack_info_path.exists() {
            let content = fs::read_to_string(&pack_info_path)?;
            serde_json::from_str(&content).ok()
        } else {
            None
        };
        
        // Remove directory
        fs::remove_dir_all(&pack_dir)?;
        
        // Update global manifest
        Self::remove_from_global_manifest(pack_id)?;
        
        Ok(InstallationResult {
            success: true,
            pack_info,
            install_path: None,
            message: format!("Successfully uninstalled {}", pack_id),
            errors: Vec::new(),
        })
    }
    
    /// List installed packs
    pub fn list_installed() -> Result<Vec<PackInfo>> {
        let install_dir = crate::pack::default_pack_dir().join("installed");
        
        if !install_dir.exists() {
            return Ok(Vec::new());
        }
        
        let mut packs = Vec::new();
        
        for entry in fs::read_dir(&install_dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                let manifest_path = path.join("pack.json");
                if manifest_path.exists() {
                    let content = fs::read_to_string(&manifest_path)?;
                    if let Ok(pack_info) = serde_json::from_str::<PackInfo>(&content) {
                        packs.push(pack_info);
                    }
                }
            }
        }
        
        Ok(packs)
    }
    
    /// Get specific installed pack info
    pub fn get_installed(pack_id: &str) -> Result<Option<PackInfo>> {
        let install_dir = crate::pack::default_pack_dir()
            .join("installed")
            .join(pack_id);
        
        if !install_dir.exists() {
            return Ok(None);
        }
        
        let manifest_path = install_dir.join("pack.json");
        if !manifest_path.exists() {
            return Ok(None);
        }
        
        let content = fs::read_to_string(&manifest_path)?;
        let pack_info = serde_json::from_str(&content)?;
        
        Ok(Some(pack_info))
    }
    
    /// Calculate total directory size
    fn calculate_dir_size(path: &Path) -> Result<u64> {
        let mut size = 0u64;
        
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let metadata = entry.metadata()?;
            
            if metadata.is_file() {
                size += metadata.len();
            } else if metadata.is_dir() {
                size += Self::calculate_dir_size(&entry.path())?;
            }
        }
        
        Ok(size)
    }
    
    /// Update global manifest
    fn update_global_manifest(pack_info: &PackInfo) -> Result<()> {
        let pack_dir = crate::pack::default_pack_dir();
        fs::create_dir_all(&pack_dir)?;
        
        let manifest_path = pack_dir.join("manifest.json");
        
        let mut manifest: PackManifest = if manifest_path.exists() {
            let content = fs::read_to_string(&manifest_path)?;
            serde_json::from_str(&content)?
        } else {
            PackManifest {
                version: "1.0.0".to_string(),
                packs: Vec::new(),
                updated_at: Utc::now().to_rfc3339(),
            }
        };
        
        // Add or update pack entry
        if let Some(pos) = manifest.packs.iter().position(|p| p.metadata.pack_id == pack_info.metadata.pack_id) {
            manifest.packs[pos] = pack_info.clone();
        } else {
            manifest.packs.push(pack_info.clone());
        }
        
        manifest.updated_at = Utc::now().to_rfc3339();
        
        fs::write(
            manifest_path,
            serde_json::to_string_pretty(&manifest)?,
        )?;
        
        Ok(())
    }
    
    /// Remove from global manifest
    fn remove_from_global_manifest(pack_id: &str) -> Result<()> {
        let pack_dir = crate::pack::default_pack_dir();
        let manifest_path = pack_dir.join("manifest.json");
        
        if !manifest_path.exists() {
            return Ok(());
        }
        
        let content = fs::read_to_string(&manifest_path)?;
        let mut manifest: PackManifest = serde_json::from_str(&content)?;
        
        manifest.packs.retain(|p| p.metadata.pack_id != pack_id);
        manifest.updated_at = Utc::now().to_rfc3339();
        
        fs::write(
            manifest_path,
            serde_json::to_string_pretty(&manifest)?,
        )?;
        
        Ok(())
    }
}

// Re-export from types
pub use crate::pack::types::PackManifest;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_calculate_dir_size() {
        let temp_dir = std::env::temp_dir().join("test_pack_size");
        if temp_dir.exists() {
            let _ = fs::remove_dir_all(&temp_dir);
        }
        
        fs::create_dir(&temp_dir).unwrap();
        fs::write(temp_dir.join("test.txt"), "test").unwrap();
        
        let size = PackInstaller::calculate_dir_size(&temp_dir).unwrap();
        assert!(size > 0);
        
        let _ = fs::remove_dir_all(&temp_dir);
    }
}
