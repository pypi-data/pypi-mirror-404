//! 局面履歴管理のための `StateInfo` 実装

use super::position::{PackedPiece, Ply, Position};
use crate::board::eval_list::DirtyEvalPiece;
use crate::board::material;
use crate::board::zobrist::ZobristKey;
use crate::types::Bitboard;
use crate::types::{Color, Hand, Move, PieceType, RepetitionState};
use std::collections::VecDeque;

/// `StateInfo` 内でのスタック位置を表す型
pub type StateIndex = u16;

/// 探索の最大深さ（YaneuraOu互換: config.h の MAX_PLY_NUM）
pub const MAX_STATE_PLY: usize = 246;

/// 局面の履歴情報を保持する構造体
///
/// `do_move` 時の差分情報を記録し、`undo_move` で完全に復元できるようにする。
/// また、千日手検出や王手情報のキャッシュも管理する。
#[derive(Clone, Debug, Default)]
pub struct StateInfo {
    /// 直前局面のスタック位置（ルート局面ならNone）
    pub prev: Option<StateIndex>,

    /// 取られた駒（なければ `PackedPiece::EMPTY` ）
    pub captured: PackedPiece,

    /// 盤面Zobrist（board_key）
    pub board_key: ZobristKey,

    /// 持ち駒Zobrist（hand_key）
    pub hand_key: ZobristKey,

    /// 歩Zobrist（pawn_key）
    pub pawn_key: ZobristKey,

    /// 小駒Zobrist（minor_piece_key）
    pub minor_piece_key: ZobristKey,

    /// 歩以外Zobrist（non_pawn_key）
    pub non_pawn_key: [ZobristKey; Color::COLOR_NB],

    /// 駒割Zobrist（material_key）
    pub material_key: ZobristKey,

    /// 同一局面の登場回数（千日手検出用）
    pub repetition_counter: i32,

    /// 同一局面までの距離（千日手検出用、YaneuraOu互換）
    /// 4回目以降の繰り返しは負の値で表す。
    pub repetition_distance: i32,

    /// 同一局面の繰り返し回数 - 1（YaneuraOu互換）
    pub repetition_times: i32,

    /// null moveからの手数
    pub plies_from_null: Ply,

    /// 王手をかけている駒の集合（高速化のためキャッシュ）
    pub checkers: Bitboard,

    /// 色別にピンしている敵の大駒（YaneuraOu互換）
    pub pinners: [Bitboard; Color::COLOR_NB],

    /// 色別の玉を守っているブロッカー集合
    pub blockers_for_king: [Bitboard; Color::COLOR_NB],

    /// 各駒種について、その駒を配置すると敵玉に王手となるマスのビットボード
    /// YaneuraOu互換: MovePicker の check bonus 計算に使用
    pub check_squares: [Bitboard; PieceType::PIECE_TYPE_NB],

    /// 連続王手カウンタ（[先手, 後手]）
    /// 王手でない手を指すと0にリセットされる
    pub continuous_check: [u16; 2],

    /// EvalList差分更新用のdirty eval piece
    pub dirty_eval_piece: DirtyEvalPiece,

    /// 現局面の手番側の持ち駒（YaneuraOu互換）
    pub hand: Hand,

    /// 千日手の状態（キャッシュ用）
    pub repetition_type: RepetitionState,

    /// 駒割り評価値（先手視点、YaneuraOu互換）
    pub material_value: i32,

    /// 直前の指し手（YaneuraOu互換）
    pub last_move: Move,

    /// 直前に動かした駒種（YaneuraOu互換）
    pub last_moved_piece_type: PieceType,

}

impl StateInfo {
    /// 新しい空の `StateInfo` を作成
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// 探索開始時のリセット（ゼロクリア）
    pub fn reset(&mut self) {
        *self = Self::default();
    }

    /// 捕獲された駒を取得
    #[must_use]
    pub fn captured(&self) -> Option<PackedPiece> {
        if self.captured == PackedPiece::EMPTY {
            None
        } else {
            Some(self.captured)
        }
    }
}

/// 可変長の `StateInfo` スタック
///
/// YaneuraOu の `StateList` に合わせて動的に拡張する。
#[derive(Debug)]
pub struct StateStack {
    /// `StateInfo` のリスト
    entries: VecDeque<StateInfo>,

    /// 現在のスタックトップのインデックス
    head: StateIndex,
}

impl StateStack {
    /// 新しい `StateStack` を作成
    #[must_use]
    pub fn new() -> Self {
        let mut entries = VecDeque::with_capacity(MAX_STATE_PLY);
        entries.push_back(StateInfo::default());
        Self { entries, head: 0 }
    }

    /// 探索開始時のリセット（headを0に戻すだけで内容はクリアしない）
    pub fn reset(&mut self) {
        self.head = 0;
        self.entries.truncate(1);
        self.entries[0].reset();
    }

    /// 局面に同期した初期StateInfoを設定する
    pub fn reset_with_position(&mut self, pos: &mut Position) {
        self.reset();
        let state = self.current_mut();
        state.board_key = pos.board_key;
        state.hand_key = pos.hand_key;
        state.pawn_key = pos.pawn_key;
        state.minor_piece_key = pos.minor_piece_key;
        state.non_pawn_key = pos.non_pawn_key;
        state.material_key = pos.material_key;
        state.dirty_eval_piece = DirtyEvalPiece::default();
        state.material_value = material::material_value(pos);
        pos.compute_caches_for_state(state);
        state.hand = pos.hands[pos.side_to_move.to_index()];
        pos.sync_caches_from_state(state);
    }

    /// 現在の（最新の）`StateInfo` への参照を取得
    #[must_use]
    pub fn current(&self) -> &StateInfo {
        &self.entries[self.head as usize]
    }

    /// 現在の`StateInfo`のインデックスを取得
    #[must_use]
    pub const fn current_index(&self) -> StateIndex {
        self.head
    }

    /// 現在の（最新の）`StateInfo` への可変参照を取得
    pub fn current_mut(&mut self) -> &mut StateInfo {
        &mut self.entries[self.head as usize]
    }

    /// 新しい空の `StateInfo` をプッシュし、そのインデックスを返す
    /// 呼び出し側で内容を埋める責任がある
    pub fn push_empty(&mut self) -> StateIndex {
        assert!(
            (self.head as usize) < MAX_STATE_PLY - 1,
            "StateStack overflow: exceeded MAX_STATE_PLY"
        );

        let prev_index = self.head;
        self.head += 1;
        let head = self.head as usize;

        if head == self.entries.len() {
            self.entries.push_back(StateInfo::default());
        }

        let entry = &mut self.entries[head];
        entry.reset();
        entry.prev = Some(prev_index);

        self.head
    }

    /// 現在の`StateInfo`を複製して新しいエントリをプッシュする
    ///
    /// YaneuraOu の do_move 相当の memcpy 動作に合わせるために用いる。
    pub fn push_clone_from_prev(&mut self) -> StateIndex {
        assert!(
            (self.head as usize) < MAX_STATE_PLY - 1,
            "StateStack overflow: exceeded MAX_STATE_PLY"
        );

        let prev_index = self.head;
        self.head += 1;
        let head = self.head as usize;

        let prev_entry = self.entries[prev_index as usize].clone();
        if head == self.entries.len() {
            self.entries.push_back(prev_entry);
        } else {
            self.entries[head] = prev_entry;
        }
        self.entries[head].prev = Some(prev_index);

        self.head
    }

    /// do_move 用に、必要なフィールドだけをコピーして新しいエントリをプッシュする
    ///
    /// YaneuraOu の do_move でコピーされる範囲に合わせて最小限のフィールドを引き継ぐ。
    pub fn push_for_move(&mut self) -> StateIndex {
        assert!(
            (self.head as usize) < MAX_STATE_PLY - 1,
            "StateStack overflow: exceeded MAX_STATE_PLY"
        );

        let prev_index = self.head;
        self.head += 1;
        let head = self.head as usize;

        let prev_entry = self.entries[prev_index as usize].clone();
        let new_entry = StateInfo {
            prev: Some(prev_index),
            material_key: prev_entry.material_key,
            pawn_key: prev_entry.pawn_key,
            minor_piece_key: prev_entry.minor_piece_key,
            non_pawn_key: prev_entry.non_pawn_key,
            plies_from_null: prev_entry.plies_from_null,
            continuous_check: prev_entry.continuous_check,
            ..StateInfo::default()
        };

        if head == self.entries.len() {
            self.entries.push_back(new_entry);
        } else {
            self.entries[head] = new_entry;
        }

        self.head
    }

    /// スタックをポップし、ポップしたエントリのインデックスを返す
    /// スタックが空（ルート局面のみ）の場合はNone
    pub fn pop(&mut self) -> Option<StateIndex> {
        if self.head == 0 {
            return None;
        }

        let popped = self.head;
        let prev_idx = self.entries[popped as usize].prev.unwrap_or(0);
        self.head = prev_idx;
        Some(popped)
    }

    /// 指定インデックスの `StateInfo` への参照を取得
    #[must_use]
    pub fn get(&self, idx: StateIndex) -> &StateInfo {
        &self.entries[idx as usize]
    }

    /// 指定インデックスの `StateInfo` への可変参照を取得
    pub fn get_mut(&mut self, idx: StateIndex) -> &mut StateInfo {
        &mut self.entries[idx as usize]
    }

    /// 現在の深さ（スタックに積まれている `StateInfo` の数）を取得
    #[must_use]
    pub const fn depth(&self) -> usize {
        self.head as usize
    }
}

impl Clone for StateStack {
    fn clone(&self) -> Self {
        Self { entries: self.entries.clone(), head: self.head }
    }
}

impl Default for StateStack {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests;
