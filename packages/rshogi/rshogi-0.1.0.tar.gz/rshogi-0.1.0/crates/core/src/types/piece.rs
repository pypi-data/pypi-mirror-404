//! 駒種と駒の型定義

use super::Color;
use std::convert::TryFrom;
use std::fmt;
use std::str::FromStr;

/// 駒種を表す型（先手/後手の区別なし）
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct PieceType(pub i8);

impl PieceType {
    // 関連定数（YaneuraOu互換）
    // 非成駒定数
    /// 無効な駒種
    pub const NO_PIECE_TYPE: Self = Self(0);
    /// 歩
    pub const PAWN: Self = Self(1);
    /// 香車
    pub const LANCE: Self = Self(2);
    /// 桂馬
    pub const KNIGHT: Self = Self(3);
    /// 銀
    pub const SILVER: Self = Self(4);
    /// 角
    pub const BISHOP: Self = Self(5);
    /// 飛車
    pub const ROOK: Self = Self(6);
    /// 金
    pub const GOLD: Self = Self(7);
    /// 玉
    pub const KING: Self = Self(8);

    // 成駒定数
    /// と金（成歩）
    pub const PRO_PAWN: Self = Self(9);
    /// 成香
    pub const PRO_LANCE: Self = Self(10);
    /// 成桂
    pub const PRO_KNIGHT: Self = Self(11);
    /// 成銀
    pub const PRO_SILVER: Self = Self(12);
    /// 馬（成角）
    pub const HORSE: Self = Self(13);
    /// 龍（成飛）
    pub const DRAGON: Self = Self(14);
    /// 金相当の駒（GOLDS）
    pub const GOLDS: Self = Self(15);

    // メタ定数
    /// 駒種の総数
    pub const PIECE_TYPE_NB: usize = 16;
    /// 成り変換用オフセット
    pub const PIECE_TYPE_PROMOTE: i8 = 8;
    /// 持ち駒の起点（PAWN）
    pub const PIECE_HAND_ZERO: Self = Self(1);
    /// 持ち駒種類数
    pub const PIECE_HAND_NB: usize = 8;

    /// const fn コンストラクタ
    #[inline]
    #[must_use]
    pub const fn new(value: i8) -> Self {
        Self(value)
    }

    /// 成れる駒かどうかを判定
    #[must_use]
    pub const fn is_promotable(self) -> bool {
        self.0 >= Self::PAWN.0 && self.0 <= Self::ROOK.0
    }

    /// 成り駒かどうかを判定
    #[must_use]
    pub const fn is_promoted(self) -> bool {
        self.0 >= Self::PRO_PAWN.0
    }

    /// これ以上成れない駒かどうかを判定
    #[must_use]
    pub const fn is_non_promotable(self) -> bool {
        self.0 >= Self::GOLD.0
    }

    /// 成り駒に変換
    #[must_use]
    pub const fn promote(self) -> Self {
        if self.is_promotable() {
            Self(self.0 + Self::PIECE_TYPE_PROMOTE)
        } else {
            self
        }
    }

    /// 成り駒を元の駒に戻す（持ち駒変換用）
    #[must_use]
    pub const fn demote(self) -> Self {
        match self.0 {
            9..=14 => Self(self.0 - Self::PIECE_TYPE_PROMOTE), // 成駒を元に戻す
            _ => self,                                         // それ以外はそのまま
        }
    }

    /// 有効な値かどうかを判定
    #[must_use]
    pub fn is_ok(self) -> bool {
        usize::try_from(self.0).map(|idx| idx < Self::PIECE_TYPE_NB).unwrap_or(false)
    }

    /// 内部値を取得する（主にテスト用）
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }

    /// `PieceType` をインデックス値に変換
    #[inline]
    #[must_use]
    #[allow(clippy::cast_sign_loss)]
    pub const fn to_index(self) -> usize {
        self.0 as usize
    }
}

impl Default for PieceType {
    fn default() -> Self {
        Self::NO_PIECE_TYPE
    }
}

impl fmt::Display for PieceType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match *self {
            Self::PAWN => "P",
            Self::LANCE => "L",
            Self::KNIGHT => "N",
            Self::SILVER => "S",
            Self::BISHOP => "B",
            Self::ROOK => "R",
            Self::GOLD => "G",
            Self::KING => "K",
            Self::PRO_PAWN => "+P",
            Self::PRO_LANCE => "+L",
            Self::PRO_KNIGHT => "+N",
            Self::PRO_SILVER => "+S",
            Self::HORSE => "+B",
            Self::DRAGON => "+R",
            _ => "?",
        };
        write!(f, "{s}")
    }
}

impl FromStr for PieceType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "P" => Ok(Self::PAWN),
            "L" => Ok(Self::LANCE),
            "N" => Ok(Self::KNIGHT),
            "S" => Ok(Self::SILVER),
            "B" => Ok(Self::BISHOP),
            "R" => Ok(Self::ROOK),
            "G" => Ok(Self::GOLD),
            "K" => Ok(Self::KING),
            "+P" => Ok(Self::PRO_PAWN),
            "+L" => Ok(Self::PRO_LANCE),
            "+N" => Ok(Self::PRO_KNIGHT),
            "+S" => Ok(Self::PRO_SILVER),
            "+B" => Ok(Self::HORSE),
            "+R" => Ok(Self::DRAGON),
            _ => Err(format!("Invalid piece type: {s}")),
        }
    }
}

/// 駒を表す型（先手/後手の区別あり）
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Piece(pub i8);

impl Piece {
    // 関連定数（YaneuraOu互換）
    // 特殊値
    /// 無効な駒
    pub const NO_PIECE: Self = Self(0);

    // 先手駒定数
    /// 先手の歩
    pub const B_PAWN: Self = Self(1);
    /// 先手の香
    pub const B_LANCE: Self = Self(2);
    /// 先手の桂
    pub const B_KNIGHT: Self = Self(3);
    /// 先手の銀
    pub const B_SILVER: Self = Self(4);
    /// 先手の角
    pub const B_BISHOP: Self = Self(5);
    /// 先手の飛車
    pub const B_ROOK: Self = Self(6);
    /// 先手の金
    pub const B_GOLD: Self = Self(7);
    /// 先手の玉
    pub const B_KING: Self = Self(8);
    /// 先手のと金
    pub const B_PRO_PAWN: Self = Self(9);
    /// 先手の成香
    pub const B_PRO_LANCE: Self = Self(10);
    /// 先手の成桂
    pub const B_PRO_KNIGHT: Self = Self(11);
    /// 先手の成銀
    pub const B_PRO_SILVER: Self = Self(12);
    /// 先手の馬
    pub const B_HORSE: Self = Self(13);
    /// 先手の龍
    pub const B_DRAGON: Self = Self(14);
    /// 先手の金相当駒（GOLDS）
    pub const B_GOLDS: Self = Self(15);

    // 後手駒定数
    /// 後手の歩
    pub const W_PAWN: Self = Self(17);
    /// 後手の香
    pub const W_LANCE: Self = Self(18);
    /// 後手の桂
    pub const W_KNIGHT: Self = Self(19);
    /// 後手の銀
    pub const W_SILVER: Self = Self(20);
    /// 後手の角
    pub const W_BISHOP: Self = Self(21);
    /// 後手の飛車
    pub const W_ROOK: Self = Self(22);
    /// 後手の金
    pub const W_GOLD: Self = Self(23);
    /// 後手の玉
    pub const W_KING: Self = Self(24);
    /// 後手のと金
    pub const W_PRO_PAWN: Self = Self(25);
    /// 後手の成香
    pub const W_PRO_LANCE: Self = Self(26);
    /// 後手の成桂
    pub const W_PRO_KNIGHT: Self = Self(27);
    /// 後手の成銀
    pub const W_PRO_SILVER: Self = Self(28);
    /// 後手の馬
    pub const W_HORSE: Self = Self(29);
    /// 後手の龍
    pub const W_DRAGON: Self = Self(30);
    /// 後手の金相当駒（GOLDS）
    pub const W_GOLDS: Self = Self(31);

    // メタ定数
    /// 駒の総数
    pub const PIECE_NB: usize = 32;
    /// 成りフラグ
    pub const PIECE_PROMOTE: i8 = 8;
    /// 後手フラグ
    pub const PIECE_WHITE: i8 = 16;
    /// 持ち駒種類数
    pub const PIECE_HAND_NB: usize = 8;
    /// 非成駒の終端
    pub const PIECE_RAW_NB: usize = 8;

    /// const fn コンストラクタ
    #[inline]
    #[must_use]
    pub const fn new(value: i8) -> Self {
        Self(value)
    }

    /// 手番と駒種から駒を作成
    #[must_use]
    pub const fn make(color: Color, piece_type: PieceType) -> Self {
        let base = piece_type.0;
        if color.raw() == Color::WHITE.raw() {
            Self(base | Self::PIECE_WHITE)
        } else {
            Self(base)
        }
    }

    /// 駒の手番を取得
    #[must_use]
    pub const fn color(self) -> Color {
        if (self.0 & Self::PIECE_WHITE) != 0 {
            Color::WHITE
        } else {
            Color::BLACK
        }
    }

    /// 駒種を取得
    #[must_use]
    pub const fn piece_type(self) -> PieceType {
        PieceType(self.0 & 15)
    }

    /// 成り駒に変換
    #[must_use]
    pub const fn promote(self) -> Self {
        let pt = self.piece_type();
        if pt.is_promotable() {
            Self(self.0 + Self::PIECE_PROMOTE)
        } else {
            self
        }
    }

    /// 成り駒かどうかを判定
    #[must_use]
    pub const fn is_promoted(self) -> bool {
        self.piece_type().is_promoted()
    }

    /// これ以上成れない駒かどうかを判定
    #[must_use]
    pub const fn is_non_promotable(self) -> bool {
        self.piece_type().is_non_promotable()
    }

    /// 成りを外した駒種を取得（先後なし）
    #[must_use]
    pub const fn raw_piece_type(self) -> PieceType {
        PieceType(self.0 & 7)
    }

    /// 成りを外した駒を取得（先後維持）
    #[must_use]
    pub const fn raw_piece(self) -> Self {
        Self(self.0 & !Self::PIECE_PROMOTE)
    }

    /// 遠方駒かどうかを判定
    #[must_use]
    pub const fn has_long_effect(self) -> bool {
        matches!(
            self.piece_type(),
            PieceType::LANCE
                | PieceType::BISHOP
                | PieceType::ROOK
                | PieceType::HORSE
                | PieceType::DRAGON
        )
    }

    /// 有効な値かどうかを判定
    #[must_use]
    pub fn is_ok(self) -> bool {
        if self.0 == Self::NO_PIECE.0 {
            return true;
        }
        let pt = self.piece_type();
        pt.is_ok()
            && pt.0 != 0
            && self.0 >= 0
            && usize::try_from(self.0).map(|idx| idx < Self::PIECE_NB).unwrap_or(false)
    }

    /// 内部値を取得する（主にテスト用）
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }

    /// インデックス値に変換
    #[inline]
    #[must_use]
    #[allow(clippy::cast_sign_loss)]
    pub const fn to_index(self) -> usize {
        self.0 as usize
    }
}

impl fmt::Display for Piece {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if *self == Self::NO_PIECE {
            return write!(f, " ");
        }

        let piece_text = self.piece_type().to_string();
        let display = if self.color() == Color::WHITE {
            // 後手は小文字
            piece_text.to_lowercase()
        } else {
            // 先手は大文字
            piece_text
        };
        write!(f, "{display}")
    }
}

impl FromStr for Piece {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s == " " {
            return Ok(Self::NO_PIECE);
        }

        // 成駒の場合、最初の'+'を確認
        let (is_promoted, base_str) =
            s.strip_prefix('+').map_or((false, s), |stripped| (true, stripped));

        // 大文字小文字で先手後手を判定
        let is_white = base_str.chars().next().map_or(false, char::is_lowercase);
        let color = if is_white { Color::WHITE } else { Color::BLACK };

        // 大文字に変換してPieceTypeとしてパース
        let upper = base_str.to_uppercase();
        let pt_str = if is_promoted { format!("+{upper}") } else { upper };
        let piece_type = PieceType::from_str(&pt_str)?;

        Ok(Self::make(color, piece_type))
    }
}

/// 駒の手番を取得（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn color_of(piece: Piece) -> Color {
    piece.color()
}

/// 駒の駒種を取得（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn type_of(piece: Piece) -> PieceType {
    piece.piece_type()
}

/// 成りを外した駒種を取得（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn raw_type_of(piece: Piece) -> PieceType {
    piece.raw_piece_type()
}

/// 成りを外した駒を取得（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn raw_of(piece: Piece) -> Piece {
    piece.raw_piece()
}

/// 駒を生成（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn make_piece(color: Color, piece_type: PieceType) -> Piece {
    Piece::make(color, piece_type)
}

/// 成り駒を生成（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn make_promoted_piece(piece: Piece) -> Piece {
    Piece(piece.raw() | Piece::PIECE_PROMOTE)
}

/// 成り駒かどうかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn is_promoted(piece: Piece) -> bool {
    piece.is_promoted()
}

/// これ以上成れない駒かどうかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn is_non_promotable_piece(piece: Piece) -> bool {
    piece.is_non_promotable()
}

/// 遠方駒かどうかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn has_long_effect(piece: Piece) -> bool {
    piece.has_long_effect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_piece_type_constants() {
        // 非成駒
        assert_eq!(PieceType::NO_PIECE_TYPE.0, 0);
        assert_eq!(PieceType::PAWN.0, 1);
        assert_eq!(PieceType::LANCE.0, 2);
        assert_eq!(PieceType::KNIGHT.0, 3);
        assert_eq!(PieceType::SILVER.0, 4);
        assert_eq!(PieceType::BISHOP.0, 5);
        assert_eq!(PieceType::ROOK.0, 6);
        assert_eq!(PieceType::GOLD.0, 7);
        assert_eq!(PieceType::KING.0, 8);

        // 成駒
        assert_eq!(PieceType::PRO_PAWN.0, 9);
        assert_eq!(PieceType::PRO_LANCE.0, 10);
        assert_eq!(PieceType::PRO_KNIGHT.0, 11);
        assert_eq!(PieceType::PRO_SILVER.0, 12);
        assert_eq!(PieceType::HORSE.0, 13);
        assert_eq!(PieceType::DRAGON.0, 14);

        // その他定数
        assert_eq!(PieceType::PIECE_TYPE_PROMOTE, 8);
        assert_eq!(PieceType::PIECE_TYPE_NB, 16);
        assert_eq!(PieceType::PIECE_HAND_ZERO.0, 1);
        assert_eq!(PieceType::PIECE_HAND_NB, 8);
    }

    #[test]
    fn test_piece_type_promote() {
        // 成れる駒
        assert_eq!(PieceType::PAWN.promote(), PieceType::PRO_PAWN);
        assert_eq!(PieceType::LANCE.promote(), PieceType::PRO_LANCE);
        assert_eq!(PieceType::KNIGHT.promote(), PieceType::PRO_KNIGHT);
        assert_eq!(PieceType::SILVER.promote(), PieceType::PRO_SILVER);
        assert_eq!(PieceType::BISHOP.promote(), PieceType::HORSE);
        assert_eq!(PieceType::ROOK.promote(), PieceType::DRAGON);

        // 成れない駒
        assert_eq!(PieceType::GOLD.promote(), PieceType::GOLD);
        assert_eq!(PieceType::KING.promote(), PieceType::KING);

        // すでに成っている駒
        assert_eq!(PieceType::PRO_PAWN.promote(), PieceType::PRO_PAWN);
        assert_eq!(PieceType::HORSE.promote(), PieceType::HORSE);
    }

    #[test]
    fn test_piece_type_is_promotable() {
        assert!(PieceType::PAWN.is_promotable());
        assert!(PieceType::LANCE.is_promotable());
        assert!(PieceType::KNIGHT.is_promotable());
        assert!(PieceType::SILVER.is_promotable());
        assert!(PieceType::BISHOP.is_promotable());
        assert!(PieceType::ROOK.is_promotable());

        assert!(!PieceType::GOLD.is_promotable());
        assert!(!PieceType::KING.is_promotable());
        assert!(!PieceType::PRO_PAWN.is_promotable());
        assert!(!PieceType::HORSE.is_promotable());
    }

    #[test]
    fn test_piece_type_is_ok() {
        // 有効な値
        for i in 0..16 {
            assert!(PieceType(i).is_ok());
        }

        // 無効な値
        assert!(!PieceType(-1).is_ok());
        assert!(!PieceType(16).is_ok());
        assert!(!PieceType(100).is_ok());
    }

    #[test]
    fn test_piece_type_display_to_string() {
        let cases = [
            (PieceType::PAWN, "P"),
            (PieceType::LANCE, "L"),
            (PieceType::KNIGHT, "N"),
            (PieceType::SILVER, "S"),
            (PieceType::BISHOP, "B"),
            (PieceType::ROOK, "R"),
            (PieceType::GOLD, "G"),
            (PieceType::KING, "K"),
            (PieceType::PRO_PAWN, "+P"),
            (PieceType::PRO_LANCE, "+L"),
            (PieceType::PRO_KNIGHT, "+N"),
            (PieceType::PRO_SILVER, "+S"),
            (PieceType::HORSE, "+B"),
            (PieceType::DRAGON, "+R"),
        ];

        for (piece_type, expected) in cases {
            assert_eq!(piece_type.to_string(), expected);
        }
    }

    #[test]
    fn test_piece_type_display_round_trip() {
        let cases = [
            PieceType::PAWN,
            PieceType::LANCE,
            PieceType::KNIGHT,
            PieceType::SILVER,
            PieceType::BISHOP,
            PieceType::ROOK,
            PieceType::GOLD,
            PieceType::KING,
            PieceType::PRO_PAWN,
            PieceType::PRO_LANCE,
            PieceType::PRO_KNIGHT,
            PieceType::PRO_SILVER,
            PieceType::HORSE,
            PieceType::DRAGON,
        ];

        for pt in cases {
            let s = pt.to_string();
            let parsed = PieceType::from_str(&s).unwrap();
            assert_eq!(pt, parsed);
        }
    }

    #[test]
    fn test_piece_type_from_str_invalid() {
        for invalid in ["X", "", "++P"] {
            assert!(PieceType::from_str(invalid).is_err());
        }
    }

    #[test]
    fn test_piece_constants_black() {
        assert_eq!(Piece::B_PAWN.0, 1);
        assert_eq!(Piece::B_LANCE.0, 2);
        assert_eq!(Piece::B_KNIGHT.0, 3);
        assert_eq!(Piece::B_SILVER.0, 4);
        assert_eq!(Piece::B_BISHOP.0, 5);
        assert_eq!(Piece::B_ROOK.0, 6);
        assert_eq!(Piece::B_GOLD.0, 7);
        assert_eq!(Piece::B_KING.0, 8);
        assert_eq!(Piece::B_PRO_PAWN.0, 9);
        assert_eq!(Piece::B_PRO_LANCE.0, 10);
        assert_eq!(Piece::B_PRO_KNIGHT.0, 11);
        assert_eq!(Piece::B_PRO_SILVER.0, 12);
        assert_eq!(Piece::B_HORSE.0, 13);
        assert_eq!(Piece::B_DRAGON.0, 14);
    }

    #[test]
    fn test_piece_constants_white() {
        assert_eq!(Piece::W_PAWN.0, 17);
        assert_eq!(Piece::W_LANCE.0, 18);
        assert_eq!(Piece::W_KNIGHT.0, 19);
        assert_eq!(Piece::W_SILVER.0, 20);
        assert_eq!(Piece::W_BISHOP.0, 21);
        assert_eq!(Piece::W_ROOK.0, 22);
        assert_eq!(Piece::W_GOLD.0, 23);
        assert_eq!(Piece::W_KING.0, 24);
        assert_eq!(Piece::W_PRO_PAWN.0, 25);
        assert_eq!(Piece::W_PRO_LANCE.0, 26);
        assert_eq!(Piece::W_PRO_KNIGHT.0, 27);
        assert_eq!(Piece::W_PRO_SILVER.0, 28);
        assert_eq!(Piece::W_HORSE.0, 29);
        assert_eq!(Piece::W_DRAGON.0, 30);
    }

    #[test]
    fn test_piece_constant_flags() {
        assert_eq!(Piece::NO_PIECE.0, 0);
        assert_eq!(Piece::PIECE_WHITE, 16);
        assert_eq!(Piece::PIECE_PROMOTE, 8);
        assert_eq!(Piece::PIECE_NB, 32);
    }

    #[test]
    fn test_piece_make_and_decompose() {
        // make -> color/piece_type のround-trip
        for color in [Color::BLACK, Color::WHITE] {
            for pt in [
                PieceType::PAWN,
                PieceType::LANCE,
                PieceType::KNIGHT,
                PieceType::SILVER,
                PieceType::BISHOP,
                PieceType::ROOK,
                PieceType::GOLD,
                PieceType::KING,
                PieceType::PRO_PAWN,
                PieceType::HORSE,
            ] {
                let piece = Piece::make(color, pt);
                assert_eq!(piece.color(), color);
                assert_eq!(piece.piece_type(), pt);
            }
        }

        // 定数との一致確認
        assert_eq!(Piece::make(Color::BLACK, PieceType::PAWN), Piece::B_PAWN);
        assert_eq!(Piece::make(Color::WHITE, PieceType::PAWN), Piece::W_PAWN);
        assert_eq!(Piece::make(Color::BLACK, PieceType::KING), Piece::B_KING);
        assert_eq!(Piece::make(Color::WHITE, PieceType::KING), Piece::W_KING);
    }

    #[test]
    fn test_piece_promote() {
        // 成れる駒
        assert_eq!(Piece::B_PAWN.promote(), Piece::B_PRO_PAWN);
        assert_eq!(Piece::W_PAWN.promote(), Piece::W_PRO_PAWN);
        assert_eq!(Piece::B_BISHOP.promote(), Piece::B_HORSE);
        assert_eq!(Piece::W_ROOK.promote(), Piece::W_DRAGON);

        // 成れない駒
        assert_eq!(Piece::B_GOLD.promote(), Piece::B_GOLD);
        assert_eq!(Piece::W_KING.promote(), Piece::W_KING);

        // すでに成っている駒
        assert_eq!(Piece::B_PRO_PAWN.promote(), Piece::B_PRO_PAWN);
        assert_eq!(Piece::W_HORSE.promote(), Piece::W_HORSE);
    }

    #[test]
    fn test_piece_is_ok() {
        // 有効な駒
        assert!(Piece::NO_PIECE.is_ok());
        assert!(Piece::B_PAWN.is_ok());
        assert!(Piece::W_KING.is_ok());
        assert!(Piece::B_DRAGON.is_ok());
        assert!(Piece::W_DRAGON.is_ok());

        // 無効な駒
        assert!(!Piece(-1).is_ok());
        assert!(!Piece(32).is_ok()); // PIECE_NBと等しい
        assert!(!Piece(33).is_ok());
        assert!(!Piece(100).is_ok());

        // piece_type部分が0の場合（NO_PIECE以外）
        assert!(!Piece(16).is_ok()); // PIECE_WHITE only
    }

    #[test]
    fn test_piece_display_to_string() {
        let cases = [
            (Piece::NO_PIECE, " "),
            (Piece::B_PAWN, "P"),
            (Piece::B_LANCE, "L"),
            (Piece::B_KNIGHT, "N"),
            (Piece::B_SILVER, "S"),
            (Piece::B_BISHOP, "B"),
            (Piece::B_ROOK, "R"),
            (Piece::B_GOLD, "G"),
            (Piece::B_KING, "K"),
            (Piece::B_PRO_PAWN, "+P"),
            (Piece::B_HORSE, "+B"),
            (Piece::B_DRAGON, "+R"),
            (Piece::W_PAWN, "p"),
            (Piece::W_LANCE, "l"),
            (Piece::W_KNIGHT, "n"),
            (Piece::W_SILVER, "s"),
            (Piece::W_BISHOP, "b"),
            (Piece::W_ROOK, "r"),
            (Piece::W_GOLD, "g"),
            (Piece::W_KING, "k"),
            (Piece::W_PRO_PAWN, "+p"),
            (Piece::W_HORSE, "+b"),
            (Piece::W_DRAGON, "+r"),
        ];

        for (piece, expected) in cases {
            assert_eq!(piece.to_string(), expected);
        }
    }

    #[test]
    fn test_piece_display_round_trip() {
        let cases = [
            Piece::NO_PIECE,
            Piece::B_PAWN,
            Piece::W_PAWN,
            Piece::B_KING,
            Piece::W_KING,
            Piece::B_DRAGON,
            Piece::W_DRAGON,
        ];

        for piece in cases {
            let s = piece.to_string();
            let parsed = Piece::from_str(&s).unwrap();
            assert_eq!(piece, parsed);
        }
    }

    #[test]
    fn test_piece_display_from_str_invalid() {
        for invalid in ["X", ""] {
            assert!(Piece::from_str(invalid).is_err());
        }
    }
}
