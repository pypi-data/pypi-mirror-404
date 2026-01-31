use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

// Early return for WASM targets - no CUDA/PTX needed
#[cfg(target_arch = "wasm32")]
fn main() {
    println!("cargo:rerun-if-changed=build.rs");
}

fn process_ptx(
    nvcc: &Path,
    is_cuda_available: bool,
    out_dir: &Path,
    cuda_file: &str,
    ptx_filename: &str,
) -> anyhow::Result<()> {
    let output_ptx_path = out_dir.join(ptx_filename);
    let saved_ptx_path = PathBuf::from("src/kernels").join(ptx_filename);

    if is_cuda_available && std::path::Path::new(cuda_file).exists() {
        let output = Command::new(nvcc)
            .arg("-ptx")
            .arg("-arch=compute_80")
            .arg("-code=sm_80")
            .arg(cuda_file)
            .arg("-o")
            .arg(&output_ptx_path)
            .output();

        match output {
            Ok(out) if out.status.success() => {
                let _ = fs::copy(&output_ptx_path, &saved_ptx_path);
                println!("cargo:warning=Updated bundled PTX at {:?}", saved_ptx_path);
            }
            Ok(out) => {
                let err = String::from_utf8_lossy(&out.stderr);
                println!(
                    "cargo:warning=CUDA compilation failed for {}: {}",
                    cuda_file, err
                );
            }
            Err(e) => {
                println!(
                    "cargo:warning=Failed to execute NVCC for {}: {}",
                    cuda_file, e
                );
            }
        }
    }

    // Fallback: use bundled PTX
    if !output_ptx_path.exists()
        || output_ptx_path
            .metadata()
            .map(|m| m.len() == 0)
            .unwrap_or(true)
    {
        if saved_ptx_path.exists() {
            println!("cargo:warning=Using bundled PTX from {:?}", saved_ptx_path);
            fs::copy(&saved_ptx_path, &output_ptx_path)?;
        } else {
            println!("cargo:warning=CRITICAL: No PTX found for {}.", ptx_filename);
            fs::write(&output_ptx_path, "")?;
        }
    }

    Ok(())
}

#[cfg(not(target_arch = "wasm32"))]
fn main() -> anyhow::Result<()> {
    println!("cargo:rerun-if-changed=src/kernels/bit_op.cu");
    println!("cargo:rerun-if-changed=src/kernels/adaptive_bit_op.cu");
    println!("cargo:rerun-if-changed=src/kernels/matmul_4bit.cu");
    println!("cargo:rerun-if-changed=src/kernels/fused_ops.cu");
    println!("cargo:rerun-if-changed=src/kernels/paged_attention.cu");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=src/kernels/bit_op.ptx");
    println!("cargo:rerun-if-changed=src/kernels/adaptive_bit_op.ptx");
    println!("cargo:rerun-if-changed=src/kernels/matmul_4bit.ptx");
    println!("cargo:rerun-if-changed=src/kernels/fused_ops.ptx");
    println!("cargo:rerun-if-changed=src/kernels/paged_attention.ptx");

    let out_dir = PathBuf::from(env::var("OUT_DIR")?);

    // Attempt to find NVCC
    let nvcc = match env::var("CUDA_HOME") {
        Ok(home) => PathBuf::from(home).join("bin/nvcc"),
        Err(_) => PathBuf::from("nvcc"),
    };

    // Check if nvcc works
    let is_cuda_available = Command::new(&nvcc).arg("--version").output().is_ok();

    if !is_cuda_available {
        println!("cargo:warning=NVCC not found. Using bundled PTX files.");
    }

    // Process all PTX files
    process_ptx(
        &nvcc,
        is_cuda_available,
        &out_dir,
        "src/kernels/bit_op.cu",
        "bit_op.ptx",
    )?;
    process_ptx(
        &nvcc,
        is_cuda_available,
        &out_dir,
        "src/kernels/adaptive_bit_op.cu",
        "adaptive_bit_op.ptx",
    )?;
    process_ptx(
        &nvcc,
        is_cuda_available,
        &out_dir,
        "src/kernels/matmul_4bit.cu",
        "matmul_4bit.ptx",
    )?;
    process_ptx(
        &nvcc,
        is_cuda_available,
        &out_dir,
        "src/kernels/fused_ops.cu",
        "fused_ops.ptx",
    )?;
    process_ptx(
        &nvcc,
        is_cuda_available,
        &out_dir,
        "src/kernels/paged_attention.cu",
        "paged_attention.ptx",
    )?;

    Ok(())
}
