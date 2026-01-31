//! 一手詰め判定ヘルパー（旧ロジック）。
//!
//! 比較検証用に旧実装を残す。

use super::{MoveList, Position};
use crate::board::attack_tables::{
    bishop_attacks, lance_attacks, rook_attacks, GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS,
    PAWN_ATTACKS, SILVER_ATTACKS,
};
use crate::board::mate_constant::get_mate_info;
use crate::board::movegen::{generate_checks, generate_moves, Evasions};
use crate::types::Bitboard;
use crate::types::{Color, HandPiece, Move, Piece, PieceType, RepetitionState, Square};
const OFFSETS_AROUND8: [(i8, i8); 8] =
    [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)];

/// Returns bitmask of valid squares around center.
fn valid_around8(center: Square) -> u8 {
    let mut mask = 0u8;
    let (cx, cy) = (center.file().raw(), center.rank().raw());
    for (i, &(dx, dy)) in OFFSETS_AROUND8.iter().enumerate() {
        let nx = cx + dx;
        let ny = cy + dy;
        if (0..9).contains(&nx) && (0..9).contains(&ny) {
            mask |= 1 << i;
        }
    }
    mask
}

/// Returns the 8-neighbor bitmask around `center` for the given `bb`.
fn around8(bb: Bitboard, center: Square) -> u8 {
    let mut mask = 0u8;
    let (cx, cy) = (center.file().raw(), center.rank().raw());

    for (i, &(dx, dy)) in OFFSETS_AROUND8.iter().enumerate() {
        let nx = cx + dx;
        let ny = cy + dy;
        if (0..9).contains(&nx) && (0..9).contains(&ny) {
            #[allow(clippy::cast_sign_loss)]
            let idx = (nx * 9 + ny) as usize;
            let n_sq = Square::from_index(idx);
            if bb.test(n_sq) {
                mask |= 1 << i;
            }
        }
    }
    mask
}

/// Helper to get bitmask of squares around King attacked by `color`.
fn around8_attacks(pos: &Position, center: Square, color: Color) -> u8 {
    let mut mask = 0u8;
    let (cx, cy) = (center.file().raw(), center.rank().raw());
    for (i, &(dx, dy)) in OFFSETS_AROUND8.iter().enumerate() {
        let nx = cx + dx;
        let ny = cy + dy;
        if (0..9).contains(&nx) && (0..9).contains(&ny) {
            #[allow(clippy::cast_sign_loss)]
            let idx = (nx * 9 + ny) as usize;
            let n_sq = Square::from_index(idx);
            if (pos.attackers_to(n_sq, pos.bitboards().occupied())
                & pos.bitboards().color_pieces(color))
            .any()
            {
                mask |= 1 << i;
            }
        }
    }
    mask
}

/// `solve_mate_in_three` の探索手順を要約して出力する。
#[must_use]
#[allow(clippy::cognitive_complexity, clippy::too_many_lines)]
#[allow(dead_code)]
pub fn debug_solve_mate_in_three_table(pos: &Position) -> String {
    use std::fmt::Write;

    const MAX_M1: usize = 8;
    const MAX_M2: usize = 8;

    let mut out = String::new();

    let root_ply = usize::from(pos.game_ply());
    let mut checks = MoveList::new();
    generate_checks(pos, &mut checks);
    let _ = writeln!(out, "mate3: checks={}", checks.len());

    let mut m1_count = 0usize;
    for m1 in checks.iter() {
        if !pos.is_legal(*m1) {
            continue;
        }
        m1_count += 1;
        if m1_count > MAX_M1 {
            let _ = writeln!(out, "mate3: m1 truncated");
            break;
        }

        let mut p1 = pos.clone();
        p1.init_stack();
        p1.do_move(*m1);

        let ply_from_root = usize::from(p1.game_ply()).saturating_sub(root_ply);
        let rep = p1.get_repetition_state_with_ply(ply_from_root);
        if rep != RepetitionState::None {
            let _ = writeln!(out, "m1 {m1:?}: repetition={rep:?}");
            let _ = writeln!(
                out,
                "m1 {m1:?}: repetition treated as mate={}",
                rep == RepetitionState::Lose
            );
            continue;
        }

        let mut evasions = MoveList::new();
        generate_moves::<Evasions>(&p1, &mut evasions);
        let mut legal_evasions = Vec::new();
        for m2 in evasions.iter() {
            if p1.is_legal(*m2) {
                legal_evasions.push(*m2);
            }
        }

        let _ = writeln!(out, "m1 {m1:?} usi={} : evasions={}", m1.to_usi(), legal_evasions.len());
        if legal_evasions.is_empty() {
            let _ = writeln!(out, "m1 {m1:?}: immediate mate");
            continue;
        }

        let mut m2_count = 0usize;
        let mut all_mate1 = true;
        for m2 in legal_evasions {
            m2_count += 1;
            if m2_count > MAX_M2 {
                let _ = writeln!(out, "m1 {m1:?}: m2 truncated");
                break;
            }
            let mut p2 = p1.clone();
            p2.init_stack();
            p2.do_move(m2);
            if solve_mate_in_one_table(&p2).is_none() {
                all_mate1 = false;
                let _ = writeln!(out, "  m2 {m2:?} usi={}: no mate1", m2.to_usi());
                break;
            }
            let _ = writeln!(out, "  m2 {m2:?} usi={}: mate1 ok", m2.to_usi());
        }

        if all_mate1 {
            let _ = writeln!(out, "m1 {m1:?}: all mate1 ok");
        }
    }

    out
}

/// Check if `sq` is attacked by `attacker_color` given the board occupancy `occupied`.
fn is_attacked(
    pos: &Position,
    sq: Square,
    occupied: Bitboard,
    attacker_color: Color,
    moved_piece: Option<(Option<Square>, Square, PieceType)>, // (from, to, pt)
) -> bool {
    let attackers = attackers_to_with_moved(pos, sq, occupied, attacker_color, moved_piece);
    !attackers.is_empty()
}

fn attackers_to_with_moved(
    pos: &Position,
    sq: Square,
    occupied: Bitboard,
    attacker_color: Color,
    moved_piece: Option<(Option<Square>, Square, PieceType)>, // (from, to, pt)
) -> Bitboard {
    let mut attackers =
        pos.attackers_to(sq, occupied) & pos.bitboards().color_pieces(attacker_color);
    let moved_color = pos.side_to_move();

    if attacker_color != moved_color {
        return attackers;
    }

    if let Some((from_opt, to, pt)) = moved_piece {
        if let Some(from) = from_opt {
            attackers.clear(from);
        }

        let attacks_from_to = get_piece_attacks(pt, to, attacker_color, occupied);
        if attacks_from_to.test(sq) {
            attackers.set(to);
        }
    }

    attackers
}

/// Helper to get attacks of a specific piece type/color/sq/occupied.
fn get_piece_attacks(pt: PieceType, sq: Square, color: Color, occupied: Bitboard) -> Bitboard {
    match pt {
        PieceType::PAWN => PAWN_ATTACKS[sq.to_index()][color.to_index()],
        PieceType::LANCE => lance_attacks(sq, occupied, color),
        PieceType::KNIGHT => KNIGHT_ATTACKS[sq.to_index()][color.to_index()],
        PieceType::SILVER => SILVER_ATTACKS[sq.to_index()][color.to_index()],
        PieceType::GOLD
        | PieceType::PRO_PAWN
        | PieceType::PRO_LANCE
        | PieceType::PRO_KNIGHT
        | PieceType::PRO_SILVER => GOLD_ATTACKS[sq.to_index()][color.to_index()],
        PieceType::KING => KING_ATTACKS[sq.to_index()],
        PieceType::BISHOP => bishop_attacks(sq, occupied),
        PieceType::ROOK => rook_attacks(sq, occupied),
        PieceType::HORSE => bishop_attacks(sq, occupied) | KING_ATTACKS[sq.to_index()],
        PieceType::DRAGON => rook_attacks(sq, occupied) | KING_ATTACKS[sq.to_index()],
        _ => Bitboard::EMPTY,
    }
}

/// Check if a piece at `sq` is pinned against the King `king_sq`.
fn is_pinned(
    pos: &Position,
    sq: Square,
    king_sq: Square,
    occupied: Bitboard,
    my_color: Color,
    moved_piece: Option<(Option<Square>, Square, PieceType)>, // (from, to, pt)
) -> bool {
    let enemy_color = my_color.flip();

    // Simple alignment check
    let direction = sq.file() == king_sq.file() || sq.rank() == king_sq.rank() || {
        let dx = i32::from(sq.file().raw()) - i32::from(king_sq.file().raw());
        let dy = i32::from(sq.rank().raw()) - i32::from(king_sq.rank().raw());
        dx.abs() == dy.abs()
    };

    if !direction {
        return false;
    }

    let occupied_without_pin = occupied ^ Bitboard::from_square(sq);
    let real_attackers = attackers_to_with_moved(pos, king_sq, occupied, enemy_color, moved_piece);
    let simulated_attackers =
        attackers_to_with_moved(pos, king_sq, occupied_without_pin, enemy_color, moved_piece);

    let exposed = simulated_attackers & !real_attackers;

    !exposed.is_empty()
}

/// Core Logic: Verify if a candidate move `mv` is a Checkmate.
fn is_mate_bitboard(pos: &Position, mv: Move) -> bool {
    let us = pos.side_to_move();
    let them = us.flip();
    let king_sq = pos.bitboards().pieces_of(PieceType::KING, them).lsb().unwrap();

    let mut occupied = pos.bitboards().occupied();
    let moves_from = mv.from_sq();
    let moves_to = mv.to_sq();
    let captured_piece = if mv.is_drop() {
        None
    } else {
        let captured = pos.piece_on(moves_to);
        if captured == Piece::NO_PIECE {
            None
        } else {
            Some((captured, moves_to))
        }
    };

    let moved_piece_def = if mv.is_drop() {
        occupied.set(moves_to);
        let pt = mv.dropped_piece().unwrap();
        Some((None, moves_to, pt))
    } else {
        occupied.clear(moves_from);
        occupied.set(moves_to);
        let mut pt = pos.piece_on(moves_from).piece_type();
        if mv.is_promote() {
            pt = pt.promote();
        }
        Some((Some(moves_from), moves_to, pt))
    };

    // Recalculate checkers on the board AFTER the move
    // We cannot trust `moves_to` is the only checker.
    let mut actual_checkers = Bitboard::from_square(moves_to);

    // 1. Direct Check from the moved piece?
    let pt_at_dest = match moved_piece_def {
        Some((_, _, pt)) => pt,
        None => pos.piece_on(moves_to).piece_type(),
    };

    // Check if moved piece attacks King
    let attacks = get_piece_attacks(pt_at_dest, moves_to, us, occupied);
    if !attacks.test(king_sq) {
        actual_checkers.clear(moves_to);
    }

    // 2. Discovered Checks?
    // Use `occupied` (post-move) to find all checkers from `us` side.
    // Note: `pos.attackers_to` uses `pos` bitboards which still have `from` occupied.
    // But `occupied` argument handles sliding pieces blockage correctly.
    // The only issue is if `from` piece is detected as attacker.
    let mut discovered = pos.attackers_to(king_sq, occupied) & pos.bitboards().color_pieces(us);
    if let Some((Some(from), _, _)) = moved_piece_def {
        discovered.clear(from);
    }
    // Also clear moves_to from discovered to avoid duplication (though safe to merge)
    // discovered.clear(moves_to);

    actual_checkers = actual_checkers | discovered;

    if actual_checkers.is_empty() {
        return false;
    }

    let double_check = actual_checkers.count() > 1;

    // 2. Check King Escape
    let king_moves = KING_ATTACKS[king_sq.to_index()];
    let mut them_pieces = pos.bitboards().color_pieces(them);
    // CRITICAL FIX: Capture Masking
    them_pieces.clear(moves_to);

    let escape_targets = king_moves & !them_pieces;

    let mut targets_iter = escape_targets;
    while let Some(dest) = targets_iter.pop_lsb() {
        let occupied_for_escape = occupied ^ Bitboard::from_square(king_sq);
        if !is_attacked(pos, dest, occupied_for_escape, us, moved_piece_def) {
            return false;
        }
    }

    if double_check {
        return true;
    }

    // Single Check Logic (Capture / Interpose)
    let checker_sq = actual_checkers.lsb().unwrap();

    // 3. Check Capture Checker
    let mut potential_capturers = pos.attackers_to(checker_sq, occupied) & them_pieces;
    potential_capturers.clear(king_sq);

    while let Some(cap_sq) = potential_capturers.pop_lsb() {
        if is_pinned(pos, cap_sq, king_sq, occupied, them, moved_piece_def) {
            let ray = Bitboard::line(king_sq, cap_sq);
            if ray.test(checker_sq) {
                return false;
            }
            continue;
        }
        return false;
    }

    // 4. Check Interposition
    // Always calculate path between King and the Actual Checker.
    // This handles both Direct Checks and Discovered Checks correctly.
    let path = Bitboard::between(king_sq, checker_sq);

    if !path.is_empty() {
        let mut path_iter = path;
        while let Some(sq) = path_iter.pop_lsb() {
            let mut blockers = pos.attackers_to(sq, occupied) & them_pieces;
            blockers.clear(king_sq);

            let hand = pos.hand_of(them);
            if hand.0 > 0 && has_valid_drop(pos, sq, them, hand, captured_piece) {
                return false;
            }

            while let Some(from) = blockers.pop_lsb() {
                if is_pinned(pos, from, king_sq, occupied, them, moved_piece_def) {
                    let ray = Bitboard::line(king_sq, from);
                    if ray.test(sq) {
                        return false;
                    }
                    continue;
                }
                return false;
            }
        }
    }

    true
}

/// Helper to check if any piece from hand can be dropped at `sq`.
fn has_valid_drop(
    pos: &Position,
    sq: Square,
    color: Color,
    hand: crate::types::Hand,
    captured_piece: Option<(Piece, Square)>,
) -> bool {
    let has_non_pawn = hand.count(HandPiece::HAND_LANCE) > 0
        || hand.count(HandPiece::HAND_KNIGHT) > 0
        || hand.count(HandPiece::HAND_SILVER) > 0
        || hand.count(HandPiece::HAND_GOLD) > 0
        || hand.count(HandPiece::HAND_BISHOP) > 0
        || hand.count(HandPiece::HAND_ROOK) > 0;

    if has_non_pawn {
        let rank = sq.rank().raw();
        if color == Color::BLACK {
            if rank == 0 {
                if hand.count(HandPiece::HAND_SILVER) > 0
                    || hand.count(HandPiece::HAND_GOLD) > 0
                    || hand.count(HandPiece::HAND_BISHOP) > 0
                    || hand.count(HandPiece::HAND_ROOK) > 0
                {
                    return true;
                }
                return false;
            }
            if rank == 1 {
                if hand.count(HandPiece::HAND_LANCE) > 0
                    || hand.count(HandPiece::HAND_SILVER) > 0
                    || hand.count(HandPiece::HAND_GOLD) > 0
                    || hand.count(HandPiece::HAND_BISHOP) > 0
                    || hand.count(HandPiece::HAND_ROOK) > 0
                {
                    return true;
                }
                return false;
            }
        }
        if color == Color::WHITE {
            if rank == 8 {
                if hand.count(HandPiece::HAND_SILVER) > 0
                    || hand.count(HandPiece::HAND_GOLD) > 0
                    || hand.count(HandPiece::HAND_BISHOP) > 0
                    || hand.count(HandPiece::HAND_ROOK) > 0
                {
                    return true;
                }
                return false;
            }
            if rank == 7 {
                if hand.count(HandPiece::HAND_LANCE) > 0
                    || hand.count(HandPiece::HAND_SILVER) > 0
                    || hand.count(HandPiece::HAND_GOLD) > 0
                    || hand.count(HandPiece::HAND_BISHOP) > 0
                    || hand.count(HandPiece::HAND_ROOK) > 0
                {
                    return true;
                }
                return false;
            }
        }
        return true;
    }

    if hand.count(HandPiece::HAND_PAWN) > 0
        && !has_pawn_on_file_after_capture(pos, color, sq.file(), captured_piece)
    {
        if (color == Color::BLACK && sq.rank().raw() == 0)
            || (color == Color::WHITE && sq.rank().raw() == 8)
        {
            return false;
        }
        return true;
    }

    false
}

fn has_pawn_on_file_after_capture(
    pos: &Position,
    color: Color,
    file: crate::types::File,
    captured_piece: Option<(Piece, Square)>,
) -> bool {
    let mut pawns = pos.bitboards().pieces_of(PieceType::PAWN, color);
    if let Some((piece, sq)) = captured_piece {
        if piece.piece_type() == PieceType::PAWN && piece.color() == color {
            pawns.clear(sq);
        }
    }
    !(pawns & Bitboard::file_mask(file)).is_empty()
}

/// 現局面で先手側が一手で詰ませられる指し手を探索する。
/// 一手詰め判定。
#[must_use]
#[allow(clippy::too_many_lines)]
pub fn solve_mate_in_one_table(pos: &Position) -> Option<Move> {
    let us = pos.side_to_move();
    let them = us.flip();

    if pos.bitboards().pieces_of(PieceType::KING, them).is_empty() {
        return None;
    }
    let ksq = pos.bitboards().pieces_of(PieceType::KING, them).lsb().expect("King not found");

    // 1. Build Info Index
    let occupied_bb = pos.bitboards().occupied();
    let valid_mask = valid_around8(ksq);
    let _a8_droppable = (!around8(occupied_bb, ksq)) & valid_mask;
    let them_pieces = pos.bitboards().color_pieces(them);
    let a8_them_movable = (!around8(them_pieces, ksq)) & valid_mask;
    let a8_targetable = (!around8(pos.bitboards().color_pieces(us), ksq)) & valid_mask;
    let a8_effect_us = around8_attacks(pos, ksq, us);

    let info1 = a8_targetable;
    let info2 = a8_them_movable & !a8_effect_us;
    let idx = (usize::from(info1)) | (usize::from(info2) << 8);
    let c = us.to_index();

    let mate_info = get_mate_info(idx, c);

    // 2. Drop Mate Check
    if mate_info.hand_kind != 0 || mate_info.directions != 0 {
        let hand = pos.hand_of(us);
        let needed = mate_info.hand_kind;
        if needed != 0 {
            let types = [
                (PieceType::GOLD, 6),
                (PieceType::SILVER, 3),
                (PieceType::ROOK, 5),
                (PieceType::LANCE, 1),
                (PieceType::BISHOP, 4),
                (PieceType::KNIGHT, 2),
            ];

            for &(pt, bit_idx) in &types {
                if (needed & (1 << bit_idx)) != 0
                    && hand.count(HandPiece::from_piece_type(pt).unwrap()) > 0
                {
                    for dir in 0..8 {
                        if (valid_mask & (1 << dir)) != 0 {
                            let (cx, cy) = (ksq.file().raw(), ksq.rank().raw());
                            let offsets = [
                                (0, -1),
                                (1, -1),
                                (1, 0),
                                (1, 1),
                                (0, 1),
                                (-1, 1),
                                (-1, 0),
                                (-1, -1),
                            ];
                            let (dx, dy) = offsets[dir];
                            let nx = i32::from(cx) + dx;
                            let ny = i32::from(cy) + dy;

                            #[allow(clippy::cast_sign_loss)]
                            let idx2 = (nx * 9 + ny) as usize;
                            let to = Square::from_index(idx2);

                            if !occupied_bb.test(to) {
                                // Verify that drop gives check! (Table compression might propose non-checking moves)
                                let new_occ = occupied_bb | Bitboard::from_square(to);
                                if !get_piece_attacks(pt, to, us, new_occ).test(ksq) {
                                    continue;
                                }

                                let mv = Move::make_drop(pt, to, us);
                                if is_mate_bitboard(pos, mv) {
                                    return Some(mv);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 3. Move Mate Check
    let mut checks = MoveList::new();
    generate_checks(pos, &mut checks);

    for mv in checks.iter() {
        if !pos.is_legal(*mv) {
            continue;
        }

        if is_mate_bitboard(pos, *mv) {
            return Some(*mv);
        }
    }

    None
}

/// Solves for a mate-in-3 from the current position.
#[must_use]
#[allow(dead_code)]
pub fn solve_mate_in_three_table(pos: &Position) -> Option<(Move, Move, Move)> {
    // Optimization: Use a single clone for M1 to save allocation if possible,
    // but here we might need a clone per depth.
    // Actually applying move to a cloned position is simplest logic here.
    // If performance is an issue, consider other approaches later.
    let mut local_pos = pos.clone();
    // Re-calculating state is safer, though expensive.
    // `solve_mate_in_three` is typically used for finishing, so it's acceptable.
    // Actually Position::clone copies everything including checkers/pin_info.
    // But applying move requires stack re-init.
    local_pos.init_stack();

    let root_ply = usize::from(pos.game_ply());
    let mut checks = MoveList::new();
    generate_checks(pos, &mut checks);

    if checks.is_empty() {
        return None;
    }

    for m1 in checks.iter() {
        if !pos.is_legal(*m1) {
            continue;
        }

        // 1. Apply M1
        local_pos.do_move(*m1);

        // Repetition handling (YaneuraOu mate_repetition 相当の簡略版)
        let ply_from_root = usize::from(local_pos.game_ply()).saturating_sub(root_ply);
        let rep = local_pos.get_repetition_state_with_ply(ply_from_root);
        if rep != RepetitionState::None {
            let _ = local_pos.undo_move(*m1);
            if rep == RepetitionState::Lose {
                return Some((*m1, crate::types::MOVE_NONE, crate::types::MOVE_NONE));
            }
            continue;
        }

        // 2. Generate Evasions (Defender moves)
        let mut evasions = MoveList::new();
        if local_pos.checkers().is_empty() {
            let _ = local_pos.undo_move(*m1);
            continue;
        }

        generate_moves::<Evasions>(&local_pos, &mut evasions);

        let legal_evasions: Vec<_> =
            evasions.iter().copied().filter(|mv| local_pos.is_legal(*mv)).collect();

        // If no legal evasions, it's actually a 1-ply mate.
        if legal_evasions.is_empty() {
            let _ = local_pos.undo_move(*m1);
            return Some((*m1, crate::types::MOVE_NONE, crate::types::MOVE_NONE));
        }

        // 3. Verify all evasions lead to mate-in-1
        let mut all_evasions_mated = true;
        let mut pv_line = None;

        for m2 in &legal_evasions {
            if !local_pos.is_legal(*m2) {
                continue;
            }
            local_pos.do_move(*m2);
            // Reverse Check (if evasion checks attacker, it's considered escape in this simple solver)
            if !local_pos.checkers().is_empty() {
                all_evasions_mated = false;
                let _ = local_pos.undo_move(*m2);
                break;
            }

            // Check mate-in-1 (m3)
            if let Some(m3) = solve_mate_in_one_table(&local_pos) {
                if pv_line.is_none() {
                    pv_line = Some((*m2, m3));
                }
                let _ = local_pos.undo_move(*m2);
            } else {
                // No mate response
                all_evasions_mated = false;
                let _ = local_pos.undo_move(*m2);
                break;
            }
        }

        let _ = local_pos.undo_move(*m1);

        if all_evasions_mated {
            if let Some((m2, m3)) = pv_line {
                return Some((*m1, m2, m3));
            }
            // If all evasions were empty? Already handled.
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::movegen::{generate_moves, NonEvasionsAll};

    const MATE_TEST_SFENS: &[&str] = &[
        "lnsG5/4g4/prpp1p1pp/1p4p1k/4+B4/2P1P3P/P+b1PSP1L1/4K2SL/2G2G1r1 b SP3nl3p 73",
        "ln2+P2nl/2R1+S1g2/p2p1p1p+B/8p/5+R3/2p3PkP/PP1PPP3/2+bS1KS2/5G1NL b GL4Pgsn 83",
        "l2+R3g1/2ln5/2k1ps+Bp1/2p3P2/p3Sp1P1/7b1/PLPKPP3/1S1G2G2/LN1s+n+r1N1 b G4P3p 103",
        "l2+S3kl/9/3p1pG+S1/ppp3Pp1/4+RP1np/P1n1S1p2/1P1PS1gN1/2G1G4/L2K3RL b 3P2bn2p 115",
        "l1ggk3l/3plsG2/4sp+P2/p2+Bp2pp/5n1+b1/2+RSPN3/Pp1P1P+n1P/3K5/L7+n b RS3Pg2p 117",
    ];

    #[test]
    fn detects_mate_in_one_move() {
        for &sfen in MATE_TEST_SFENS {
            let position = crate::board::position_from_sfen(sfen).expect("valid sfen");

            let mv = solve_mate_in_one_table(&position).expect("mate move should exist");
            println!("Detected mate move: {}", mv.to_usi());

            // Verify
            let mut next = position.clone();
            next.init_stack();

            next.do_move(mv);
            assert!(!next.checkers().is_empty(), "resulting position must give check");

            let mut replies = MoveList::new();
            generate_moves::<NonEvasionsAll>(&next, &mut replies);

            let mut legals = 0;
            for r in replies.iter() {
                if next.is_legal(*r) {
                    legals += 1;
                }
            }
            assert_eq!(legals, 0, "opponent should have no legal replies");
        }
    }

    #[test]
    fn returns_none_when_no_mate() {
        let position = crate::board::hirate_position();
        assert!(solve_mate_in_one_table(&position).is_none());
    }

    #[test]
    fn test_solve_mate_in_three_core() {
        let sfen = "l5l1l/4lsS2/p2p1p3/7pk/1pP2Np2/5NPGg/PP1P1P2R/2G2S3/+bNSK1G3 b RPbn5p 111";
        let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
        let result = solve_mate_in_three_table(&pos);
        assert!(result.is_some());
        let (m1, _m2, _m3) = result.unwrap();
        assert!(pos.is_legal(m1));

        let mut local_pos = pos;
        local_pos.init_stack();
        local_pos.do_move(m1);
        assert!(!local_pos.checkers().is_empty(), "resulting position must give check");

        let mut evasions = MoveList::new();
        generate_moves::<Evasions>(&local_pos, &mut evasions);
        let legal_evasions: Vec<_> =
            evasions.iter().copied().filter(|mv| local_pos.is_legal(*mv)).collect();
        if legal_evasions.is_empty() {
            return;
        }

        for m2 in &legal_evasions {
            local_pos.do_move(*m2);
            assert!(
                solve_mate_in_one_table(&local_pos).is_some(),
                "mate response must exist for every evasion"
            );
            local_pos.undo_move(*m2).expect("undo evasion");
        }
    }
}
