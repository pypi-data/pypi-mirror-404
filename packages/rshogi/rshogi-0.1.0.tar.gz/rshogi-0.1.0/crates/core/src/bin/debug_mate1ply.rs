use std::env;

use rshogi_core::board;
use rshogi_core::board::movegen::{generate_moves, Evasions};
use rshogi_core::mate;
use rshogi_core::types::{Move, Move16, Piece, PieceType, Square};

fn move_from_usi(pos: &board::Position, s: &str) -> Result<Move, String> {
    let m16 = Move16::from_usi(s).ok_or_else(|| format!("invalid usi: {s}"))?;
    if !m16.is_ok() {
        return Err(format!("invalid usi: {s}"));
    }

    if m16.is_drop() {
        let pt = m16.dropped_piece().ok_or_else(|| format!("invalid drop usi: {s}"))?;
        return Ok(Move::make_drop(pt, m16.to_sq(), pos.side_to_move()));
    }

    let from = m16.from_sq();
    let to = m16.to_sq();
    let piece = pos.piece_on(from);
    if piece == Piece::NO_PIECE {
        return Err(format!("no piece on {from} for {s}"));
    }
    if m16.is_promote() {
        Ok(Move::make_promote(from, to, piece))
    } else {
        Ok(Move::make(from, to, piece))
    }
}

fn bitboard_squares(mut bb: rshogi_core::types::Bitboard) -> Vec<Square> {
    let mut out = Vec::new();
    while let Some(sq) = bb.pop_lsb() {
        out.push(sq);
    }
    out
}

fn analyze_evasions(pos: &board::Position, mv: Move) {
    let mut next = pos.clone();
    next.init_stack();

    println!("analyze move: {} legal={}", mv.to_usi(), pos.is_legal(mv));
    if !pos.is_legal(mv) {
        return;
    }

    next.do_move(mv);
    let checkers = next.checkers();
    let checker_sqs = bitboard_squares(checkers);
    let king_sq = next.king_square(next.side_to_move());

    print!("checkers:");
    for sq in &checker_sqs {
        print!(" {sq}");
    }
    println!();

    let mut evasions = rshogi_core::board::MoveList::new();
    generate_moves::<Evasions>(&next, &mut evasions);
    println!("generated evasions: {}", evasions.len());
    for ev in evasions.iter().copied() {
        println!("  - {} legal={}", ev.to_usi(), next.is_legal(ev));
    }
    let legal: Vec<Move> = evasions.iter().copied().filter(|mv| next.is_legal(*mv)).collect();

    println!("legal evasions: {}", legal.len());
    for ev in legal {
        let mut tags = Vec::new();
        if ev.from_sq() == king_sq {
            tags.push("king");
        }
        if checker_sqs.len() == 1 && ev.to_sq() == checker_sqs[0] {
            tags.push("capture_checker");
            if ev.from_sq() == king_sq {
                tags.push("king_capture");
            }
        }
        if ev.is_drop() {
            let pt = ev.dropped_piece().unwrap_or(PieceType::NO_PIECE_TYPE);
            tags.push(match pt {
                PieceType::PAWN => "drop_pawn",
                PieceType::LANCE => "drop_lance",
                PieceType::KNIGHT => "drop_knight",
                PieceType::SILVER => "drop_silver",
                PieceType::GOLD => "drop_gold",
                PieceType::BISHOP => "drop_bishop",
                PieceType::ROOK => "drop_rook",
                _ => "drop",
            });
        }
        if tags.is_empty() {
            println!("  - {}", ev.to_usi());
        } else {
            println!("  - {} [{}]", ev.to_usi(), tags.join(","));
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args().skip(1);
    let mut sfen: Option<String> = None;
    let mut sfen_tokens: Vec<String> = Vec::new();
    let mut move_usi: Option<String> = None;
    let mut sequence: Vec<String> = Vec::new();

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--sfen" => {
                let value = args.next().ok_or("missing value for --sfen")?;
                sfen = Some(value);
            }
            "--move" => {
                let value = args.next().ok_or("missing value for --move")?;
                move_usi = Some(value);
            }
            "--sequence" => {
                let value = args.next().ok_or("missing value for --sequence")?;
                sequence.extend(
                    value
                        .split(',')
                        .map(str::trim)
                        .filter(|part| !part.is_empty())
                        .map(String::from),
                );
            }
            "--seq" => {
                let value = args.next().ok_or("missing value for --seq")?;
                sequence.push(value);
            }
            _ => {
                sfen_tokens.push(arg);
            }
        }
    }

    if sfen.is_none() {
        if sfen_tokens.len() >= 4 {
            sfen = Some(format!(
                "{} {} {} {}",
                sfen_tokens[0], sfen_tokens[1], sfen_tokens[2], sfen_tokens[3]
            ));
        } else if sfen_tokens.len() == 1 {
            sfen = Some(sfen_tokens[0].clone());
        }
    }

    let sfen = sfen.ok_or("missing sfen")?;
    let mut pos = board::position_from_sfen(&sfen)?;
    pos.init_stack();

    println!("sfen: {sfen}");
    if !sequence.is_empty() {
        print!("apply sequence:");
        for mv in &sequence {
            print!(" {mv}");
        }
        println!();
    }

    for mv_usi in &sequence {
        let mv = move_from_usi(&pos, mv_usi)?;
        println!("sequence move: {} legal={}", mv.to_usi(), pos.is_legal(mv));
        if !pos.is_legal(mv) {
            return Err(format!("illegal sequence move: {}", mv.to_usi()).into());
        }
        pos.do_move(mv);
    }
    if !sequence.is_empty() {
        println!("sfen (after sequence): {}", pos.sfen(None));
    }

    let table = mate::solve_mate_in_one_table(&pos);
    let yane = mate::yaneuraou::mate_1ply(&pos);
    let combined = mate::solve_mate_in_one(&pos);
    println!("table mate1ply: {}", table.map_or("-".to_string(), Move::to_usi));
    println!("yaneuraou mate1ply: {}", yane.map_or("-".to_string(), Move::to_usi));
    println!("yaneuraou (combined): {}", combined.map_or("-".to_string(), Move::to_usi));

    #[cfg(feature = "mate1ply-full")]
    {
        let ext = mate::yaneuraou::mate_1ply_extension(&pos);
        println!("yaneuraou mate1ply-extension: {}", ext.map_or("-".to_string(), Move::to_usi));
    }

    let mut moves = Vec::new();
    if let Some(usi) = move_usi {
        moves.push(move_from_usi(&pos, &usi)?);
    } else {
        if let Some(mv) = table {
            moves.push(mv);
        }
        if let Some(mv) = combined {
            if !moves.contains(&mv) {
                moves.push(mv);
            }
        }
    }

    for mv in moves {
        analyze_evasions(&pos, mv);
    }

    Ok(())
}
