use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

use rshogi_core::board;
use rshogi_core::board::mate::{
    debug_solve_mate_in_three, debug_solve_mate_in_three_table, solve_mate_in_three,
    solve_mate_in_three_table,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    #[cfg(not(feature = "mate1ply-full"))]
    eprintln!(
        "verify_mate3ply: mate1ply-full is disabled; pass --features mate1ply-full to enable."
    );

    let mut path = PathBuf::from("_refs/mate3.sfen");
    let mut limit: usize = 0;
    let mut target_idx: Option<usize> = None;
    let mut trace_mate3 = false;
    let mut use_table = false;
    let mut expect_none = false;

    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--limit" => {
                let value = args.next().ok_or("missing value for --limit")?;
                limit = value.parse::<usize>()?;
            }
            "--target-idx" => {
                let value = args.next().ok_or("missing value for --target-idx")?;
                target_idx = Some(value.parse::<usize>()?);
            }
            "--trace-mate3" => {
                trace_mate3 = true;
            }
            "--table" => {
                use_table = true;
            }
            "--expect-none" => {
                expect_none = true;
            }
            "--help" | "-h" => {
                eprintln!(
                    "Usage: verify_mate3ply [SFEN_FILE] [--limit N] [--target-idx N] [--trace-mate3] [--table] [--expect-none]\n\
Default SFEN_FILE is _refs/mate3.sfen"
                );
                return Ok(());
            }
            _ => {
                path = PathBuf::from(arg);
            }
        }
    }

    let file = File::open(&path)?;
    let reader = BufReader::new(file);

    let mut total = 0usize;
    let mut failures = 0usize;
    for line in reader.lines() {
        let line = line?;
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 4 {
            continue;
        }
        let sfen = format!("{} {} {} {}", parts[0], parts[1], parts[2], parts[3]);

        let idx = total;
        total += 1;
        let pos = board::position_from_sfen(&sfen)?;
        let solved = if use_table {
            solve_mate_in_three_table(&pos).is_some()
        } else {
            solve_mate_in_three(&pos).is_some()
        };

        let failed = if expect_none { solved } else { !solved };
        if failed {
            failures += 1;
            let label = if expect_none { "unexpected_mate" } else { "unsolved" };
            eprintln!("fail idx={idx} reason={label} sfen={sfen}");
            if trace_mate3 {
                if use_table {
                    eprintln!("{}", debug_solve_mate_in_three_table(&pos));
                } else {
                    eprintln!("{}", debug_solve_mate_in_three(&pos));
                }
            }
        }

        if let Some(target) = target_idx {
            if idx == target {
                break;
            }
        }

        if limit > 0 && total >= limit {
            break;
        }

        if total % 10000 == 0 {
            eprintln!("progress {total}");
        }
    }

    if failures > 0 {
        eprintln!("mate3ply failed: {failures}/{total}");
        return Err("mate3ply verification failed".into());
    }

    println!("mate3ply ok: {total}");
    Ok(())
}
