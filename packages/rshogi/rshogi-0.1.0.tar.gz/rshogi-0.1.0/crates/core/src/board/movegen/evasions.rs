use crate::board::Position;
use crate::types::{Color, Move, PieceType};

use super::drops::generate_drops_for_target_color;
use super::pieces::{
    generate_br_moves, generate_gold_hd_moves, generate_knight_moves, generate_lance_moves,
    generate_pawn_moves, generate_silver_moves,
};
use super::types::{Evasions, MoveGenType};
use super::{Black, ColorMarker, MoveSink, White};

/// 王手回避手を生成
///
/// 現在王手がかかっている局面で、王手を回避する手を生成します。
///
/// # Arguments
/// * `pos` - 現在の局面（王手がかかっている状態）
/// * `list` - 生成した手を格納するリスト
///
/// # 生成される手
/// - 両王手の場合: 玉の移動手のみ
/// - 単王手の場合: 玉の移動手 + 王手駒を取る手 + 合駒
pub fn generate_evasions(pos: &Position, list: &mut impl MoveSink) {
    generate_evasions_for::<Evasions>(pos, list);
}

#[inline]
pub fn generate_evasions_for<T: MoveGenType + 'static>(pos: &Position, list: &mut impl MoveSink) {
    match pos.side_to_move() {
        Color::BLACK => generate_evasions_for_color::<T, Black>(pos, list),
        Color::WHITE => generate_evasions_for_color::<T, White>(pos, list),
        _ => {}
    }
}

pub fn generate_evasions_for_color<T: MoveGenType + 'static, C: ColorMarker>(
    pos: &Position,
    list: &mut impl MoveSink,
) {
    use crate::board::attack_tables::{
        bishop_attacks, lance_attacks, rook_attacks, GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS,
        PAWN_ATTACKS, SILVER_ATTACKS,
    };

    let us = C::COLOR;
    let checkers = pos.checkers();
    if checkers.is_empty() {
        return;
    }

    let king_sq = pos.bitboards().pieces_of(PieceType::KING, us).lsb().unwrap();
    let occupied = pos.bitboards().occupied();
    let occupied_without_king = occupied.and_not(crate::board::Bitboard::from_square(king_sq));
    let mut slider_attacks = crate::board::Bitboard::EMPTY;
    let mut checkers_cnt = 0;
    let mut checkers_bb = checkers;
    while let Some(check_sq) = checkers_bb.pop_lsb() {
        checkers_cnt += 1;
        let piece = pos.piece_on(check_sq);
        let color = piece.color();
        let attacks = match piece.piece_type() {
            PieceType::PAWN => PAWN_ATTACKS[check_sq.to_index()][color.to_index()],
            PieceType::LANCE => lance_attacks(check_sq, occupied_without_king, color),
            PieceType::KNIGHT => KNIGHT_ATTACKS[check_sq.to_index()][color.to_index()],
            PieceType::SILVER => SILVER_ATTACKS[check_sq.to_index()][color.to_index()],
            PieceType::GOLD
            | PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER => GOLD_ATTACKS[check_sq.to_index()][color.to_index()],
            PieceType::KING => KING_ATTACKS[check_sq.to_index()],
            PieceType::BISHOP => bishop_attacks(check_sq, occupied_without_king),
            PieceType::ROOK => rook_attacks(check_sq, occupied_without_king),
            PieceType::HORSE => {
                bishop_attacks(check_sq, occupied_without_king) | KING_ATTACKS[check_sq.to_index()]
            }
            PieceType::DRAGON => {
                rook_attacks(check_sq, occupied_without_king) | KING_ATTACKS[check_sq.to_index()]
            }
            _ => crate::board::Bitboard::EMPTY,
        };
        slider_attacks = slider_attacks.or(attacks);
    }

    let king_piece = pos.piece_on(king_sq);
    let our_pieces = pos.bitboards().color_pieces(us);
    let mut king_targets = KING_ATTACKS[king_sq.to_index()].and_not(our_pieces | slider_attacks);
    while let Some(to) = king_targets.pop_lsb() {
        list.push_move(Move::make(king_sq, to, king_piece));
    }

    if checkers_cnt > 1 {
        return;
    }

    let checker_sq = checkers.lsb().unwrap();
    let target1 = crate::board::Bitboard::between(king_sq, checker_sq);
    let target2 = target1.or(crate::board::Bitboard::from_square(checker_sq));

    generate_pawn_moves::<T>(pos, list, target2, us);
    generate_lance_moves::<T>(pos, list, target2, occupied, us);
    generate_knight_moves::<T>(pos, list, target2, us);
    generate_silver_moves::<T>(pos, list, target2, us);
    generate_br_moves::<T>(pos, list, target2, occupied, us);
    generate_gold_hd_moves::<T>(pos, list, target2, occupied, us);
    generate_drops_for_target_color::<T, C>(pos, list, target1);
}
