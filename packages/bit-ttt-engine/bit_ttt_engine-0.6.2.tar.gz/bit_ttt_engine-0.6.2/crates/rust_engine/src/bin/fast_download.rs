//! Fast Parallel Downloader CLI
//!
//! Usage:
//!   fast_download <URL> [--output <path>] [--connections <n>]
//!   fast_download --hf <repo_id> [--file <filename>] [--output <dir>]
//!
//! Examples:
//!   fast_download https://example.com/file.zip -o ./file.zip
//!   fast_download --hf TinyLlama/TinyLlama-1.1B-Chat-v1.0 -o benchmark/tinyllama-fp16

use anyhow::Result;
use cortex_rust::download::{DownloadConfig, FastDownloader, HfDownloader};
use std::env;
use std::path::PathBuf;

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        print_help(&args[0]);
        std::process::exit(1);
    }

    let mut url: Option<String> = None;
    let mut output: Option<PathBuf> = None;
    let mut connections = 8;
    let mut hf_repo: Option<String> = None;
    let mut hf_files: Vec<String> = Vec::new();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--help" | "-h" => {
                print_help(&args[0]);
                return Ok(());
            }
            "--output" | "-o" => {
                i += 1;
                if i < args.len() {
                    output = Some(PathBuf::from(&args[i]));
                }
            }
            "--connections" | "-c" => {
                i += 1;
                if i < args.len() {
                    connections = args[i].parse().unwrap_or(8);
                }
            }
            "--hf" => {
                i += 1;
                if i < args.len() {
                    hf_repo = Some(args[i].clone());
                }
            }
            "--file" | "-f" => {
                i += 1;
                if i < args.len() {
                    hf_files.push(args[i].clone());
                }
            }
            arg if !arg.starts_with('-') && url.is_none() && hf_repo.is_none() => {
                url = Some(arg.to_string());
            }
            _ => {}
        }
        i += 1;
    }

    // HuggingFace download mode
    if let Some(repo) = hf_repo {
        let downloader = HfDownloader::new()?;
        let dest_dir = output.unwrap_or_else(|| PathBuf::from("."));

        // Default files if none specified
        let files = if hf_files.is_empty() {
            vec![
                "config.json".to_string(),
                "tokenizer.json".to_string(),
                "tokenizer.model".to_string(),
                "tokenizer_config.json".to_string(),
                "model.safetensors".to_string(),
            ]
        } else {
            hf_files
        };

        println!("🤗 HuggingFace Download Mode");
        println!("   Repo: {}", repo);
        println!("   Dest: {:?}", dest_dir);
        println!("   Files: {:?}", files);
        println!();

        let file_refs: Vec<&str> = files.iter().map(|s| s.as_str()).collect();

        for file in &file_refs {
            match downloader.download_file(&repo, file, &dest_dir, None) {
                Ok(_) => {}
                Err(e) => {
                    eprintln!("⚠️  Skipping {}: {}", file, e);
                }
            }
        }

        return Ok(());
    }

    // Direct URL download mode
    let url = url.ok_or_else(|| anyhow::anyhow!("No URL specified"))?;
    let output = output
        .unwrap_or_else(|| PathBuf::from(url.split('/').next_back().unwrap_or("downloaded_file")));

    println!("⚡ Fast Download");
    println!("   URL: {}", url);
    println!("   Output: {:?}", output);
    println!("   Connections: {}", connections);
    println!();

    let config = DownloadConfig {
        num_connections: connections,
        show_progress: true,
        resume: true,
        ..Default::default()
    };

    let downloader = FastDownloader::with_config(config)?;
    downloader.download(&url, &output)?;

    Ok(())
}

fn print_help(prog: &str) {
    println!("⚡ Fast Parallel Downloader");
    println!();
    println!("Usage:");
    println!("  {} <URL> [options]              Download from URL", prog);
    println!(
        "  {} --hf <repo_id> [options]     Download from HuggingFace",
        prog
    );
    println!();
    println!("Options:");
    println!("  -o, --output <path>      Output file/directory");
    println!("  -c, --connections <n>    Number of parallel connections (default: 8)");
    println!("  -f, --file <name>        HF file to download (can repeat)");
    println!("  -h, --help               Show this help");
    println!();
    println!("Examples:");
    println!(
        "  {} https://example.com/large.zip -o ./large.zip -c 16",
        prog
    );
    println!();
    println!("  {} --hf TinyLlama/TinyLlama-1.1B-Chat-v1.0 \\", prog);
    println!("       -o benchmark/tinyllama-fp16 \\");
    println!("       -f model.safetensors -f config.json");
    println!();
    println!("Features:");
    println!("  • Parallel chunk downloads (HTTP Range)");
    println!("  • Automatic resume from interruption");
    println!("  • Progress tracking with speed display");
}
