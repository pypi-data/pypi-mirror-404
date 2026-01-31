//! ビットボード実装（81マス将棋盤用）
#![allow(unsafe_code)]

#[cfg(not(all(
    target_arch = "x86_64",
    target_feature = "sse2",
    target_feature = "sse4.1",
    target_feature = "ssse3"
)))]
use crate::simd::u64x2_ops;
use crate::types::{File, Rank, Square};

use std::convert::TryFrom;
use std::fmt;
use std::ops::{BitAnd, BitOr, BitXor, Not};

#[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
use std::arch::x86_64::{
    __m128i, _mm_add_epi64, _mm_and_si128, _mm_andnot_si128, _mm_cmpeq_epi64, _mm_or_si128,
    _mm_set1_epi64x, _mm_setzero_si128, _mm_unpackhi_epi64, _mm_unpacklo_epi64, _mm_xor_si128,
};

#[cfg(all(
    target_arch = "x86_64",
    target_feature = "sse2",
    not(all(target_feature = "sse4.1", target_feature = "ssse3"))
))]
use std::arch::x86_64::{_mm_set_epi64x, _mm_slli_si128, _mm_srli_epi64, _mm_sub_epi64};

#[cfg(all(target_arch = "x86_64", target_feature = "ssse3"))]
use std::arch::x86_64::{_mm_alignr_epi8, _mm_setr_epi8, _mm_shuffle_epi8};

#[cfg(all(target_arch = "x86_64", target_feature = "sse4.1"))]
use std::arch::x86_64::_mm_testz_si128;

const BOARD_MASK_LOW: u64 = 0x7FFF_FFFF_FFFF_FFFF;
const BOARD_MASK_HIGH: u64 = 0x0000_0000_0003_FFFF;

#[inline]
#[allow(dead_code)]
const fn raw_from_parts(parts: (u64, u64)) -> u128 {
    (parts.0 as u128) | ((parts.1 as u128) << 64)
}

/// 81マス将棋盤のビット表現
///
/// 下位81ビットを使用し、各ビットが1つのマスに対応する。
/// `SQ_11`（0）が最下位ビット、`SQ_99`（80）がbit80となる。
#[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
#[derive(Copy, Clone)]
#[repr(C, align(16))]
union BitboardRepr {
    p: [u64; 2],
    m: __m128i,
}

#[derive(Copy, Clone)]
#[repr(C, align(16))]
pub struct Bitboard {
    #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
    repr: BitboardRepr,
    #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
    p: [u64; 2],
}

impl Default for Bitboard {
    fn default() -> Self {
        Self::EMPTY
    }
}

impl PartialEq for Bitboard {
    fn eq(&self, other: &Self) -> bool {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse4.1"))]
        {
            let neq = unsafe { _mm_xor_si128(self.as_m128(), other.as_m128()) };
            unsafe { _mm_testz_si128(neq, neq) != 0 }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse4.1")))]
        {
            let [a0, a1] = self.parts();
            let [b0, b1] = other.parts();
            a0 == b0 && a1 == b1
        }
    }
}

impl Eq for Bitboard {}

impl Bitboard {
    /// 空のビットボード
    pub const EMPTY: Self = {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [0, 0] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [0, 0] }
        }
    };

    /// 全マスが立っているビットボード（81マス分）
    pub const ALL: Self = {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [BOARD_MASK_LOW, BOARD_MASK_HIGH] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [BOARD_MASK_LOW, BOARD_MASK_HIGH] }
        }
    };

    /// Packed u128 (0..80) からBitboardを生成
    #[inline]
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub const fn from_packed_bits(packed_bits: u128) -> Self {
        let packed = packed_bits & ((1u128 << 81) - 1);
        let low = (packed & BOARD_MASK_LOW as u128) as u64;
        let high = ((packed >> 63) & BOARD_MASK_HIGH as u128) as u64;
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [low, high] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [low, high] }
        }
    }

    #[inline]
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub(crate) const fn from_packed_bits_unchecked(packed_bits: u128) -> Self {
        let low = packed_bits as u64;
        let high = (packed_bits >> 64) as u64;
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [low, high] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [low, high] }
        }
    }

    /// 単一のマスからビットボードを作成
    #[inline]
    #[must_use]
    pub fn from_square(sq: Square) -> Self {
        debug_assert!(sq.is_ok(), "Invalid square: {sq:?}");
        debug_assert!(!sq.is_none(), "Invalid square: {sq:?}");
        let idx = sq.0;
        if idx < 63 {
            let shift = u32::try_from(idx).expect("square index fits in u32");
            #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
            {
                Self { repr: BitboardRepr { p: [1u64 << shift, 0] } }
            }
            #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
            {
                Self { p: [1u64 << shift, 0] }
            }
        } else {
            let shift = u32::try_from(idx - 63).expect("square index fits in u32");
            #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
            {
                Self { repr: BitboardRepr { p: [0, 1u64 << shift] } }
            }
            #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
            {
                Self { p: [0, 1u64 << shift] }
            }
        }
    }

    /// 内部のビット表現を取得
    #[inline]
    #[must_use]
    pub const fn packed_bits(&self) -> u128 {
        let parts = self.parts();
        (parts[0] as u128) | ((parts[1] as u128) << 63)
    }

    #[inline]
    #[must_use]
    #[allow(dead_code)]
    pub(crate) const fn raw_bits(&self) -> u128 {
        let parts = self.parts();
        (parts[0] as u128) | ((parts[1] as u128) << 64)
    }

    #[inline]
    #[must_use]
    pub const fn parts(&self) -> [u64; 2] {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        unsafe {
            self.repr.p
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            self.p
        }
    }

    /// 内部の2x u64表現からBitboardを生成
    #[inline]
    #[must_use]
    pub const fn from_parts(parts: [u64; 2]) -> Self {
        let low = parts[0] & BOARD_MASK_LOW;
        let high = parts[1] & BOARD_MASK_HIGH;
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [low, high] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [low, high] }
        }
    }

    #[inline]
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    #[allow(dead_code)]
    pub(crate) const fn from_raw_bits_unmasked(raw: u128) -> Self {
        let low = raw as u64;
        let high = (raw >> 64) as u64;
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: [low, high] } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: [low, high] }
        }
    }

    #[inline]
    fn parts_mut(&mut self) -> &mut [u64; 2] {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        unsafe {
            &mut self.repr.p
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            &mut self.p
        }
    }

    #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
    #[inline]
    #[allow(clippy::missing_const_for_fn)]
    pub(crate) fn as_m128(self) -> __m128i {
        unsafe { self.repr.m }
    }

    #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
    #[inline]
    #[allow(clippy::missing_const_for_fn)]
    pub(crate) fn from_m128(value: __m128i) -> Self {
        Self { repr: BitboardRepr { m: value } }
    }

    /// 指定マスのビットを立てる
    #[inline]
    pub fn set(&mut self, sq: Square) {
        debug_assert!(sq.is_ok(), "Invalid square: {sq:?}");
        debug_assert!(!sq.is_none(), "Invalid square: {sq:?}");
        let idx = sq.0;
        if idx < 63 {
            let shift = u32::try_from(idx).expect("square index fits in u32");
            let parts = self.parts_mut();
            parts[0] |= 1u64 << shift;
        } else {
            let shift = u32::try_from(idx - 63).expect("square index fits in u32");
            let parts = self.parts_mut();
            parts[1] |= 1u64 << shift;
        }
    }

    /// 指定マスのビットをクリア
    #[inline]
    pub fn clear(&mut self, sq: Square) {
        debug_assert!(sq.is_ok(), "Invalid square: {sq:?}");
        debug_assert!(!sq.is_none(), "Invalid square: {sq:?}");
        let idx = sq.0;
        if idx < 63 {
            let shift = u32::try_from(idx).expect("square index fits in u32");
            let parts = self.parts_mut();
            parts[0] &= !(1u64 << shift);
        } else {
            let shift = u32::try_from(idx - 63).expect("square index fits in u32");
            let parts = self.parts_mut();
            parts[1] &= !(1u64 << shift);
        }
    }

    /// 指定マスのビットが立っているか判定
    #[inline]
    #[must_use]
    pub fn test(&self, sq: Square) -> bool {
        debug_assert!(sq.is_ok(), "Invalid square: {sq:?}");
        debug_assert!(!sq.is_none(), "Invalid square: {sq:?}");
        let idx = sq.0;
        if idx < 63 {
            let shift = u32::try_from(idx).expect("square index fits in u32");
            let parts = self.parts();
            (parts[0] & (1u64 << shift)) != 0
        } else {
            let shift = u32::try_from(idx - 63).expect("square index fits in u32");
            let parts = self.parts();
            (parts[1] & (1u64 << shift)) != 0
        }
    }

    /// 最下位の立っているビットを取り出してクリア
    #[inline]
    pub fn pop_lsb(&mut self) -> Option<Square> {
        let parts = self.parts_mut();
        if parts[0] == 0 && parts[1] == 0 {
            return None;
        }
        if parts[0] != 0 {
            let lsb = parts[0].trailing_zeros();
            parts[0] &= parts[0] - 1;
            let idx = i8::try_from(lsb).expect("bit index within board bounds");
            Some(Square(idx))
        } else {
            let lsb = parts[1].trailing_zeros();
            parts[1] &= parts[1] - 1;
            let idx = i8::try_from(63 + lsb).expect("bit index within board bounds");
            Some(Square(idx))
        }
    }

    /// 最下位ビット（LSB）の位置を取得（破壊的でない）
    #[inline]
    #[must_use]
    pub fn lsb(&self) -> Option<Square> {
        let parts = self.parts();
        if parts[0] == 0 && parts[1] == 0 {
            return None;
        }
        if parts[0] != 0 {
            let lsb = parts[0].trailing_zeros();
            let idx = i8::try_from(lsb).expect("bit index within board bounds");
            Some(Square(idx))
        } else {
            let lsb = parts[1].trailing_zeros();
            let idx = i8::try_from(63 + lsb).expect("bit index within board bounds");
            Some(Square(idx))
        }
    }

    /// 最上位ビット（MSB）の位置を取得
    #[inline]
    #[must_use]
    pub fn msb(&self) -> Option<Square> {
        let parts = self.parts();
        if parts[0] == 0 && parts[1] == 0 {
            return None;
        }
        if parts[1] != 0 {
            let msb = 63 - parts[1].leading_zeros();
            let idx = i8::try_from(63 + msb).expect("bit index within board bounds");
            Some(Square(idx))
        } else {
            let msb = 63 - parts[0].leading_zeros();
            let idx = i8::try_from(msb).expect("bit index within board bounds");
            Some(Square(idx))
        }
    }

    /// 立っているビットの数を数える
    #[inline]
    #[must_use]
    pub const fn count(&self) -> u32 {
        let parts = self.parts();
        parts[0].count_ones() + parts[1].count_ones()
    }

    /// ビットごとのAND演算
    #[inline]
    #[must_use]
    pub fn and(&self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_and_si128((*self).as_m128(), other.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::and(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    /// ビットごとのOR演算
    #[inline]
    #[must_use]
    pub fn or(&self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_or_si128((*self).as_m128(), other.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::or(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    /// ビットごとのXOR演算
    #[inline]
    #[must_use]
    pub fn xor(&self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_xor_si128((*self).as_m128(), other.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::xor(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    /// 指定した筋のビットボードを作成
    #[must_use]
    pub fn file_mask(file: File) -> Self {
        let mut mask = Self::EMPTY;
        for rank_idx in 0..9 {
            let sq = Square::from_file_rank(file, Rank::new(rank_idx));
            if sq.is_ok() {
                mask.set(sq);
            }
        }
        mask
    }

    /// 指定した段のビットボードを作成
    #[must_use]
    pub fn rank_mask(rank: Rank) -> Self {
        let mut mask = Self::EMPTY;
        for file_idx in 0..9 {
            let sq = Square::from_file_rank(File::new(file_idx), rank);
            if sq.is_ok() {
                mask.set(sq);
            }
        }
        mask
    }

    /// ビット反転（81マスの範囲内）
    #[inline]
    #[must_use]
    pub const fn not(&self) -> Self {
        let parts = self.parts();
        let masked = [(!parts[0]) & BOARD_MASK_LOW, (!parts[1]) & BOARD_MASK_HIGH];
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: masked } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: masked }
        }
    }

    /// 盤面を180度回転させたBitboardを返す。
    #[must_use]
    pub fn flip(&self) -> Self {
        let mut out = Self::EMPTY;
        for sq in 0..81 {
            let square = Square(sq);
            if self.test(square) {
                let flipped = Square(80 - sq);
                out.set(flipped);
            }
        }
        out
    }

    /// 盤面を左右反転させたBitboardを返す。
    #[must_use]
    pub fn mirror(&self) -> Self {
        let mut out = Self::EMPTY;
        for sq in 0..81 {
            let square = Square(sq);
            if self.test(square) {
                let file = sq / 9;
                let rank = sq % 9;
                let flipped_file = 8 - file;
                out.set(Square(flipped_file * 9 + rank));
            }
        }
        out
    }

    /// 盤面を180度回転させたBitboardを返す（`flip` の別名）。
    #[must_use]
    pub fn rotate(&self) -> Self {
        self.flip()
    }

    /// AND NOT演算（self & !other）
    ///
    /// YaneuraOuの`andnot`は `!self & other` を指すため注意すること。
    #[inline]
    #[must_use]
    pub fn and_not(&self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_andnot_si128(other.as_m128(), (*self).as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::and_not(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    #[inline]
    #[must_use]
    pub(crate) fn and_raw(self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_and_si128(self.as_m128(), other.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::and(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    #[inline]
    #[must_use]
    pub(crate) fn xor_raw(self, other: Self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_xor_si128(self.as_m128(), other.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::xor(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }

    /// 他のBitboardと交差しているか判定する。
    #[inline]
    #[must_use]
    pub fn intersects(&self, other: Self) -> bool {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse4.1"))]
        {
            unsafe { _mm_testz_si128((*self).as_m128(), other.as_m128()) == 0 }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse4.1")))]
        {
            !u64x2_ops::testz(
                (self.parts()[0], self.parts()[1]),
                (other.parts()[0], other.parts()[1]),
            )
        }
    }

    /// byte単位で入れ替えたBitboardを返す。
    #[inline]
    #[must_use]
    pub fn byte_reverse(&self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "ssse3"))]
        {
            let shuffle =
                unsafe { _mm_setr_epi8(15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0) };
            let value = unsafe { _mm_shuffle_epi8(self.as_m128(), shuffle) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "ssse3")))]
        {
            let parts = self.parts();
            let (p0, p1) = u64x2_ops::byte_reverse(parts[0], parts[1]);
            let parts: [u64; 2] = (p0, p1).into();
            #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
            {
                Self { repr: BitboardRepr { p: parts } }
            }
            #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
            {
                Self { p: parts }
            }
        }
    }

    /// SSE2のunpackを実行した結果を返す。
    #[inline]
    #[must_use]
    pub fn unpack(hi_in: Self, lo_in: Self) -> (Self, Self) {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let hi = unsafe { _mm_unpackhi_epi64(lo_in.as_m128(), hi_in.as_m128()) };
            let lo = unsafe { _mm_unpacklo_epi64(lo_in.as_m128(), hi_in.as_m128()) };
            (Self::from_m128(hi), Self::from_m128(lo))
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let (hi, lo) = u64x2_ops::unpack(
                (hi_in.parts()[0], hi_in.parts()[1]),
                (lo_in.parts()[0], lo_in.parts()[1]),
            );
            (
                Self::from_raw_bits_unmasked(raw_from_parts(hi)),
                Self::from_raw_bits_unmasked(raw_from_parts(lo)),
            )
        }
    }

    /// 2組のBitboardを128bit整数とみなして1減算した結果を返す。
    #[inline]
    #[must_use]
    pub fn decrement_pair(hi_in: Self, lo_in: Self) -> (Self, Self) {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let hi = hi_in.as_m128();
            let lo = lo_in.as_m128();
            let borrow = unsafe { _mm_cmpeq_epi64(lo, _mm_setzero_si128()) };
            let hi_out = unsafe { _mm_add_epi64(hi, borrow) };
            let lo_out = unsafe { _mm_add_epi64(lo, _mm_set1_epi64x(-1)) };
            (Self::from_m128(hi_out), Self::from_m128(lo_out))
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let (hi, lo) = u64x2_ops::decrement_pair(
                (hi_in.parts()[0], hi_in.parts()[1]),
                (lo_in.parts()[0], lo_in.parts()[1]),
            );
            (
                Self::from_raw_bits_unmasked(raw_from_parts(hi)),
                Self::from_raw_bits_unmasked(raw_from_parts(lo)),
            )
        }
    }

    /// このBitboardを128bit整数とみなして1減算したBitboardを返す。
    #[inline]
    #[must_use]
    #[allow(clippy::missing_const_for_fn)]
    pub fn decrement(&self) -> Self {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse4.1", target_feature = "ssse3"))]
        {
            let t2 = unsafe { _mm_cmpeq_epi64(self.as_m128(), _mm_setzero_si128()) };
            let t2 = unsafe { _mm_alignr_epi8(t2, _mm_set1_epi64x(-1), 8) };
            let t1 = unsafe { _mm_add_epi64(self.as_m128(), t2) };
            Self::from_m128(t1)
        }
        #[cfg(all(
            target_arch = "x86_64",
            target_feature = "sse2",
            not(all(target_feature = "sse4.1", target_feature = "ssse3"))
        ))]
        {
            let c = unsafe { _mm_set_epi64x(0, 1) };
            let mut t1 = unsafe { _mm_sub_epi64(self.as_m128(), c) };
            let t2 = unsafe { _mm_srli_epi64(t1, 63) };
            let t2 = unsafe { _mm_slli_si128(t2, 8) };
            t1 = unsafe { _mm_sub_epi64(t1, t2) };
            Self::from_m128(t1)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let raw = self.raw_bits().wrapping_sub(1);
            Self::from_raw_bits_unmasked(raw)
        }
    }

    /// 2bit以上あるかどうかを判定する。
    #[inline]
    #[must_use]
    pub const fn more_than_one(&self) -> bool {
        let parts = self.parts();
        if parts[0] & (parts[0].wrapping_sub(1)) != 0 {
            return true;
        }
        if parts[1] & (parts[1].wrapping_sub(1)) != 0 {
            return true;
        }
        parts[0] != 0 && parts[1] != 0
    }

    /// 空かどうか判定
    #[inline]
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        let parts = self.parts();
        parts[0] == 0 && parts[1] == 0
    }

    /// 何かビットが立っているか判定
    #[inline]
    #[must_use]
    pub const fn any(&self) -> bool {
        let parts = self.parts();
        parts[0] != 0 || parts[1] != 0
    }

    /// イテレータを返す
    #[must_use]
    pub const fn iter(&self) -> BitIter {
        BitIter { bb: *self }
    }
}

impl IntoIterator for &Bitboard {
    type Item = Square;
    type IntoIter = BitIter;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

/// Bitboard上の立っているビットを列挙するイテレータ
pub struct BitIter {
    bb: Bitboard,
}

impl Iterator for BitIter {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        self.bb.pop_lsb()
    }
}

impl fmt::Debug for Bitboard {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "Bitboard(")?;
        for rank in (0..9).rev() {
            write!(f, "  ")?;
            for file in (0..9).rev() {
                let sq = Square::from_file_rank(File(file), Rank(rank));
                if self.test(sq) {
                    write!(f, "1")?;
                } else {
                    write!(f, "0")?;
                }
            }
            writeln!(f)?;
        }
        write!(f, ")")
    }
}

impl BitAnd for Bitboard {
    type Output = Self;

    #[inline]
    fn bitand(self, rhs: Self) -> Self::Output {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_and_si128(self.as_m128(), rhs.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::and(
                (self.parts()[0], self.parts()[1]),
                (rhs.parts()[0], rhs.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }
}

impl BitOr for Bitboard {
    type Output = Self;

    #[inline]
    fn bitor(self, rhs: Self) -> Self::Output {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_or_si128(self.as_m128(), rhs.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts =
                u64x2_ops::or((self.parts()[0], self.parts()[1]), (rhs.parts()[0], rhs.parts()[1]));
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }
}

impl BitXor for Bitboard {
    type Output = Self;

    #[inline]
    fn bitxor(self, rhs: Self) -> Self::Output {
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            let value = unsafe { _mm_xor_si128(self.as_m128(), rhs.as_m128()) };
            Self::from_m128(value)
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            let parts = u64x2_ops::xor(
                (self.parts()[0], self.parts()[1]),
                (rhs.parts()[0], rhs.parts()[1]),
            );
            Self::from_raw_bits_unmasked(raw_from_parts(parts))
        }
    }
}

impl Not for Bitboard {
    type Output = Self;

    #[inline]
    fn not(self) -> Self::Output {
        // 81ビットマスクを適用して、使用しないビットをクリア
        let parts = self.parts();
        let masked = [(!parts[0]) & BOARD_MASK_LOW, (!parts[1]) & BOARD_MASK_HIGH];
        #[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]
        {
            Self { repr: BitboardRepr { p: masked } }
        }
        #[cfg(not(all(target_arch = "x86_64", target_feature = "sse2")))]
        {
            Self { p: masked }
        }
    }
}

impl fmt::Display for Bitboard {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self:?}")
    }
}

#[cfg(test)]
mod tests;
