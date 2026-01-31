use crate::board::attack_tables::{
    bishop_attacks, lance_attacks, rook_attacks, CHECK_CANDIDATE_BB, GOLD_ATTACKS, KING_ATTACKS,
    KNIGHT_ATTACKS, PAWN_ATTACKS, SILVER_ATTACKS,
};
use crate::board::{Bitboard, Position};
use crate::types::{Color, Move, Piece, PieceType, Rank, Square};

use super::promotions::{can_promote, must_promote};
use super::{Black, ColorMarker, MoveSink, White};

fn enemy_territory(us: Color) -> Bitboard {
    match us {
        Color::BLACK => {
            Bitboard::rank_mask(Rank::RANK_1)
                | Bitboard::rank_mask(Rank::RANK_2)
                | Bitboard::rank_mask(Rank::RANK_3)
        }
        Color::WHITE => {
            Bitboard::rank_mask(Rank::RANK_7)
                | Bitboard::rank_mask(Rank::RANK_8)
                | Bitboard::rank_mask(Rank::RANK_9)
        }
        _ => Bitboard::EMPTY,
    }
}

#[inline]
fn pawn_effect(color: Color, sq: Square) -> Bitboard {
    PAWN_ATTACKS[sq.to_index()][color.to_index()]
}

#[inline]
fn knight_effect(color: Color, sq: Square) -> Bitboard {
    KNIGHT_ATTACKS[sq.to_index()][color.to_index()]
}

#[inline]
fn silver_effect(color: Color, sq: Square) -> Bitboard {
    SILVER_ATTACKS[sq.to_index()][color.to_index()]
}

#[inline]
fn gold_effect(color: Color, sq: Square) -> Bitboard {
    GOLD_ATTACKS[sq.to_index()][color.to_index()]
}

#[inline]
fn king_effect(sq: Square) -> Bitboard {
    KING_ATTACKS[sq.to_index()]
}

#[inline]
fn horse_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    bishop_attacks(sq, occupied) | king_effect(sq)
}

#[inline]
fn dragon_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    rook_attacks(sq, occupied) | king_effect(sq)
}

const fn check_candidate_index(pt: PieceType) -> Option<usize> {
    match pt {
        PieceType::PAWN => Some(0),
        PieceType::LANCE => Some(1),
        PieceType::KNIGHT => Some(2),
        PieceType::SILVER => Some(3),
        PieceType::GOLD => Some(4),
        PieceType::BISHOP => Some(5),
        PieceType::ROOK => Some(6),
        _ => None,
    }
}

fn check_candidate_bb(us: Color, pt: PieceType, ksq: Square) -> Bitboard {
    let Some(idx) = check_candidate_index(pt) else {
        return Bitboard::EMPTY;
    };
    CHECK_CANDIDATE_BB[ksq.to_index()][idx][us.to_index()]
}

fn can_promote_sq(us: Color, sq: Square) -> bool {
    enemy_territory(us).test(sq)
}

#[allow(clippy::too_many_arguments)]
fn make_move_target_pro(
    piece: Piece,
    us: Color,
    pt: PieceType,
    all: bool,
    promote: bool,
    from: Square,
    target: Bitboard,
    list: &mut impl MoveSink,
) {
    let mut bb = target;
    while let Some(to) = bb.pop_lsb() {
        if promote {
            list.push_move(Move::make_promote(from, to, piece));
            continue;
        }

        let allow = if pt == PieceType::PAWN {
            (!all && !can_promote_sq(us, to))
                || (all
                    && to.rank() != if us == Color::BLACK { Rank::RANK_1 } else { Rank::RANK_9 })
        } else if pt == PieceType::LANCE {
            (!all
                && ((us == Color::BLACK && to.rank() >= Rank::RANK_3)
                    || (us == Color::WHITE && to.rank() <= Rank::RANK_7)))
                || (all
                    && to.rank() != if us == Color::BLACK { Rank::RANK_1 } else { Rank::RANK_9 })
        } else if pt == PieceType::KNIGHT {
            (us == Color::BLACK && to.rank() >= Rank::RANK_3)
                || (us == Color::WHITE && to.rank() <= Rank::RANK_7)
        } else if pt == PieceType::SILVER {
            true
        } else if pt == PieceType::BISHOP || pt == PieceType::ROOK {
            !(can_promote_sq(us, from) || can_promote_sq(us, to)) || all
        } else {
            false
        };

        if allow {
            list.push_move(Move::make(from, to, piece));
        }
    }
}

#[allow(clippy::cognitive_complexity, clippy::too_many_lines)]
fn make_move_target_general(
    pos: &Position,
    piece: Piece,
    from: Square,
    target: Bitboard,
    list: &mut impl MoveSink,
    all: bool,
    us: Color,
) {
    let occupied = pos.bitboards().occupied();
    let pt = piece.piece_type();

    let attacks = match pt {
        PieceType::PAWN => pawn_effect(us, from),
        PieceType::LANCE => lance_attacks(from, occupied, us),
        PieceType::KNIGHT => knight_effect(us, from),
        PieceType::SILVER => silver_effect(us, from),
        PieceType::GOLD
        | PieceType::PRO_PAWN
        | PieceType::PRO_LANCE
        | PieceType::PRO_KNIGHT
        | PieceType::PRO_SILVER => gold_effect(us, from),
        PieceType::BISHOP => bishop_attacks(from, occupied),
        PieceType::ROOK => rook_attacks(from, occupied),
        PieceType::HORSE => horse_effect(from, occupied),
        PieceType::DRAGON => dragon_effect(from, occupied),
        PieceType::KING => king_effect(from),
        _ => Bitboard::EMPTY,
    };

    let mut target = attacks & target;
    if target.is_empty() {
        return;
    }

    match pt {
        PieceType::PAWN => {
            while let Some(to) = target.pop_lsb() {
                if can_promote(from, to, us) {
                    list.push_move(Move::make_promote(from, to, piece));
                    if all
                        && to.rank() != if us == Color::BLACK { Rank::RANK_1 } else { Rank::RANK_9 }
                    {
                        list.push_move(Move::make(from, to, piece));
                    }
                } else {
                    list.push_move(Move::make(from, to, piece));
                }
            }
        }
        PieceType::LANCE => {
            let enemy = enemy_territory(us);
            let mut promote = target & enemy;
            while let Some(to) = promote.pop_lsb() {
                list.push_move(Move::make_promote(from, to, piece));
            }
            let non_promote_mask = if all {
                if us == Color::BLACK {
                    Bitboard::ALL.and_not(Bitboard::rank_mask(Rank::RANK_1))
                } else {
                    Bitboard::ALL.and_not(Bitboard::rank_mask(Rank::RANK_9))
                }
            } else if us == Color::BLACK {
                Bitboard::ALL
                    .and_not(Bitboard::rank_mask(Rank::RANK_1))
                    .and_not(Bitboard::rank_mask(Rank::RANK_2))
            } else {
                Bitboard::ALL
                    .and_not(Bitboard::rank_mask(Rank::RANK_8))
                    .and_not(Bitboard::rank_mask(Rank::RANK_9))
            };
            let mut non_promote = target & non_promote_mask;
            while let Some(to) = non_promote.pop_lsb() {
                if must_promote(pt, to, us) {
                    continue;
                }
                list.push_move(Move::make(from, to, piece));
            }
        }
        PieceType::KNIGHT => {
            while let Some(to) = target.pop_lsb() {
                if can_promote(from, to, us) {
                    list.push_move(Move::make_promote(from, to, piece));
                }
                if (us == Color::BLACK && to.rank() >= Rank::RANK_3)
                    || (us == Color::WHITE && to.rank() <= Rank::RANK_7)
                {
                    list.push_move(Move::make(from, to, piece));
                }
            }
        }
        PieceType::SILVER => {
            let enemy = enemy_territory(us);
            if enemy.test(from) {
                let mut bb = target;
                while let Some(to) = bb.pop_lsb() {
                    list.push_move(Move::make_promote(from, to, piece));
                    list.push_move(Move::make(from, to, piece));
                }
            } else {
                let mut promote = target & enemy;
                while let Some(to) = promote.pop_lsb() {
                    list.push_move(Move::make_promote(from, to, piece));
                    list.push_move(Move::make(from, to, piece));
                }
                let mut non_promote = target.and_not(enemy);
                while let Some(to) = non_promote.pop_lsb() {
                    list.push_move(Move::make(from, to, piece));
                }
            }
        }
        PieceType::BISHOP | PieceType::ROOK => {
            let enemy = enemy_territory(us);
            if enemy.test(from) {
                let mut bb = target;
                while let Some(to) = bb.pop_lsb() {
                    list.push_move(Move::make_promote(from, to, piece));
                    if all {
                        list.push_move(Move::make(from, to, piece));
                    }
                }
            } else {
                let mut promote = target & enemy;
                while let Some(to) = promote.pop_lsb() {
                    list.push_move(Move::make_promote(from, to, piece));
                    if all {
                        list.push_move(Move::make(from, to, piece));
                    }
                }
                let mut non_promote = target.and_not(enemy);
                while let Some(to) = non_promote.pop_lsb() {
                    list.push_move(Move::make(from, to, piece));
                }
            }
        }
        _ => {
            while let Some(to) = target.pop_lsb() {
                list.push_move(Move::make(from, to, piece));
            }
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn make_move_check(
    pos: &Position,
    piece: Piece,
    from: Square,
    ksq: Square,
    target: Bitboard,
    list: &mut impl MoveSink,
    all: bool,
    us: Color,
    them: Color,
) {
    let pt = piece.piece_type();
    let enemy = enemy_territory(us);
    let occupied = pos.bitboards().occupied();

    match pt {
        PieceType::PAWN => {
            let mut dst = pawn_effect(us, from) & gold_effect(them, ksq) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);
            let dst = pawn_effect(us, from) & pawn_effect(them, ksq) & target;
            make_move_target_pro(piece, us, pt, all, false, from, dst, list);
        }
        PieceType::KNIGHT => {
            let mut dst = knight_effect(us, from) & gold_effect(them, ksq) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);
            let dst = knight_effect(us, from) & knight_effect(them, ksq) & target;
            make_move_target_pro(piece, us, pt, all, false, from, dst, list);
        }
        PieceType::SILVER => {
            let mut dst = silver_effect(us, from) & gold_effect(them, ksq) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);
            let dst = silver_effect(us, from) & silver_effect(them, ksq) & target;
            make_move_target_pro(piece, us, pt, all, false, from, dst, list);
        }
        PieceType::LANCE => {
            let mut dst = lance_attacks(from, occupied, us) & gold_effect(them, ksq) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);

            if from.file() == ksq.file() {
                let between = Bitboard::between(from, ksq) & occupied;
                if between.count() <= 1 {
                    let dst =
                        pos.bitboards().color_pieces(them) & Bitboard::between(from, ksq) & target;
                    make_move_target_pro(piece, us, pt, all, false, from, dst, list);
                }
            }
        }
        PieceType::BISHOP => {
            let mut dst = bishop_attacks(from, occupied) & horse_effect(ksq, occupied) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);
            let dst = bishop_attacks(from, occupied) & bishop_attacks(ksq, occupied) & target;
            make_move_target_pro(piece, us, pt, all, false, from, dst, list);
        }
        PieceType::ROOK => {
            let mut dst = rook_attacks(from, occupied) & dragon_effect(ksq, occupied) & target;
            if !enemy.test(from) {
                dst = dst & enemy;
            }
            make_move_target_pro(piece, us, pt, all, true, from, dst, list);
            let dst = rook_attacks(from, occupied) & rook_attacks(ksq, occupied) & target;
            make_move_target_pro(piece, us, pt, all, false, from, dst, list);
        }
        PieceType::GOLD
        | PieceType::PRO_PAWN
        | PieceType::PRO_LANCE
        | PieceType::PRO_KNIGHT
        | PieceType::PRO_SILVER => {
            let dst = gold_effect(us, from) & gold_effect(them, ksq) & target;
            let mut bb = dst;
            while let Some(to) = bb.pop_lsb() {
                list.push_move(Move::make(from, to, piece));
            }
        }
        PieceType::HORSE => {
            let dst = horse_effect(from, occupied) & horse_effect(ksq, occupied) & target;
            let mut bb = dst;
            while let Some(to) = bb.pop_lsb() {
                list.push_move(Move::make(from, to, piece));
            }
        }
        PieceType::DRAGON => {
            let dst = dragon_effect(from, occupied) & dragon_effect(ksq, occupied) & target;
            let mut bb = dst;
            while let Some(to) = bb.pop_lsb() {
                list.push_move(Move::make(from, to, piece));
            }
        }
        _ => {}
    }
}

fn generate_checks_internal(
    pos: &Position,
    list: &mut impl MoveSink,
    all: bool,
    quiet_only: bool,
    us: Color,
    them: Color,
) {
    let bb = pos.bitboards();
    let Some(ksq) = bb.pieces_of(PieceType::KING, them).lsb() else {
        return;
    };

    let golds = bb.pieces_of(PieceType::GOLD, us)
        | bb.pieces_of(PieceType::PRO_PAWN, us)
        | bb.pieces_of(PieceType::PRO_LANCE, us)
        | bb.pieces_of(PieceType::PRO_KNIGHT, us)
        | bb.pieces_of(PieceType::PRO_SILVER, us);

    let x = (bb.pieces_of(PieceType::PAWN, us) & check_candidate_bb(us, PieceType::PAWN, ksq))
        | (bb.pieces_of(PieceType::LANCE, us) & check_candidate_bb(us, PieceType::LANCE, ksq))
        | (bb.pieces_of(PieceType::KNIGHT, us) & check_candidate_bb(us, PieceType::KNIGHT, ksq))
        | (bb.pieces_of(PieceType::SILVER, us) & check_candidate_bb(us, PieceType::SILVER, ksq))
        | (golds & check_candidate_bb(us, PieceType::GOLD, ksq))
        | (bb.pieces_of(PieceType::BISHOP, us) & check_candidate_bb(us, PieceType::BISHOP, ksq))
        | (bb.pieces_of(PieceType::ROOK, us) | bb.pieces_of(PieceType::DRAGON, us))
        | (bb.pieces_of(PieceType::HORSE, us) & check_candidate_bb(us, PieceType::ROOK, ksq));

    let y = pos.blockers_for_king(them) & bb.color_pieces(us);

    let target = if quiet_only { bb.empty() } else { !bb.color_pieces(us) };

    let mut src = y;
    while let Some(from) = src.pop_lsb() {
        let piece = pos.piece_on(from);
        let pin_line = Bitboard::line(ksq, from);
        make_move_target_general(pos, piece, from, target.and_not(pin_line), list, all, us);
        if x.test(from) {
            make_move_check(pos, piece, from, ksq, pin_line & target, list, all, us, them);
        }
    }

    let mut src = x.and_not(y);
    while let Some(from) = src.pop_lsb() {
        let piece = pos.piece_on(from);
        make_move_check(pos, piece, from, ksq, target, list, all, us, them);
    }

    match us {
        Color::BLACK => generate_checks_drops_part_color::<Black>(pos, list),
        Color::WHITE => generate_checks_drops_part_color::<White>(pos, list),
        _ => {}
    }
}

/// 王手となる指し手を生成
#[inline]
pub fn generate_checks(pos: &Position, list: &mut impl MoveSink) {
    match pos.side_to_move() {
        Color::BLACK => generate_checks_for_color::<Black>(pos, list, false, false),
        Color::WHITE => generate_checks_for_color::<White>(pos, list, false, false),
        _ => {}
    }
}

/// 王手となる静かな手を生成
#[inline]
pub fn generate_quiet_checks(pos: &Position, list: &mut impl MoveSink) {
    match pos.side_to_move() {
        Color::BLACK => generate_checks_for_color::<Black>(pos, list, false, true),
        Color::WHITE => generate_checks_for_color::<White>(pos, list, false, true),
        _ => {}
    }
}

#[inline]
pub fn generate_checks_for_color<C: ColorMarker>(
    pos: &Position,
    list: &mut impl MoveSink,
    all: bool,
    quiet_only: bool,
) {
    generate_checks_internal(pos, list, all, quiet_only, C::COLOR, C::THEM);
}

#[inline]
pub fn generate_checks_drops_part(pos: &Position, list: &mut impl MoveSink) {
    match pos.side_to_move() {
        Color::BLACK => generate_checks_drops_part_color::<Black>(pos, list),
        Color::WHITE => generate_checks_drops_part_color::<White>(pos, list),
        _ => {}
    }
}

#[inline]
pub fn generate_checks_drops_part_color<C: ColorMarker>(pos: &Position, list: &mut impl MoveSink) {
    use crate::types::HandPiece;

    let us = C::COLOR;
    let bb = pos.bitboards();
    let hand = pos.hand_of(us);
    let empty = !bb.occupied();

    for piece_type in [
        PieceType::PAWN,
        PieceType::LANCE,
        PieceType::KNIGHT,
        PieceType::SILVER,
        PieceType::GOLD,
        PieceType::BISHOP,
        PieceType::ROOK,
    ] {
        let Some(hand_piece) = HandPiece::from_piece_type(piece_type) else {
            continue;
        };
        if hand.count(hand_piece) == 0 {
            continue;
        }

        let mut target = empty & pos.check_squares(piece_type);
        while let Some(to) = target.pop_lsb() {
            if piece_type == PieceType::PAWN && !pos.legal_pawn_drop(us, to) {
                continue;
            }
            list.push_move(Move::make_drop(piece_type, to, us));
        }
    }
}
