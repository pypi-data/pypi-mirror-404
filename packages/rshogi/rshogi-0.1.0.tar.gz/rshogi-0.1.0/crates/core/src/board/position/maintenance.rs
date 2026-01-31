use super::Position;
use crate::board::bitboard_set::BitboardSet;
use crate::board::eval_list::{
    EvalList, PIECE_NUMBER_BISHOP, PIECE_NUMBER_BKING, PIECE_NUMBER_GOLD, PIECE_NUMBER_KNIGHT,
    PIECE_NUMBER_LANCE, PIECE_NUMBER_NB, PIECE_NUMBER_PAWN, PIECE_NUMBER_ROOK, PIECE_NUMBER_SILVER,
    PIECE_NUMBER_WKING,
};
use crate::board::piece_list::PieceList;
use crate::types::{Color, HandPiece, Move, Move16, Piece, PieceType, Square, MOVE_NONE};

impl Position {
    /// 置換表や定跡から取り出した `Move16` を盤面依存の `Move` に拡張
    #[must_use]
    pub fn to_move(&self, mv16: Move16) -> Move {
        if !mv16.is_ok() {
            return Move(u32::from(mv16.0));
        }

        if mv16.is_drop() {
            let Some(piece_type) = mv16.dropped_piece() else {
                return MOVE_NONE;
            };
            return Move::make_drop(piece_type, mv16.to_sq(), self.side_to_move());
        }

        let from = mv16.from_sq();
        let to = mv16.to_sq();
        let piece = self.piece_on(from);
        if piece == Piece::NO_PIECE || piece.color() != self.side_to_move() {
            return MOVE_NONE;
        }

        if mv16.is_promote() {
            if !piece.piece_type().is_promotable() {
                return MOVE_NONE;
            }
            return Move::make_promote(from, to, piece);
        }

        Move::make(from, to, piece)
    }

    /// ビットボードを盤面配列から再構築
    pub(in crate::board) fn rebuild_bitboards(&mut self) {
        self.bitboards = BitboardSet::new();
        self.king_square = [Square::SQ_NONE; Color::COLOR_NB];

        for (sq, packed) in self.board.iter() {
            if !packed.is_empty() {
                // PackedPiece::to_piece()で成駒を正しく復元
                let piece = packed.to_piece();
                let piece_type = piece.piece_type();
                let color = piece.color();
                self.bitboards.set_piece(sq, piece_type, color);
                if piece_type == PieceType::KING {
                    self.king_square[color.to_index()] = sq;
                }
            }
        }

        self.recompute_caches();
    }

    /// `PieceList` を盤面から再構築
    ///
    /// SFEN読み込み後やデバッグ時に使用
    pub(in crate::board) fn rebuild_piece_list(&mut self) {
        self.piece_list = PieceList::new();

        for (sq, packed) in self.board.iter() {
            if !packed.is_empty() {
                let piece = packed.to_piece();
                let piece_type = piece.piece_type();
                let color = piece.color();
                self.piece_list.add_piece(color, piece_type, sq);
            }
        }
    }

    /// `EvalList` を盤面と持ち駒から再構築
    pub(in crate::board) fn rebuild_eval_list(&mut self) {
        let mut eval_list = EvalList::new();
        eval_list.clear();

        let mut piece_no_count = [PIECE_NUMBER_NB; PieceType::PIECE_TYPE_NB];
        piece_no_count[PieceType::PAWN.to_index()] = PIECE_NUMBER_PAWN;
        piece_no_count[PieceType::LANCE.to_index()] = PIECE_NUMBER_LANCE;
        piece_no_count[PieceType::KNIGHT.to_index()] = PIECE_NUMBER_KNIGHT;
        piece_no_count[PieceType::SILVER.to_index()] = PIECE_NUMBER_SILVER;
        piece_no_count[PieceType::GOLD.to_index()] = PIECE_NUMBER_GOLD;
        piece_no_count[PieceType::BISHOP.to_index()] = PIECE_NUMBER_BISHOP;
        piece_no_count[PieceType::ROOK.to_index()] = PIECE_NUMBER_ROOK;

        for (sq, packed) in self.board.iter() {
            if packed.is_empty() {
                continue;
            }
            let piece = packed.to_piece();
            let pt = piece.piece_type().demote();
            let idx = pt.to_index();
            let piece_no = match piece {
                Piece::B_KING => PIECE_NUMBER_BKING,
                Piece::W_KING => PIECE_NUMBER_WKING,
                _ => {
                    let current = piece_no_count[idx];
                    piece_no_count[idx] = current + 1;
                    current
                }
            };
            eval_list.put_piece_on_board(piece_no, sq, piece);
        }

        for &color in &[Color::BLACK, Color::WHITE] {
            let hand = self.hands[color.to_index()];
            for hp_raw in 0..HandPiece::HAND_NB {
                let hand_piece =
                    HandPiece(i8::try_from(hp_raw).expect("hand piece index fits in i8"));
                let piece_type = hand_piece.into_piece_type();
                let count = hand.count(hand_piece);
                let idx = piece_type.to_index();
                for i in 0..count {
                    let current = piece_no_count[idx];
                    piece_no_count[idx] = current + 1;
                    eval_list.put_piece_on_hand(current, color, piece_type, i as usize);
                }
            }
        }

        self.eval_list = eval_list;
    }
}
