use super::types::BoardArray;
use super::Position;
use crate::board::bitboard_set::BitboardSet;
use crate::board::material;
use crate::board::piece_list::PieceList;
use crate::board::state_info::StateStack;
use crate::board::zobrist::ZobristKey;
use crate::types::{Bitboard, Color, EnteringKingRule, Hand, PieceType, Square};

impl Position {
    /// 新しい空の盤面を作成
    #[must_use]
    pub fn new() -> Self {
        Self {
            board: BoardArray::empty(),
            bitboards: BitboardSet::new(),
            hands: [Hand::HAND_ZERO; Color::COLOR_NB],
            zobrist: ZobristKey::default(),
            board_key: ZobristKey::default(),
            hand_key: ZobristKey::default(),
            pawn_key: crate::board::zobrist::Zobrist::no_pawns(),
            minor_piece_key: ZobristKey::default(),
            non_pawn_key: [ZobristKey::default(); Color::COLOR_NB],
            material_key: ZobristKey::default(),
            side_to_move: Color::BLACK,
            entering_king_rule: EnteringKingRule::None,
            entering_king_point: [0, 0],
            ply: 1,
            st_index: 0,
            state_stack: std::cell::RefCell::new(StateStack::new()),
            king_square: [Square::SQ_NONE; Color::COLOR_NB],
            checkers_cache: Bitboard::EMPTY,
            check_squares_cache: [Bitboard::EMPTY; PieceType::PIECE_TYPE_NB],
            pinners_cache: [Bitboard::EMPTY; Color::COLOR_NB],
            blockers_for_king: [Bitboard::EMPTY; Color::COLOR_NB],
            piece_list: PieceList::new(),
            eval_list: crate::board::eval_list::EvalList::new(),
            _padding: [0; 5],
        }
    }

    /// スタックを初期化する（探索開始時などに使用）
    pub fn init_stack(&mut self) {
        let state_snapshot = {
            let mut stack = self.state_stack_mut();
            stack.reset();
            let state = stack.current_mut();
            state.board_key = self.board_key;
            state.hand_key = self.hand_key;
            state.pawn_key = self.pawn_key;
            state.minor_piece_key = self.minor_piece_key;
            state.non_pawn_key = self.non_pawn_key;
            state.material_key = self.material_key;
            state.dirty_eval_piece = crate::board::eval_list::DirtyEvalPiece::default();
            state.material_value = material::material_value(self);
            self.compute_caches_for_state(state);
            state.hand = self.hands[self.side_to_move.to_index()];
            state.clone()
        };

        self.sync_caches_from_state(&state_snapshot);
        let st_index = {
            let stack = self.state_stack();
            stack.current_index()
        };
        self.st_index = st_index;
    }
}
