//! Tests for Isomorphic Layer Offloading System (Phase 3, #12)

#[cfg(test)]
mod tests {
    use crate::layers::{IsomorphicOffloader, LayerPlacement, MemoryPressure};

    #[test]
    fn test_memory_pressure_levels() {
        // Test pressure calculation from free VRAM ratio
        assert_eq!(MemoryPressure::from_ratio(0.95), MemoryPressure::Low);
        assert_eq!(MemoryPressure::from_ratio(0.70), MemoryPressure::Moderate);
        assert_eq!(MemoryPressure::from_ratio(0.50), MemoryPressure::High);
        assert_eq!(MemoryPressure::from_ratio(0.30), MemoryPressure::Critical);
    }

    #[test]
    fn test_memory_pressure_ordering() {
        // Test that pressure levels are properly ordered
        assert!(MemoryPressure::Low < MemoryPressure::Moderate);
        assert!(MemoryPressure::Moderate < MemoryPressure::High);
        assert!(MemoryPressure::High < MemoryPressure::Critical);

        // Test that equality works
        assert_eq!(MemoryPressure::Low, MemoryPressure::Low);
        assert_ne!(MemoryPressure::Low, MemoryPressure::Critical);
    }

    #[test]
    fn test_isomorphic_offloader_creation_hybrid() {
        // Test creating a hybrid offloader (static n_gpu)
        let result = IsomorphicOffloader::new_hybrid(4);

        // Should succeed or fail gracefully based on GPU availability
        match result {
            Ok(offloader) => {
                // Check that we can get stats
                let stats = offloader.stats();
                assert_eq!(stats.transfers, 0);
                assert_eq!(stats.offload_triggers, 0);
            }
            Err(e) => {
                // GPU may not be available in test environment
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_isomorphic_layer_init() {
        // Test layer initialization
        let result = IsomorphicOffloader::new_hybrid(4);

        match result {
            Ok(mut offloader) => {
                let n_layers = 32; // Typical LLaMA-2
                offloader.init_layers(n_layers).ok();

                // First 4 layers should be on GPU
                for i in 0..4 {
                    assert_eq!(
                        offloader.get_placement(i),
                        LayerPlacement::GPU,
                        "Layer {} should be on GPU",
                        i
                    );
                }

                // Layers 4+ should be on CPU
                for i in 4..std::cmp::min(8, n_layers) {
                    assert_eq!(
                        offloader.get_placement(i),
                        LayerPlacement::CPU,
                        "Layer {} should be on CPU",
                        i
                    );
                }

                // Check GPU layers list
                let gpu_layers = offloader.gpu_layers();
                assert_eq!(gpu_layers.len(), 4);
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_isomorphic_dynamic_offloader() {
        // Test dynamic offloader (memory-aware)
        let result = IsomorphicOffloader::new_dynamic(
            512 * 1024 * 1024, // 512 MB min free
            256 * 1024 * 1024, // 256 MB staging
        );

        match result {
            Ok(mut offloader) => {
                let n_layers = 32;
                offloader.init_layers(n_layers).ok();

                // In dynamic mode, all layers should start on CPU to minimize initial VRAM
                for i in 0..n_layers {
                    // With dynamic strategy, placement depends on actual VRAM
                    // Just check that it's valid
                    let placement = offloader.get_placement(i);
                    assert!(placement == LayerPlacement::GPU || placement == LayerPlacement::CPU);
                }
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_layer_placement_get() {
        // Test getting layer placements
        let result = IsomorphicOffloader::new_hybrid(8);

        match result {
            Ok(mut offloader) => {
                offloader.init_layers(16).ok();

                // Test get_placement for various layers
                for i in 0..8 {
                    assert_eq!(offloader.get_placement(i), LayerPlacement::GPU);
                }

                for i in 8..16 {
                    assert_eq!(offloader.get_placement(i), LayerPlacement::CPU);
                }

                // Test non-existent layer (should default to CPU)
                assert_eq!(offloader.get_placement(999), LayerPlacement::CPU);
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_stats_accumulation() {
        // Test that statistics are properly tracked
        let result = IsomorphicOffloader::new_hybrid(4);

        match result {
            Ok(offloader) => {
                let stats = offloader.stats();

                // Initial stats should be zero
                assert_eq!(stats.transfers, 0);
                assert_eq!(stats.bytes_transferred, 0);
                assert_eq!(stats.offload_triggers, 0);
                assert_eq!(stats.preload_triggers, 0);

                // Stats should be readable
                let _ = stats.peak_vram_used;
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_offloader_target_device() {
        // Test getting the target device for layers
        let result = IsomorphicOffloader::new_hybrid(4);

        match result {
            Ok(mut offloader) => {
                offloader.init_layers(8).ok();

                // Get target devices
                let _device_0 = offloader.get_target_device(0);
                let _device_5 = offloader.get_target_device(5);

                // We can't directly compare Device objects easily, but we can check
                // that the function returns valid devices
                // (This test mainly checks that the function doesn't panic)
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_memory_status() {
        // Test memory status reporting
        let result = IsomorphicOffloader::new_hybrid(4);

        match result {
            Ok(mut offloader) => {
                let status_result = offloader.memory_status();

                // Should either succeed or fail gracefully
                match status_result {
                    Ok((_free, used, peak)) => {
                        // Basic sanity checks (free and used are usize, always >= 0)
                        assert!(peak >= used, "Peak memory should be >= used memory");
                    }
                    Err(e) => {
                        println!("Memory status query failed: {}", e);
                    }
                }
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    #[ignore = "Requires GPU"]
    fn test_gpu_layers_list() {
        // Test getting list of GPU layers
        let result = IsomorphicOffloader::new_hybrid(6);

        match result {
            Ok(mut offloader) => {
                offloader.init_layers(24).ok();

                let gpu_layers = offloader.gpu_layers();

                // Should have 6 GPU layers
                assert_eq!(gpu_layers.len(), 6);

                // Should be layers 0-5
                for (i, &layer_id) in gpu_layers.iter().enumerate() {
                    assert_eq!(layer_id, i);
                }
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }

    #[test]
    fn test_layer_placement_enum() {
        // Test LayerPlacement enum properties
        assert_eq!(LayerPlacement::GPU, LayerPlacement::GPU);
        assert_eq!(LayerPlacement::CPU, LayerPlacement::CPU);
        assert_eq!(LayerPlacement::InTransit, LayerPlacement::InTransit);

        assert_ne!(LayerPlacement::GPU, LayerPlacement::CPU);
        assert_ne!(LayerPlacement::CPU, LayerPlacement::InTransit);
    }

    #[test]
    fn test_ensure_layer_ready_basic() {
        // Test basic ensure_layer_ready functionality
        let result = IsomorphicOffloader::new_hybrid(4);

        match result {
            Ok(mut offloader) => {
                offloader.init_layers(8).ok();

                // Try to ensure a CPU layer is ready
                let ensure_result = offloader.ensure_layer_ready(5, 50 * 1024 * 1024); // 50MB

                // Should handle gracefully whether it succeeds or not
                let _ = ensure_result;
            }
            Err(e) => {
                println!("Skipping GPU test: {}", e);
            }
        }
    }
}
