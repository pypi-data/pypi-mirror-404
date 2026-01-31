//! 指し手の型定義

use super::{Color, Piece, PieceType, Square};
use std::convert::TryFrom;
use std::fmt;

/// 16bit指し手表現
/// ビットフィールド構成:
/// - bit0..6: 移動先 (to)
/// - bit7..13: 移動元 (from) または打つ駒種
/// - bit14: 駒打ちフラグ (`MOVE_DROP`)
/// - bit15: 成りフラグ (`MOVE_PROMOTE`)
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Move16(pub u16);

// 定数定義（YaneuraOu互換）
// Move32用
pub const MOVE_NONE: Move = Move(0);
pub const MOVE_NULL: Move = Move(((1 << 7) + 1) as u32);
pub const MOVE_RESIGN: Move = Move(((2 << 7) + 2) as u32);
pub const MOVE_WIN: Move = Move(((3 << 7) + 3) as u32);

// Move16用
pub const MOVE16_NONE: Move16 = Move16(0);
pub const MOVE16_NULL: Move16 = Move16((1 << 7) + 1);
pub const MOVE16_RESIGN: Move16 = Move16((2 << 7) + 2);
pub const MOVE16_WIN: Move16 = Move16((3 << 7) + 3);

// フラグ定数
pub const MOVE16_DROP_MASK: u16 = 1 << 14;
pub const MOVE16_PROMOTE_MASK: u16 = 1 << 15;

/// 指し手種別（YaneuraOu互換）
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum MoveType {
    Normal,
    Promotion,
    Drop,
}

impl MoveType {
    #[inline]
    #[must_use]
    pub const fn from_bits(bits: u16) -> Self {
        match bits {
            Move16::MOVE_PROMOTE => Self::Promotion,
            Move16::MOVE_DROP => Self::Drop,
            _ => Self::Normal,
        }
    }
}

impl Move16 {
    // 特殊手定数（互換性のため残す）
    pub const MOVE_NONE: Self = Self(0);
    pub const MOVE_NULL: Self = Self((1 << 7) + 1);
    pub const MOVE_RESIGN: Self = Self((2 << 7) + 2);
    pub const MOVE_WIN: Self = Self((3 << 7) + 3);

    // フラグ定数
    pub const MOVE_DROP: u16 = 1 << 14;
    pub const MOVE_PROMOTE: u16 = 1 << 15;

    // ビットマスク
    const TO_MASK: u16 = 0x7f; // 下位7bit
    const FROM_MASK: u16 = 0x7f; // 7bit分
    const FROM_SHIFT: u16 = 7;

    /// 通常の移動手を生成
    #[must_use]
    pub fn make_move(from: Square, to: Square) -> Self {
        let from_idx = u16::try_from(from.to_board_index()).expect("from square index");
        let to_idx = u16::try_from(to.to_board_index()).expect("to square index");
        Self((from_idx << Self::FROM_SHIFT) | to_idx)
    }

    /// 駒打ち手を生成
    #[must_use]
    pub fn make_drop(piece_type: PieceType, to: Square) -> Self {
        let piece_idx = u16::try_from(piece_type.to_index()).expect("piece type index");
        let to_idx = u16::try_from(to.to_board_index()).expect("drop target index");
        Self(Self::MOVE_DROP | (piece_idx << Self::FROM_SHIFT) | to_idx)
    }

    /// 成り手を生成
    #[must_use]
    pub fn make_promote(from: Square, to: Square) -> Self {
        let from_idx = u16::try_from(from.to_board_index()).expect("from square index");
        let to_idx = u16::try_from(to.to_board_index()).expect("to square index");
        Self(Self::MOVE_PROMOTE | (from_idx << Self::FROM_SHIFT) | to_idx)
    }

    /// 移動元の座標を取得
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub const fn from_sq(self) -> Square {
        Square::new(((self.0 >> Self::FROM_SHIFT) & Self::FROM_MASK) as i8)
    }

    /// 移動先の座標を取得
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub const fn to_sq(self) -> Square {
        Square::new((self.0 & Self::TO_MASK) as i8)
    }

    /// 駒打ちかどうか判定
    #[must_use]
    pub const fn is_drop(self) -> bool {
        (self.0 & Self::MOVE_DROP) != 0
    }

    /// 成りかどうか判定
    #[must_use]
    pub const fn is_promote(self) -> bool {
        (self.0 & Self::MOVE_PROMOTE) != 0
    }

    /// 指し手種別を取得
    #[must_use]
    pub const fn type_of(self) -> MoveType {
        MoveType::from_bits(self.0 & (Self::MOVE_PROMOTE | Self::MOVE_DROP))
    }

    /// 打つ駒種を取得（駒打ちの場合）
    #[must_use]
    pub fn dropped_piece(self) -> Option<PieceType> {
        if self.is_drop() {
            let raw = (self.0 >> Self::FROM_SHIFT) & Self::FROM_MASK;
            let piece_raw = i8::try_from(raw).expect("piece type nibble");
            Some(PieceType::new(piece_raw))
        } else {
            None
        }
    }

    /// 有効な手かどうか判定（特殊手を除外）
    #[must_use]
    pub fn is_ok(self) -> bool {
        if self == Self::MOVE_NONE
            || self == Self::MOVE_NULL
            || self == Self::MOVE_RESIGN
            || self == Self::MOVE_WIN
        {
            return false;
        }

        let to = self.to_sq();
        if !to.is_ok() || to == Square::SQ_NONE {
            return false;
        }

        if self.is_drop() {
            // 駒打ちの場合は駒種をチェック
            self.dropped_piece()
                .map_or(false, |pt| pt.0 >= PieceType::PAWN.0 && pt.0 <= PieceType::GOLD.0)
        } else {
            // 通常移動の場合は移動元をチェック
            let from = self.from_sq();
            from.is_ok() && from != Square::SQ_NONE
        }
    }

    /// USI形式の文字列から生成
    #[must_use]
    pub fn from_usi(s: &str) -> Option<Self> {
        // 特殊な手（YaneuraOuはMOVE_NONE扱い）
        if s == "null" || s == "none" {
            return Some(Self::MOVE_NONE);
        }

        let chars: Vec<char> = s.chars().collect();

        // 駒打ち（例: "P*5e"）
        if chars.len() >= 4 && chars[1] == '*' {
            let piece_str = chars[0].to_string();
            let pt = match piece_str.as_str() {
                "P" => PieceType::PAWN,
                "L" => PieceType::LANCE,
                "N" => PieceType::KNIGHT,
                "S" => PieceType::SILVER,
                "B" => PieceType::BISHOP,
                "R" => PieceType::ROOK,
                "G" => PieceType::GOLD,
                _ => return None,
            };

            let to_str: String = chars[2..4].iter().collect();
            let to = Square::from_usi(&to_str)?;

            return Some(Self::make_drop(pt, to));
        }

        // 通常移動（例: "7g7f" または "2b3c+"）
        if chars.len() >= 4 {
            let from_str: String = chars[0..2].iter().collect();
            let to_str: String = chars[2..4].iter().collect();

            let from = Square::from_usi(&from_str)?;
            let to = Square::from_usi(&to_str)?;

            let is_promote = chars.len() >= 5 && chars[4] == '+';

            if is_promote {
                Some(Self::make_promote(from, to))
            } else {
                Some(Self::make_move(from, to))
            }
        } else {
            None
        }
    }

    /// USI形式の文字列に変換
    #[must_use]
    pub fn to_usi(&self) -> String {
        if !self.is_ok() {
            return if *self == Self::MOVE_RESIGN {
                "resign".to_string()
            } else if *self == Self::MOVE_WIN {
                "win".to_string()
            } else if *self == Self::MOVE_NULL {
                "null".to_string()
            } else if *self == Self::MOVE_NONE {
                "none".to_string()
            } else {
                String::new()
            };
        }

        if self.is_drop() {
            // 駒打ち
            let Some(pt) = self.dropped_piece() else {
                return String::new();
            };
            let piece_char = match pt {
                PieceType::PAWN => "P",
                PieceType::LANCE => "L",
                PieceType::KNIGHT => "N",
                PieceType::SILVER => "S",
                PieceType::BISHOP => "B",
                PieceType::ROOK => "R",
                PieceType::GOLD => "G",
                _ => return String::new(),
            };
            format!("{piece_char}*{}", self.to_sq())
        } else {
            // 通常移動
            let mut result = format!("{}{}", self.from_sq(), self.to_sq());
            if self.is_promote() {
                result.push('+');
            }
            result
        }
    }
}

impl fmt::Display for Move16 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_usi())
    }
}

/// 32bit指し手表現（駒情報付き）
/// - 下位16bit: Move16
/// - 上位16bit: 移動する駒（Piece, 下位5bitのみ使用）
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Move(pub u32);

impl Move {
    /// 通常移動の生成
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub fn make(from: Square, to: Square, piece: Piece) -> Self {
        let m16 = Move16::make_move(from, to);
        let piece_raw = u8::try_from(piece.raw()).expect("piece index fits in u8") & 0x1f;
        Self((u32::from(piece_raw) << 16) | u32::from(m16.0))
    }

    /// 駒打ちの生成
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub fn make_drop(piece_type: PieceType, to: Square, color: Color) -> Self {
        let m16 = Move16::make_drop(piece_type, to);
        let piece = Piece::make(color, piece_type);
        let piece_raw = u8::try_from(piece.raw()).expect("piece index fits in u8") & 0x1f;
        Self((u32::from(piece_raw) << 16) | u32::from(m16.0))
    }

    /// 成り移動の生成
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub fn make_promote(from: Square, to: Square, piece: Piece) -> Self {
        let m16 = Move16::make_promote(from, to);
        let promoted = piece.promote();
        let piece_raw = u8::try_from(promoted.raw()).expect("piece index fits in u8") & 0x1f;
        Self((u32::from(piece_raw) << 16) | u32::from(m16.0))
    }

    /// Move16部分を取得
    #[must_use]
    #[allow(clippy::cast_possible_truncation)]
    pub const fn to_move16(self) -> Move16 {
        Move16((self.0 & 0xffff) as u16)
    }

    /// 移動後の駒を取得
    #[must_use]
    pub fn moved_after_piece(self) -> Piece {
        let raw = ((self.0 >> 16) & 0x1f) as u8;
        Piece::new(i8::try_from(raw).expect("piece index fits in i8"))
    }

    // Move16のメソッドを委譲
    #[must_use]
    pub const fn from_sq(self) -> Square {
        self.to_move16().from_sq()
    }

    #[must_use]
    pub const fn to_sq(self) -> Square {
        self.to_move16().to_sq()
    }

    #[must_use]
    pub const fn is_drop(self) -> bool {
        self.to_move16().is_drop()
    }

    #[must_use]
    pub const fn is_promote(self) -> bool {
        self.to_move16().is_promote()
    }

    #[must_use]
    pub fn dropped_piece(self) -> Option<PieceType> {
        self.to_move16().dropped_piece()
    }

    /// 指し手種別を取得
    #[must_use]
    pub const fn type_of(self) -> MoveType {
        self.to_move16().type_of()
    }

    #[must_use]
    pub fn is_ok(self) -> bool {
        self.to_move16().is_ok()
    }

    #[must_use]
    pub fn to_usi(self) -> String {
        self.to_move16().to_usi()
    }
}

impl Default for Move {
    fn default() -> Self {
        MOVE_NONE
    }
}

impl fmt::Display for Move {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_usi())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::PieceType;

    #[test]
    fn test_move16_constants() {
        assert_eq!(Move16::MOVE_NONE.0, 0);
        assert_eq!(Move16::MOVE_NULL.0, (1 << 7) + 1);
        assert_eq!(Move16::MOVE_RESIGN.0, (2 << 7) + 2);
        assert_eq!(Move16::MOVE_WIN.0, (3 << 7) + 3);
        assert_eq!(Move16::MOVE_DROP, 1 << 14);
        assert_eq!(Move16::MOVE_PROMOTE, 1 << 15);
    }

    #[test]
    fn test_move16_bit_encoding() {
        // 通常移動: 7g → 7f
        let from = "7g".parse::<Square>().unwrap();
        let to = "7f".parse::<Square>().unwrap();
        let m = Move16::make_move(from, to);
        assert_eq!(m.to_sq(), to);
        assert_eq!(m.from_sq(), from);
        assert!(!m.is_drop());
        assert!(!m.is_promote());

        // 駒打ち: P*5e(40)
        let drop_to = "5e".parse::<Square>().unwrap();
        let m = Move16::make_drop(PieceType::PAWN, drop_to);
        assert_eq!(m.to_sq(), drop_to);
        assert!(m.is_drop());
        assert_eq!(m.dropped_piece(), Some(PieceType::PAWN));
        assert!(!m.is_promote());

        // 成り移動: 2b(10) → 3c(20)+
        let promote_from = "2b".parse::<Square>().unwrap();
        let promote_to = "3c".parse::<Square>().unwrap();
        let m = Move16::make_promote(promote_from, promote_to);
        assert_eq!(m.to_sq(), promote_to);
        assert_eq!(m.from_sq(), promote_from);
        assert!(!m.is_drop());
        assert!(m.is_promote());
    }

    #[test]
    fn test_move16_from_usi() {
        // 通常移動
        let m = Move16::from_usi("7g7f").unwrap();
        assert_eq!(m.from_sq(), "7g".parse::<Square>().unwrap());
        assert_eq!(m.to_sq(), "7f".parse::<Square>().unwrap());
        assert!(!m.is_drop());
        assert!(!m.is_promote());

        // 駒打ち
        let m = Move16::from_usi("P*5e").unwrap();
        assert!(m.is_drop());
        assert_eq!(m.dropped_piece(), Some(PieceType::PAWN));
        assert_eq!(m.to_sq(), "5e".parse::<Square>().unwrap());

        // 成り移動
        let m = Move16::from_usi("2b3c+").unwrap();
        let from_sq_expected = "2b".parse::<Square>().unwrap();
        let to_sq_expected = "3c".parse::<Square>().unwrap();
        assert_eq!(m.from_sq(), from_sq_expected);
        assert_eq!(m.to_sq(), to_sq_expected);
        assert!(m.is_promote());

        // 特殊な手はUSI変換対象外
        assert_eq!(Move16::from_usi("resign"), None);
        assert_eq!(Move16::from_usi("win"), None);
        assert_eq!(Move16::from_usi("null"), Some(Move16::MOVE_NONE));
        assert_eq!(Move16::from_usi("none"), Some(Move16::MOVE_NONE));
    }

    #[test]
    fn test_move16_to_usi() {
        // 通常移動
        let m = Move16::make_move("7g".parse().unwrap(), "7f".parse().unwrap());
        assert_eq!(m.to_usi(), "7g7f");

        // 駒打ち
        let m = Move16::make_drop(PieceType::PAWN, "5e".parse::<Square>().unwrap());
        assert_eq!(m.to_usi(), "P*5e");

        // 成り移動
        let from_sq_expected = "2b".parse::<Square>().unwrap();
        let to_sq_expected = "3c".parse::<Square>().unwrap();
        let m = Move16::make_promote(from_sq_expected, to_sq_expected);
        assert_eq!(m.to_usi(), "2b3c+");

        // 特殊な手
        assert_eq!(Move16::MOVE_NONE.to_usi(), "none");
        assert_eq!(Move16::MOVE_RESIGN.to_usi(), "resign");
        assert_eq!(Move16::MOVE_WIN.to_usi(), "win");
    }

    #[test]
    fn test_move16_usi_round_trip() {
        let test_cases = vec!["7g7f", "2g2f", "8h2b+", "P*5e", "G*3c", "1a1b+"];

        for usi in test_cases {
            let m = Move16::from_usi(usi).unwrap();
            assert_eq!(m.to_usi(), usi);
        }
    }

    #[test]
    fn test_move16_is_ok() {
        // 有効な手
        assert!(Move16::make_move("8g".parse().unwrap(), "8f".parse().unwrap()).is_ok());
        assert!(Move16::make_drop(PieceType::PAWN, "5e".parse().unwrap()).is_ok());
        assert!(Move16::make_promote("2b".parse().unwrap(), "3c".parse().unwrap()).is_ok());

        // 特殊手は無効扱い
        assert!(!Move16::MOVE_NONE.is_ok());
        assert!(!Move16::MOVE_NULL.is_ok());
        assert!(!Move16::MOVE_RESIGN.is_ok());
        assert!(!Move16::MOVE_WIN.is_ok());

        // 不正な駒打ち（KING）
        let invalid_drop = Move16(Move16::MOVE_DROP | ((PieceType::KING.0 as u16) << 7) | 40);
        assert!(!invalid_drop.is_ok());
    }

    #[test]
    fn test_move32_structure() {
        // 通常移動
        let normal_from = "7g".parse::<Square>().unwrap();
        let normal_to = "7f".parse::<Square>().unwrap();
        let m = Move::make(normal_from, normal_to, Piece::B_PAWN);
        assert_eq!(m.to_move16(), Move16::make_move(normal_from, normal_to));
        assert_eq!(m.moved_after_piece(), Piece::B_PAWN);

        // 駒打ち
        let drop_sq = "5e".parse::<Square>().unwrap();
        let m = Move::make_drop(PieceType::GOLD, drop_sq, Color::WHITE);
        assert_eq!(m.to_move16(), Move16::make_drop(PieceType::GOLD, drop_sq));
        assert_eq!(m.moved_after_piece(), Piece::W_GOLD);

        // 成り移動
        let promote_from = "2b".parse::<Square>().unwrap();
        let promote_to = "3c".parse::<Square>().unwrap();
        let m = Move::make_promote(promote_from, promote_to, Piece::B_BISHOP);
        assert_eq!(m.to_move16(), Move16::make_promote(promote_from, promote_to));
        assert_eq!(m.moved_after_piece(), Piece::B_HORSE); // BISHOPが成ってHORSEに
    }

    #[test]
    fn test_move32_delegation() {
        let from = "7g".parse::<Square>().unwrap();
        let to = "7f".parse::<Square>().unwrap();
        let m = Move::make(from, to, Piece::B_PAWN);
        assert_eq!(m.from_sq(), from);
        assert_eq!(m.to_sq(), to);
        assert!(!m.is_drop());
        assert!(!m.is_promote());
        assert_eq!(m.dropped_piece(), None);
        assert!(m.is_ok());
        assert_eq!(m.to_usi(), "7g7f");
    }
}
