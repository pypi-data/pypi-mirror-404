use crate::board::{Bitboard, Position};
use crate::types::{Color, File, Move, PieceType, Square, SQ_D, SQ_U};

use super::promotions::{can_promote, must_promote};
use super::types::MoveGenType;
use super::MoveSink;

fn pawn_bb_effect(pawns: Bitboard, us: Color) -> Bitboard {
    let mut out = Bitboard::EMPTY;
    for file_idx in 0..9 {
        let file = File::new(file_idx);
        let file_mask = Bitboard::file_mask(file);
        let file_bits = pawns & file_mask;
        if file_bits.is_empty() {
            continue;
        }
        let mask_bits = file_mask.packed_bits();
        let shifted = if us == Color::BLACK {
            file_bits.packed_bits() >> 1
        } else {
            file_bits.packed_bits() << 1
        };
        out = out | Bitboard::from_packed_bits(shifted & mask_bits);
    }
    out
}

/// 歩の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_pawn_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    us: Color,
) {
    let bb = pos.bitboards();
    let allow_underpromote = T::generate_all_legal();
    let pawns = bb.pieces_of(PieceType::PAWN, us);
    let mut destinations = pawn_bb_effect(pawns, us).and(target);

    while let Some(to) = destinations.pop_lsb() {
        let from =
            if us == Color::BLACK { Square::new(to.0 + SQ_D) } else { Square::new(to.0 + SQ_U) };
        let piece = pos.piece_on(from);
        let must_promote = must_promote(piece.piece_type(), to, us);
        if must_promote {
            list.push_move(Move::make_promote(from, to, piece));
            continue;
        }

        let can_promote = can_promote(from, to, us);
        if can_promote {
            list.push_move(Move::make_promote(from, to, piece));
        }
        if allow_underpromote || !can_promote {
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 桂馬の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_knight_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::KNIGHT_ATTACKS;

    let bb = pos.bitboards();
    let mut knights = bb.pieces_of(PieceType::KNIGHT, us);

    while let Some(from) = knights.pop_lsb() {
        let attacks = KNIGHT_ATTACKS[from.to_index()][us.to_index()];
        let mut destinations = attacks.and(target);

        while let Some(to) = destinations.pop_lsb() {
            let piece = pos.piece_on(from);
            let must_promote = must_promote(piece.piece_type(), to, us);
            if must_promote {
                list.push_move(Move::make_promote(from, to, piece));
                continue;
            }

            let can_promote = can_promote(from, to, us);
            if can_promote {
                list.push_move(Move::make_promote(from, to, piece));
            }
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 銀の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_silver_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::SILVER_ATTACKS;
    use crate::types::Rank;

    let bb = pos.bitboards();
    let mut silvers = bb.pieces_of(PieceType::SILVER, us);
    let enemy_territory = match us {
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
    };

    while let Some(from) = silvers.pop_lsb() {
        let attacks = SILVER_ATTACKS[from.to_index()][us.to_index()];
        let destinations = attacks.and(target);
        let piece = pos.piece_on(from);

        if enemy_territory.test(from) {
            let mut squares = destinations;
            while let Some(to) = squares.pop_lsb() {
                list.push_move(Move::make_promote(from, to, piece));
                list.push_move(Move::make(from, to, piece));
            }
            continue;
        }

        let mut promotions = destinations.and(enemy_territory);
        while let Some(to) = promotions.pop_lsb() {
            list.push_move(Move::make_promote(from, to, piece));
            list.push_move(Move::make(from, to, piece));
        }

        let mut non_promotions = destinations.and_not(enemy_territory);
        while let Some(to) = non_promotions.pop_lsb() {
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 金相当 + 馬/龍 + 玉の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_gold_hdk_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    occupied: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::{bishop_attacks, rook_attacks, GOLD_ATTACKS, KING_ATTACKS};

    let bb = pos.bitboards();
    let mut movers = bb.pieces_of(PieceType::GOLD, us)
        | bb.pieces_of(PieceType::PRO_PAWN, us)
        | bb.pieces_of(PieceType::PRO_LANCE, us)
        | bb.pieces_of(PieceType::PRO_KNIGHT, us)
        | bb.pieces_of(PieceType::PRO_SILVER, us)
        | bb.pieces_of(PieceType::HORSE, us)
        | bb.pieces_of(PieceType::DRAGON, us)
        | bb.pieces_of(PieceType::KING, us);

    while let Some(from) = movers.pop_lsb() {
        let piece = pos.piece_on(from);
        let attacks = match piece.piece_type() {
            PieceType::GOLD
            | PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER => GOLD_ATTACKS[from.to_index()][us.to_index()],
            PieceType::KING => KING_ATTACKS[from.to_index()],
            PieceType::HORSE => {
                let bishop_moves = bishop_attacks(from, occupied);
                let king_moves = KING_ATTACKS[from.to_index()];
                bishop_moves.or(king_moves.and_not(bishop_moves))
            }
            PieceType::DRAGON => {
                let rook_moves = rook_attacks(from, occupied);
                let king_moves = KING_ATTACKS[from.to_index()];
                rook_moves.or(king_moves.and_not(rook_moves))
            }
            _ => continue,
        };
        let mut destinations = attacks.and(target);

        while let Some(to) = destinations.pop_lsb() {
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 金相当 + 馬/龍の移動手を生成（玉は除外）
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_gold_hd_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    occupied: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::{bishop_attacks, rook_attacks, GOLD_ATTACKS, KING_ATTACKS};

    let bb = pos.bitboards();
    let mut movers = bb.pieces_of(PieceType::GOLD, us)
        | bb.pieces_of(PieceType::PRO_PAWN, us)
        | bb.pieces_of(PieceType::PRO_LANCE, us)
        | bb.pieces_of(PieceType::PRO_KNIGHT, us)
        | bb.pieces_of(PieceType::PRO_SILVER, us)
        | bb.pieces_of(PieceType::HORSE, us)
        | bb.pieces_of(PieceType::DRAGON, us);

    while let Some(from) = movers.pop_lsb() {
        let piece = pos.piece_on(from);
        let attacks = match piece.piece_type() {
            PieceType::GOLD
            | PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER => GOLD_ATTACKS[from.to_index()][us.to_index()],
            PieceType::HORSE => {
                let bishop_moves = bishop_attacks(from, occupied);
                let king_moves = KING_ATTACKS[from.to_index()];
                bishop_moves.or(king_moves.and_not(bishop_moves))
            }
            PieceType::DRAGON => {
                let rook_moves = rook_attacks(from, occupied);
                let king_moves = KING_ATTACKS[from.to_index()];
                rook_moves.or(king_moves.and_not(rook_moves))
            }
            _ => continue,
        };
        let mut destinations = attacks.and(target);

        while let Some(to) = destinations.pop_lsb() {
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 香車の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_lance_moves<T: MoveGenType>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    occupied: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::lance_attacks;
    use crate::types::Rank;

    let bb = pos.bitboards();
    let mut lances = bb.pieces_of(PieceType::LANCE, us);
    let allow_underpromote = T::generate_all_legal();
    let enemy_territory = match us {
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
    };
    let non_promote_mask = if allow_underpromote {
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

    while let Some(from) = lances.pop_lsb() {
        let attacks = lance_attacks(from, occupied, us);
        let destinations = attacks.and(target);
        let piece = pos.piece_on(from);

        let mut promotions = destinations.and(enemy_territory);
        while let Some(to) = promotions.pop_lsb() {
            list.push_move(Move::make_promote(from, to, piece));
        }

        let mut non_promotions = destinations.and(non_promote_mask);
        while let Some(to) = non_promotions.pop_lsb() {
            if must_promote(piece.piece_type(), to, us) {
                continue;
            }
            list.push_move(Move::make(from, to, piece));
        }
    }
}

/// 角・飛車の移動手を生成
#[allow(clippy::extra_unused_type_parameters)]
pub(super) fn generate_br_moves<T: MoveGenType + 'static>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
    occupied: Bitboard,
    us: Color,
) {
    use crate::board::attack_tables::{bishop_attacks, rook_attacks};
    use crate::types::Rank;

    let bb = pos.bitboards();
    let mut movers = bb.pieces_of(PieceType::BISHOP, us) | bb.pieces_of(PieceType::ROOK, us);
    let allow_underpromote = T::generate_all_legal();
    let enemy_territory = match us {
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
    };

    while let Some(from) = movers.pop_lsb() {
        let piece = pos.piece_on(from);
        let attacks = match piece.piece_type() {
            PieceType::BISHOP => bishop_attacks(from, occupied),
            PieceType::ROOK => rook_attacks(from, occupied),
            _ => continue,
        };
        let my_target = target;

        let destinations = attacks.and(my_target);
        let from_in_enemy = enemy_territory.test(from);

        if from_in_enemy {
            let mut squares = destinations;
            while let Some(to) = squares.pop_lsb() {
                list.push_move(Move::make_promote(from, to, piece));
                if allow_underpromote {
                    list.push_move(Move::make(from, to, piece));
                }
            }
            continue;
        }

        let mut promotions = destinations.and(enemy_territory);
        while let Some(to) = promotions.pop_lsb() {
            list.push_move(Move::make_promote(from, to, piece));
            if allow_underpromote {
                list.push_move(Move::make(from, to, piece));
            }
        }

        let mut non_promotions = destinations.and_not(enemy_territory);
        while let Some(to) = non_promotions.pop_lsb() {
            list.push_move(Move::make(from, to, piece));
        }
    }
}
