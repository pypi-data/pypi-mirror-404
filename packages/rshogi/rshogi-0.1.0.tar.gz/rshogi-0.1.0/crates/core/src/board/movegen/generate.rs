use crate::board::Position;
use crate::types::{Color, Square};

use super::checks::generate_checks_for_color;
use super::drops::generate_drops_color;
use super::evasions::generate_evasions_for_color;
use super::pieces::{
    generate_br_moves, generate_gold_hdk_moves, generate_knight_moves, generate_lance_moves,
    generate_pawn_moves, generate_silver_moves,
};
use super::types::{Evasions, EvasionsAll, MoveGenType};
use super::{Black, ColorMarker, MoveSink, White};

/// 指し手を生成する（メインインターフェース）
///
/// # Pseudo-Legal手生成とYaneuraOu互換性
///
/// この関数は基本的に**pseudo-legal（擬似合法手）**を生成します。
/// これはYaneuraOuの設計方針に従ったものです。
///
/// - **生成段階**: ピン判定や自殺手の完全チェックは行わない。
/// - **検証段階**: 探索中に`Position::legal()`で遅延検証する。
///
/// ## 注意事項
///
/// 生成された手は以下を含む可能性があります。
/// - ピンされた駒の違法な移動。
/// - 自殺手（玉を取られる手）。
/// - 打ち歩詰め（王手になる歩打ちのみ `legal_drop()` 相当で除外）。
///
/// これらは探索中に`legal()`で検証されることを前提とします。
///
/// ## 将来の最適化（P13以降）
///
/// `blockers_for_king`を活用した高速パス実装により、
/// 明らかに合法な手は生成時に判定し、疑わしい手のみ遅延検証する予定です。
/// 詳細は implementation-diff-report.md セクション2.4参照です。
#[allow(clippy::too_many_lines)]
#[inline]
pub fn generate_moves<T: MoveGenType + 'static>(pos: &Position, list: &mut impl MoveSink) {
    match pos.side_to_move() {
        Color::BLACK => generate_moves_color::<T, Black>(pos, list),
        Color::WHITE => generate_moves_color::<T, White>(pos, list),
        _ => {}
    }
}

#[allow(clippy::too_many_lines)]
#[inline]
fn generate_moves_color<T: MoveGenType + 'static, C: ColorMarker>(
    pos: &Position,
    list: &mut impl MoveSink,
) {
    use crate::types::{Bitboard, Rank};
    let us = C::COLOR;
    let them = C::THEM;
    let bb = pos.bitboards();

    if T::IS_RECAPTURES {
        return;
    }

    let is_checks = T::IS_CHECKS;
    let is_legal = T::IS_LEGAL;

    if T::QUIET_CHECKS && !T::CAPTURES && !T::QUIETS {
        let all = T::generate_all_legal();
        generate_checks_for_color::<C>(pos, list, all, true);
        if !pos.checkers().is_empty() {
            list.retain_unordered(|m| pos.pseudo_legal(m, all));
        }
        return;
    }

    if is_checks {
        let all = T::generate_all_legal();
        generate_checks_for_color::<C>(pos, list, all, false);
        if !pos.checkers().is_empty() {
            list.retain_unordered(|m| pos.pseudo_legal(m, all));
        }
        return;
    }

    if T::EVASIONS {
        debug_assert!(T::CAPTURES && T::QUIETS, "EVASIONS must generate both captures and quiets.");
        generate_evasions_for_color::<T, C>(pos, list);
        if is_legal {
            list.retain_unordered(|m| pos.legal(m));
        }
        return;
    }

    if is_legal && !pos.checkers().is_empty() {
        if T::generate_all_legal() {
            generate_evasions_for_color::<EvasionsAll, C>(pos, list);
        } else {
            generate_evasions_for_color::<Evasions, C>(pos, list);
        }
        list.retain_unordered(|m| pos.legal(m));
        return;
    }

    // 自分の駒のBitboard
    let our_pieces = bb.color_pieces(us);
    // 相手の駒のBitboard
    let their_pieces = bb.color_pieces(them);
    // 全占有
    let occupied = bb.occupied();

    // DEBUG TRACE
    // println!("DEBUG: generate_moves called");

    // ターゲット: 移動可能なマス（空マスまたは相手の駒）
    let target = if T::CAPTURES && T::QUIETS {
        !our_pieces // 自分の駒以外
    } else if T::CAPTURES {
        their_pieces // 相手の駒のみ
    } else if T::QUIETS {
        !occupied // 空マスのみ
    } else {
        return; // 何も生成しない
    };
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
    let pawn_target = if T::IS_QUIETS_PRO_MINUS {
        (!occupied).and_not(enemy_territory)
    } else if T::IS_CAPTURE_PLUS_PRO {
        enemy_territory.and_not(our_pieces) | their_pieces
    } else {
        target
    };
    // 歩の移動生成
    generate_pawn_moves::<T>(pos, list, pawn_target, us);

    // 香車の移動生成（YaneuraOu互換: 歩の次に生成）
    generate_lance_moves::<T>(pos, list, target, occupied, us);

    // 桂馬の移動生成
    generate_knight_moves::<T>(pos, list, target, us);

    // 銀の移動生成
    generate_silver_moves::<T>(pos, list, target, us);

    // 角・飛車の移動生成（YaneuraOu: GPM_BR の順序）
    generate_br_moves::<T>(pos, list, target, occupied, us);

    // 金相当 + 馬/龍 + 玉の移動生成（YaneuraOu: GPM_GHDK の順序）
    generate_gold_hdk_moves::<T>(pos, list, target, occupied, us);

    // 打ち駒生成
    if T::QUIETS {
        generate_drops_color::<T, C>(pos, list);
    }

    if is_legal {
        list.retain_unordered(|m| pos.legal(m));
    }
}

/// 指定マスへの移動手（Recaptures）を生成する。
#[allow(clippy::too_many_lines)]
#[inline]
pub fn generate_moves_to<T: MoveGenType + 'static>(
    pos: &Position,
    target_sq: Square,
    list: &mut impl MoveSink,
) {
    match pos.side_to_move() {
        Color::BLACK => generate_moves_to_color::<T, Black>(pos, target_sq, list),
        Color::WHITE => generate_moves_to_color::<T, White>(pos, target_sq, list),
        _ => {}
    }
}

#[allow(clippy::too_many_lines)]
#[inline]
fn generate_moves_to_color<T: MoveGenType + 'static, C: ColorMarker>(
    pos: &Position,
    target_sq: Square,
    list: &mut impl MoveSink,
) {
    use crate::types::{Bitboard, Rank};

    debug_assert!(T::IS_RECAPTURES, "generate_moves_to is for Recaptures only");

    let us = C::COLOR;
    let bb = pos.bitboards();

    let is_legal = T::IS_LEGAL;

    if target_sq.is_none() {
        return;
    }

    // 全占有
    let occupied = bb.occupied();

    let target = Bitboard::from_square(target_sq);
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
    let pawn_target = if T::IS_QUIETS_PRO_MINUS {
        (!occupied).and_not(enemy_territory)
    } else if T::IS_CAPTURE_PLUS_PRO {
        enemy_territory.and_not(bb.color_pieces(us)) | bb.color_pieces(us.flip())
    } else {
        target
    };

    // 歩の移動生成
    generate_pawn_moves::<T>(pos, list, pawn_target, us);

    // 香車の移動生成（YaneuraOu互換: 歩の次に生成）
    generate_lance_moves::<T>(pos, list, target, occupied, us);

    // 桂馬の移動生成
    generate_knight_moves::<T>(pos, list, target, us);

    // 銀の移動生成
    generate_silver_moves::<T>(pos, list, target, us);

    // 角・飛車の移動生成（YaneuraOu: GPM_BR の順序）
    generate_br_moves::<T>(pos, list, target, occupied, us);

    // 金相当 + 馬/龍 + 玉の移動生成（YaneuraOu: GPM_GHDK の順序）
    generate_gold_hdk_moves::<T>(pos, list, target, occupied, us);

    if is_legal {
        list.retain_unordered(|m| pos.legal(m));
    }
}
