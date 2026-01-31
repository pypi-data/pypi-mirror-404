use super::Position;
use crate::types::{Bitboard, Color, HandPiece, Move, Piece, PieceType, Rank};

impl Position {
    /// 指し手がpseudo-legalかどうかを判定する（自殺手チェックは含まない）。
    #[must_use]
    #[allow(clippy::too_many_lines)]
    pub fn pseudo_legal(&self, m: Move, generate_all_legal_moves: bool) -> bool {
        let us = self.side_to_move();
        let to = m.to_sq();

        if m.is_drop() {
            let Some(piece_type) = m.dropped_piece() else {
                return false;
            };
            if m.moved_after_piece() != Piece::make(us, piece_type) {
                return false;
            }
            let hand_piece = HandPiece::from_piece_type(piece_type)
                .expect("dropped piece must map to hand piece");
            if self.piece_on(to) != Piece::NO_PIECE {
                return false;
            }
            if self.hands[us.to_index()].count(hand_piece) == 0 {
                return false;
            }

            let checkers = self.checkers();
            if !checkers.is_empty() {
                let mut checkers_bb = checkers;
                let checker_sq = checkers_bb.pop_lsb().expect("checker exists");
                if !checkers_bb.is_empty() {
                    return false;
                }
                let king_sq = self.king_square(us);
                if !Bitboard::between(checker_sq, king_sq).test(to) {
                    return false;
                }
            }

            if piece_type == PieceType::PAWN && !self.legal_pawn_drop(us, to) {
                return false;
            }

            return true;
        }

        let from = m.from_sq();
        let piece = self.piece_on(from);
        if piece == Piece::NO_PIECE || piece.color() != us {
            return false;
        }

        let occupied = self.bitboards().occupied();
        if !Self::piece_attacks(piece.piece_type(), from, us, occupied).test(to) {
            return false;
        }

        if self.bitboards().color_pieces(us).test(to) {
            return false;
        }
        let pt = piece.piece_type();
        if m.is_promote() {
            if !pt.is_promotable() {
                return false;
            }
            if m.moved_after_piece() != piece.promote() {
                return false;
            }
        } else {
            if m.moved_after_piece() != piece {
                return false;
            }
            if pt == PieceType::NO_PIECE_TYPE {
                return false;
            }
            if generate_all_legal_moves {
                if (pt == PieceType::PAWN || pt == PieceType::LANCE)
                    && ((us == Color::BLACK && to.rank() == Rank::RANK_1)
                        || (us == Color::WHITE && to.rank() == Rank::RANK_9))
                {
                    return false;
                }
            } else {
                match pt {
                    PieceType::PAWN => {
                        let enemy_territory = match us {
                            Color::BLACK => {
                                Bitboard::rank_mask(Rank::RANK_1)
                                    | Bitboard::rank_mask(Rank::RANK_2)
                                    | Bitboard::rank_mask(Rank::RANK_3)
                            }
                            Color::WHITE => {
                                Bitboard::rank_mask(Rank::RANK_7)
                                    | Bitboard::rank_mask(Rank::RANK_8)
                                    | Bitboard::rank_mask(Rank::RANK_9)
                            }
                            _ => Bitboard::EMPTY,
                        };
                        if enemy_territory.test(to) {
                            return false;
                        }
                    }
                    PieceType::LANCE => {
                        if (us == Color::BLACK && to.rank() <= Rank::RANK_2)
                            || (us == Color::WHITE && to.rank() >= Rank::RANK_8)
                        {
                            return false;
                        }
                    }
                    PieceType::BISHOP | PieceType::ROOK => {
                        if Self::can_promote(from, to, us) {
                            return false;
                        }
                    }
                    _ => {}
                }
            }
        }

        let checkers = self.checkers();
        if !checkers.is_empty() && pt != PieceType::KING {
            if checkers.count() > 1 {
                return false;
            }
            let king_sq = self.king_square(us);
            let checker_sq = checkers.lsb().expect("single checker exists");
            let target =
                Bitboard::between(checker_sq, king_sq).or(Bitboard::from_square(checker_sq));
            if !target.test(to) {
                return false;
            }
        }

        true
    }
}
