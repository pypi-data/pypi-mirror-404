//! 将棋盤面の管理

mod accessors;
mod attacks;
mod cache;
mod constructors;
mod eval_list;
mod legality;
mod maintenance;
mod packed_sfen;
mod parser;
mod rules;
pub mod see;
mod types;
mod updates;
mod hash;
mod validation;

use super::bitboard_set::BitboardSet;
use super::eval_list::EvalList;
use super::piece_list::PieceList;
use crate::board::zobrist::ZobristKey;
use crate::board::StateIndex;
use crate::types::Bitboard;
use crate::types::{Color, EnteringKingRule, File, Hand, Piece, PieceType, Rank, Square};
use std::cell::RefCell;
use std::fmt;

use crate::board::StateStack;
#[cfg(test)]
use crate::types::Move;

pub use super::parser::{MissingFieldKind, SfenError};
pub use packed_sfen::{PackedSfen, PackedSfenError};
pub use see::{piece_value, see, see_ge};
pub(super) use types::MINOR_PIECE_TYPES;
pub use types::{BoardArray, MoveError, PackedPiece, Ply, ValidationError};

/// 将棋の盤面状態を管理する構造体
///
/// キャッシュ効率のため、頻繁にアクセスされるデータを先頭に配置
#[repr(C, align(64))]
#[derive(Clone)]
pub struct Position {
    /// `PackedPiece` を81要素並べた盤面
    pub(super) board: BoardArray,

    /// 駒種別・先後別のビットボード集合
    pub(super) bitboards: BitboardSet,

    /// 持ち駒カウント配列
    pub(super) hands: [Hand; Color::COLOR_NB],

    /// 現局面のZobristハッシュ
    pub(super) zobrist: ZobristKey,

    /// 盤面ハッシュ（手番込み）
    pub(super) board_key: ZobristKey,

    /// 持ち駒ハッシュ
    pub(super) hand_key: ZobristKey,

    /// 歩の盤面ハッシュ
    pub(super) pawn_key: ZobristKey,

    /// 小駒（香桂銀金と成り駒）の盤面ハッシュ
    pub(super) minor_piece_key: ZobristKey,

    /// 歩以外の盤面ハッシュ（色別）
    pub(super) non_pawn_key: [ZobristKey; Color::COLOR_NB],

    /// 駒割ハッシュ
    pub(super) material_key: ZobristKey,

    /// 手番
    pub(super) side_to_move: Color,

    /// 入玉ルール設定
    pub(super) entering_king_rule: EnteringKingRule,

    /// 入玉判定に必要な駒点
    pub(super) entering_king_point: [i32; Color::COLOR_NB],

    /// USIで定義される手数（1から始まる）
    pub(super) ply: Ply,

    /// 現局面に対応するStateInfoのインデックス
    pub(super) st_index: StateIndex,

    /// 局面履歴（YaneuraOu互換のStateList）
    pub(super) state_stack: RefCell<StateStack>,

    /// 玉の位置（色別）
    pub(super) king_square: [Square; Color::COLOR_NB],

    /// 現局面で自玉に王手している駒集合（手番側の玉）
    pub(super) checkers_cache: Bitboard,

    /// 各駒種について、その駒を配置すると敵玉に王手となるマスのビットボード
    pub(super) check_squares_cache: [Bitboard; PieceType::PIECE_TYPE_NB],

    /// 各色の玉に対してピンしている敵の大駒集合
    pub(super) pinners_cache: [Bitboard; Color::COLOR_NB],

    /// 各色の玉を守っているブロッカー集合
    pub(super) blockers_for_king: [Bitboard; Color::COLOR_NB],

    /// 駒種ごとの駒位置リスト（NNUE高速化用）
    pub(super) piece_list: PieceList,

    /// EvalList（USE_EVAL_LIST互換）
    pub(super) eval_list: EvalList,

    /// 現在の手で変化した駒（NNUE差分更新用）
    /// パディング（アライメント調整）
    pub(super) _padding: [u8; 5],
}

impl Default for Position {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // 盤面を表示
        writeln!(f, "  9 8 7 6 5 4 3 2 1")?;
        writeln!(f, "+-------------------+")?;

        for rank_idx in 0..9 {
            let rank_value = i8::try_from(rank_idx).expect("rank index within range");
            let rank = Rank::new(rank_value);
            write!(f, "|")?;
            for file_idx in (0..9).rev() {
                let file_value = i8::try_from(file_idx).expect("file index within range");
                let sq = Square::from_file_rank(File::new(file_value), rank);
                let piece = self.piece_on(sq);

                if piece == Piece::NO_PIECE {
                    write!(f, " .")?;
                } else {
                    // 簡易表示（実際はもっと詳細な表示が必要）
                    write!(f, " *")?;
                }
            }
            let rank_char =
                char::from(b'a' + u8::try_from(rank_idx).expect("rank index fits in u8"));
            writeln!(f, "|{rank_char}")?;
        }

        writeln!(f, "+-------------------+")?;
        writeln!(f, "Side to move: {:?}", self.side_to_move)?;
        writeln!(f, "Ply: {}", self.ply)?;

        Ok(())
    }
}

impl Position {
    /// `StateStack` への参照を取得
    #[must_use]
    pub fn state_stack(&self) -> std::cell::Ref<'_, StateStack> {
        self.state_stack.borrow()
    }

    /// `StateStack` への可変参照を取得
    pub fn state_stack_mut(&self) -> std::cell::RefMut<'_, StateStack> {
        self.state_stack.borrow_mut()
    }
}

/// 盤面の整合性を確認する（YaneuraOu互換）。
#[must_use]
pub fn is_ok(pos: &Position) -> bool {
    pos.pos_is_ok()
}

#[cfg(test)]
mod tests;
