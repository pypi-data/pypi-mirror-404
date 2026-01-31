use super::Position;
use crate::board::bona::{BonaPiece, KPP_HAND_INDEX};
use crate::board::eval_list::{PieceNumber, PIECE_NUMBER_NB};
use crate::types::{Color, PieceType, Square};

impl Position {
    pub(super) fn bona_piece_of(&self, color: Color, piece_type: PieceType) -> Option<BonaPiece> {
        let hand_piece = crate::types::HandPiece::from_piece_type(piece_type)?;
        let count = self.hands[color.to_index()].count(hand_piece);
        debug_assert!(
            count > 0,
            "bona_piece_of expects a hand piece: color={color:?} piece_type={piece_type:?}"
        );
        if count == 0 {
            return None;
        }
        let base = KPP_HAND_INDEX[color.to_index()][piece_type.to_index()].fb;
        let offset = i32::try_from(count - 1).expect("hand count fits in i32");
        Some(base + offset)
    }

    pub(super) fn piece_no_of_hand(&self, color: Color, piece_type: PieceType) -> PieceNumber {
        let Some(bona) = self.bona_piece_of(color, piece_type) else {
            return PIECE_NUMBER_NB;
        };
        self.eval_list.piece_no_of_hand(bona)
    }

    pub(super) fn piece_no_of_square(&self, sq: Square) -> PieceNumber {
        debug_assert!(
            !self.board.get(sq).is_empty(),
            "piece_no_of_square expects occupied square: {sq:?}"
        );
        let piece_no = self.eval_list.piece_no_of_board(sq);
        debug_assert!(
            piece_no != PIECE_NUMBER_NB,
            "piece_no_of_square expects valid piece number: {sq:?}"
        );
        piece_no
    }
}
