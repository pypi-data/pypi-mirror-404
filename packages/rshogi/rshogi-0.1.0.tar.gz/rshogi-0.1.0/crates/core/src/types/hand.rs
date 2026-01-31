//! 持ち駒の型定義

use super::PieceType;

/// 持ち駒の駒種
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct HandPiece(pub i8);

// 定数定義（YaneuraOu互換）
pub const HAND_BIT_MASK: u32 =
    0x1f | (0x7 << 8) | (0x7 << 12) | (0x7 << 16) | (0x3 << 20) | (0x3 << 24) | (0x7 << 28);
pub const HAND_BORROW_MASK: u32 = (HAND_BIT_MASK << 1) & !HAND_BIT_MASK;
impl HandPiece {
    // 持ち駒定数（歩から金まで）
    pub const HAND_PAWN: Self = Self(0);
    pub const HAND_LANCE: Self = Self(1);
    pub const HAND_KNIGHT: Self = Self(2);
    pub const HAND_SILVER: Self = Self(3);
    pub const HAND_BISHOP: Self = Self(4);
    pub const HAND_ROOK: Self = Self(5);
    pub const HAND_GOLD: Self = Self(6);
    pub const HAND_NB: usize = 7;

    /// `PieceType` から変換
    #[must_use]
    pub const fn from_piece_type(pt: PieceType) -> Option<Self> {
        match pt {
            PieceType::PAWN => Some(Self::HAND_PAWN),
            PieceType::LANCE => Some(Self::HAND_LANCE),
            PieceType::KNIGHT => Some(Self::HAND_KNIGHT),
            PieceType::SILVER => Some(Self::HAND_SILVER),
            PieceType::BISHOP => Some(Self::HAND_BISHOP),
            PieceType::ROOK => Some(Self::HAND_ROOK),
            PieceType::GOLD => Some(Self::HAND_GOLD),
            _ => None,
        }
    }

    /// `PieceType` へ変換
    #[must_use]
    pub const fn into_piece_type(self) -> PieceType {
        match self {
            Self::HAND_PAWN => PieceType::PAWN,
            Self::HAND_LANCE => PieceType::LANCE,
            Self::HAND_KNIGHT => PieceType::KNIGHT,
            Self::HAND_SILVER => PieceType::SILVER,
            Self::HAND_BISHOP => PieceType::BISHOP,
            Self::HAND_ROOK => PieceType::ROOK,
            Self::HAND_GOLD => PieceType::GOLD,
            _ => PieceType::NO_PIECE_TYPE,
        }
    }

    /// 有効な値かどうか判定
    #[must_use]
    pub const fn is_ok(self) -> bool {
        self.0 >= 0 && self.0 <= Self::HAND_GOLD.raw()
    }

    /// 内部値を取得する（主にテスト用）
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }
}

/// 持ち駒
/// ビットフィールド構成:
/// - 歩: bit0-4 (5bit, 最大31枚)
/// - 香: bit8-10 (3bit, 最大7枚)
/// - 桂: bit12-14 (3bit, 最大7枚)
/// - 銀: bit16-18 (3bit, 最大7枚)
/// - 角: bit20-21 (2bit, 最大3枚)
/// - 飛: bit24-25 (2bit, 最大3枚)
/// - 金: bit28-30 (3bit, 最大7枚)
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Hand(pub u32);

impl Hand {
    pub const HAND_ZERO: Self = Self(0);

    // ビット配置定数（開始ビット位置）
    const PIECE_BITS: [u32; 7] = [
        0,  // 歩: bit 0から
        8,  // 香: bit 8から
        12, // 桂: bit 12から
        16, // 銀: bit 16から
        20, // 角: bit 20から
        24, // 飛: bit 24から
        28, // 金: bit 28から
    ];

    // ビットマスク（各駒種のビット幅）
    const PIECE_BIT_MASK: [u32; 7] = [
        0x1f, // 歩: 5bit
        0x07, // 香: 3bit
        0x07, // 桂: 3bit
        0x07, // 銀: 3bit
        0x03, // 角: 2bit
        0x03, // 飛: 2bit
        0x07, // 金: 3bit
    ];

    // 単体マスク（1枚分の値）
    const PIECE_BIT_ONE: [u32; 7] = [
        1 << 0,  // 歩
        1 << 8,  // 香
        1 << 12, // 桂
        1 << 16, // 銀
        1 << 20, // 角
        1 << 24, // 飛
        1 << 28, // 金
    ];

    // 優劣判定用マスク

    /// 指定した駒種の枚数を取得
    #[inline]
    #[must_use]
    pub const fn hand_count(hand: Self, hp: HandPiece) -> u32 {
        if let Some(idx) = Self::index_for(hp) {
            let shift = Self::PIECE_BITS[idx];
            let mask = Self::PIECE_BIT_MASK[idx];
            (hand.0 >> shift) & mask
        } else {
            0
        }
    }

    /// 指定した駒種が存在するか判定
    #[inline]
    #[must_use]
    pub const fn hand_exists(hand: Self, hp: HandPiece) -> bool {
        Self::hand_count(hand, hp) > 0
    }

    /// 指定した駒種を1枚追加
    #[inline]
    #[must_use]
    pub const fn add_hand(hand: Self, hp: HandPiece) -> Self {
        if let Some(idx) = Self::index_for(hp) {
            Self(hand.0 + Self::PIECE_BIT_ONE[idx])
        } else {
            hand
        }
    }

    /// 指定した駒種を1枚減らす
    #[inline]
    #[must_use]
    pub const fn sub_hand(hand: Self, hp: HandPiece) -> Self {
        if let Some(idx) = Self::index_for(hp) {
            Self(hand.0 - Self::PIECE_BIT_ONE[idx])
        } else {
            hand
        }
    }

    /// h1がh2以上の持ち駒を持っているか判定
    /// `HAND_BORROW_MASK` を使った高速判定
    #[must_use]
    pub const fn hand_is_equal_or_superior(h1: Self, h2: Self) -> bool {
        (h1.0.wrapping_sub(h2.0) & HAND_BORROW_MASK) == 0
    }

    // 簡便なメソッド追加
    /// 指定した駒種の枚数を取得
    #[inline]
    #[must_use]
    pub const fn count(&self, hp: HandPiece) -> u32 {
        Self::hand_count(*self, hp)
    }

    /// 指定した駒種を指定枚数追加
    #[inline]
    pub fn add(&mut self, hp: HandPiece, n: u32) {
        for _ in 0..n {
            *self = Self::add_hand(*self, hp);
        }
    }

    /// 指定した駒種を指定枚数減らす
    #[inline]
    pub fn sub(&mut self, hp: HandPiece, n: u32) {
        for _ in 0..n {
            *self = Self::sub_hand(*self, hp);
        }
    }

    /// 歩の枚数を取得
    #[inline]
    #[must_use]
    pub const fn pawn_count(&self) -> u32 {
        self.count(HandPiece::HAND_PAWN)
    }

    /// 持ち駒種に対応するインデックス
    const fn index_for(hp: HandPiece) -> Option<usize> {
        match hp {
            HandPiece::HAND_PAWN => Some(0),
            HandPiece::HAND_LANCE => Some(1),
            HandPiece::HAND_KNIGHT => Some(2),
            HandPiece::HAND_SILVER => Some(3),
            HandPiece::HAND_BISHOP => Some(4),
            HandPiece::HAND_ROOK => Some(5),
            HandPiece::HAND_GOLD => Some(6),
            _ => None,
        }
    }
}

impl Default for Hand {
    fn default() -> Self {
        Self::HAND_ZERO
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hand_piece_constants() {
        assert_eq!(HandPiece::HAND_PAWN.raw(), 0);
        assert_eq!(HandPiece::HAND_LANCE.raw(), 1);
        assert_eq!(HandPiece::HAND_KNIGHT.raw(), 2);
        assert_eq!(HandPiece::HAND_SILVER.raw(), 3);
        assert_eq!(HandPiece::HAND_BISHOP.raw(), 4);
        assert_eq!(HandPiece::HAND_ROOK.raw(), 5);
        assert_eq!(HandPiece::HAND_GOLD.raw(), 6);
        assert_eq!(HandPiece::HAND_NB, 7);
    }

    #[test]
    fn test_hand_piece_conversion() {
        // from_piece_type -> into_piece_type round trip
        let test_cases = [
            (PieceType::PAWN, HandPiece::HAND_PAWN),
            (PieceType::LANCE, HandPiece::HAND_LANCE),
            (PieceType::KNIGHT, HandPiece::HAND_KNIGHT),
            (PieceType::SILVER, HandPiece::HAND_SILVER),
            (PieceType::BISHOP, HandPiece::HAND_BISHOP),
            (PieceType::ROOK, HandPiece::HAND_ROOK),
            (PieceType::GOLD, HandPiece::HAND_GOLD),
        ];

        for (pt, hp) in test_cases {
            assert_eq!(HandPiece::from_piece_type(pt), Some(hp));
            assert_eq!(hp.into_piece_type(), pt);
        }

        // 不正な駒種
        assert_eq!(HandPiece::from_piece_type(PieceType::KING), None);
        assert_eq!(HandPiece::from_piece_type(PieceType::PRO_PAWN), None);
        assert_eq!(HandPiece::from_piece_type(PieceType::NO_PIECE_TYPE), None);
    }

    #[test]
    fn test_hand_piece_is_ok() {
        // 有効な値
        for i in 0..7 {
            assert!(HandPiece(i).is_ok());
        }

        // 無効な値
        assert!(!HandPiece(-1).is_ok());
        assert!(!HandPiece(7).is_ok());
        assert!(!HandPiece(100).is_ok());
    }

    #[test]
    fn test_hand_bit_packing() {
        // 空の持ち駒
        assert_eq!(Hand::HAND_ZERO.0, 0);

        // 各駒種を1枚ずつ追加
        let mut hand = Hand::HAND_ZERO;

        // 歩を1枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_PAWN);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_PAWN), 1);
        assert_eq!(hand.0, 1);

        // 香を1枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_LANCE);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_LANCE), 1);
        assert_eq!(hand.0, 1 | (1 << 8));

        // 桂を1枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_KNIGHT);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_KNIGHT), 1);
        assert_eq!(hand.0, 1 | (1 << 8) | (1 << 12));
    }

    #[test]
    fn test_hand_add_sub() {
        let mut hand = Hand::HAND_ZERO;

        // 歩を5枚追加
        for _ in 0..5 {
            hand = Hand::add_hand(hand, HandPiece::HAND_PAWN);
        }
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_PAWN), 5);

        // 歩を2枚減らす
        for _ in 0..2 {
            hand = Hand::sub_hand(hand, HandPiece::HAND_PAWN);
        }
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_PAWN), 3);

        // 角を2枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_BISHOP);
        hand = Hand::add_hand(hand, HandPiece::HAND_BISHOP);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_BISHOP), 2);

        // 飛車を1枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_ROOK);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_ROOK), 1);
    }

    #[test]
    fn test_hand_exists() {
        let mut hand = Hand::HAND_ZERO;

        // 最初は何も持っていない
        assert!(!Hand::hand_exists(hand, HandPiece::HAND_PAWN));
        assert!(!Hand::hand_exists(hand, HandPiece::HAND_GOLD));

        // 金を1枚追加
        hand = Hand::add_hand(hand, HandPiece::HAND_GOLD);
        assert!(Hand::hand_exists(hand, HandPiece::HAND_GOLD));
        assert!(!Hand::hand_exists(hand, HandPiece::HAND_PAWN));
    }

    #[test]
    fn test_hand_is_equal_or_superior() {
        let h1 = Hand::HAND_ZERO;
        let mut h2 = Hand::HAND_ZERO;

        // 同じ持ち駒
        assert!(Hand::hand_is_equal_or_superior(h1, h2));

        // h1の方が少ない
        h2 = Hand::add_hand(h2, HandPiece::HAND_PAWN);
        assert!(!Hand::hand_is_equal_or_superior(h1, h2));

        // h1の方が多い
        let mut h3 = Hand::add_hand(h1, HandPiece::HAND_PAWN);
        h3 = Hand::add_hand(h3, HandPiece::HAND_PAWN);
        assert!(Hand::hand_is_equal_or_superior(h3, h2));

        // 複数種類の駒での比較
        let mut h4 = Hand::HAND_ZERO;
        let mut h5 = Hand::HAND_ZERO;

        // h4: 歩3, 金1
        for _ in 0..3 {
            h4 = Hand::add_hand(h4, HandPiece::HAND_PAWN);
        }
        h4 = Hand::add_hand(h4, HandPiece::HAND_GOLD);

        // h5: 歩2, 金1
        for _ in 0..2 {
            h5 = Hand::add_hand(h5, HandPiece::HAND_PAWN);
        }
        h5 = Hand::add_hand(h5, HandPiece::HAND_GOLD);

        assert!(Hand::hand_is_equal_or_superior(h4, h5));
        assert!(!Hand::hand_is_equal_or_superior(h5, h4));
    }

    #[test]
    fn test_hand_overflow_boundary() {
        let mut hand = Hand::HAND_ZERO;

        // 歩を最大枚数（18枚）近くまで追加
        for _ in 0..18 {
            hand = Hand::add_hand(hand, HandPiece::HAND_PAWN);
        }
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_PAWN), 18);

        // 金を最大枚数（4枚）追加
        for _ in 0..4 {
            hand = Hand::add_hand(hand, HandPiece::HAND_GOLD);
        }
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_GOLD), 4);

        // 他の駒種が影響を受けていないことを確認
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_PAWN), 18);
        assert_eq!(Hand::hand_count(hand, HandPiece::HAND_LANCE), 0);
    }
}
