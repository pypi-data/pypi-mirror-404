//! 攻撃テーブル - ビルド時に生成されたテーブルを公開

// ビルド時に生成されたテーブルをインクルード
#[allow(clippy::unreadable_literal)]
mod generated {
    include!(concat!(env!("OUT_DIR"), "/attack_tables.rs"));
}

pub use generated::{
    BishopBeams, LanceBeams, RookBeams, BISHOP_BEAMS, CHECK_CANDIDATE_BB, GOLD_ATTACKS,
    KING_ATTACKS, KNIGHT_ATTACKS, LANCE_BEAMS, PAWN_ATTACKS, QUGIY_BISHOP_MASK, QUGIY_ROOK_MASK,
    QUGIY_STEP_EFFECT, ROOK_BEAMS, SILVER_ATTACKS,
};

use crate::board::{Bitboard, Bitboard256};
use crate::types::{Color, Square};

/// 香車の攻撃範囲を計算（Qugiy方式の差分抽出）
#[inline]
#[must_use]
pub fn lance_attacks(sq: Square, occupied: Bitboard, color: Color) -> Bitboard {
    let beams = LANCE_BEAMS[sq.to_index()];
    let part = usize::from(sq.to_index() >= 63);
    let [occ0, occ1] = occupied.parts();

    match color {
        Color::WHITE => {
            let mask = beams.white;
            let [mask0, mask1] = mask.parts();
            let (em, mask_part) =
                if part == 0 { (occ0 & mask0, mask0) } else { (occ1 & mask1, mask1) };
            let t = em.wrapping_sub(1);
            let result = (em ^ t) & mask_part;
            if part == 0 {
                Bitboard::from_parts([result, 0])
            } else {
                Bitboard::from_parts([0, result])
            }
        }
        Color::BLACK => {
            let mask = beams.black;
            let [mask0, mask1] = mask.parts();
            let (mocc, mask_part) =
                if part == 0 { (occ0 & mask0, mask0) } else { (occ1 & mask1, mask1) };
            let msb = 63 - (mocc | 1).leading_zeros();
            let fill = (!0u64) << msb;
            let result = fill & mask_part;
            if part == 0 {
                Bitboard::from_parts([result, 0])
            } else {
                Bitboard::from_parts([0, result])
            }
        }
        _ => Bitboard::EMPTY,
    }
}

/// 角の攻撃範囲を計算（4方向のビームと占有から計算）
#[inline]
#[must_use]
#[allow(clippy::similar_names)]
pub fn bishop_attacks(sq: Square, occupied: Bitboard) -> Bitboard {
    let mask_lo = QUGIY_BISHOP_MASK[sq.to_index()][0];
    let mask_hi = QUGIY_BISHOP_MASK[sq.to_index()][1];

    let occ2 = Bitboard256::splat(occupied);
    let rocc2 = Bitboard256::splat(occupied.byte_reverse());
    let (hi, lo) = Bitboard256::unpack(rocc2, occ2);

    let hi = hi.and(mask_hi);
    let lo = lo.and(mask_lo);
    let (t1, t0) = Bitboard256::decrement(hi, lo);
    let t1 = t1.xor(hi).and(mask_hi);
    let t0 = t0.xor(lo).and(mask_lo);
    let (hi, lo) = Bitboard256::unpack(t1, t0);
    hi.byte_reverse().or(lo).merge()
}

/// 飛車の攻撃範囲を計算（4方向のビームと占有から計算）
#[inline]
#[must_use]
pub fn rook_attacks(sq: Square, occupied: Bitboard) -> Bitboard {
    let mut attacks = Bitboard::EMPTY;
    attacks = attacks | lance_attacks(sq, occupied, Color::BLACK);
    attacks = attacks | lance_attacks(sq, occupied, Color::WHITE);

    let mask_lo = QUGIY_ROOK_MASK[sq.to_index()][0];
    let mask_hi = QUGIY_ROOK_MASK[sq.to_index()][1];
    let occ_rev = occupied.byte_reverse();
    let (hi, lo) = Bitboard::unpack(occ_rev, occupied);
    let hi = hi.and_raw(mask_hi);
    let lo = lo.and_raw(mask_lo);
    let (t1, t0) = Bitboard::decrement_pair(hi, lo);
    let t1 = t1.xor_raw(hi).and_raw(mask_hi);
    let t0 = t0.xor_raw(lo).and_raw(mask_lo);
    let (hi, lo) = Bitboard::unpack(t1, t0);
    attacks | hi.byte_reverse() | lo
}

#[cfg(test)]
mod tests;
