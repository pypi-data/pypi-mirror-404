use super::types::ValidationError;
use super::Position;
use crate::types::{Bitboard, Color, File, HandPiece, PieceType, Rank, Square};

impl Position {
    /// 盤面の妥当性を検証（デバッグ向け）
    ///
    /// 将棋のルールに従って盤面が正しいかをチェックする。
    /// 駒落ち・詰将棋局面を想定し、玉の欠落は許容する。
    /// 以下の項目を検証：
    /// - 王の枚数（各色0〜1枚）
    /// - 二歩のチェック
    /// - 持ち駒の上限
    /// - 成り駒の位置の妥当性
    /// - 歩・香・桂の配置制限
    #[allow(clippy::too_many_lines)]
    pub fn is_valid(&self) -> Result<(), ValidationError> {
        // 1. 王の枚数チェック
        let black_king_count = self.bitboards.pieces_of(PieceType::KING, Color::BLACK).count();
        let white_king_count = self.bitboards.pieces_of(PieceType::KING, Color::WHITE).count();

        if black_king_count > 1 {
            return Err(ValidationError::TwoKings(Color::BLACK));
        }
        if white_king_count > 1 {
            return Err(ValidationError::TwoKings(Color::WHITE));
        }

        // 2. 二歩チェック
        for file in 0..9 {
            let file = File::new(file);
            let file_mask = Bitboard::file_mask(file);

            // 先手の歩
            let black_pawns = self.bitboards.pieces_of(PieceType::PAWN, Color::BLACK) & file_mask;
            if black_pawns.count() > 1 {
                return Err(ValidationError::DoublePawn(file, Color::BLACK));
            }

            // 後手の歩
            let white_pawns = self.bitboards.pieces_of(PieceType::PAWN, Color::WHITE) & file_mask;
            if white_pawns.count() > 1 {
                return Err(ValidationError::DoublePawn(file, Color::WHITE));
            }
        }

        // 3. 持ち駒の上限チェック
        for color in [Color::BLACK, Color::WHITE] {
            let hand = &self.hands[color.to_index()];

            // 各駒種の最大枚数をチェック
            if hand.count(HandPiece::HAND_PAWN) > 18 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_PAWN,
                    count: hand.count(HandPiece::HAND_PAWN),
                });
            }
            if hand.count(HandPiece::HAND_LANCE) > 4 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_LANCE,
                    count: hand.count(HandPiece::HAND_LANCE),
                });
            }
            if hand.count(HandPiece::HAND_KNIGHT) > 4 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_KNIGHT,
                    count: hand.count(HandPiece::HAND_KNIGHT),
                });
            }
            if hand.count(HandPiece::HAND_SILVER) > 4 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_SILVER,
                    count: hand.count(HandPiece::HAND_SILVER),
                });
            }
            if hand.count(HandPiece::HAND_GOLD) > 4 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_GOLD,
                    count: hand.count(HandPiece::HAND_GOLD),
                });
            }
            if hand.count(HandPiece::HAND_BISHOP) > 2 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_BISHOP,
                    count: hand.count(HandPiece::HAND_BISHOP),
                });
            }
            if hand.count(HandPiece::HAND_ROOK) > 2 {
                return Err(ValidationError::InvalidHandCount {
                    piece: HandPiece::HAND_ROOK,
                    count: hand.count(HandPiece::HAND_ROOK),
                });
            }
        }

        // 4. 行き所のない駒の配置制限チェック
        for sq_idx in 0..81 {
            let sq = Square::new(sq_idx);
            let piece_packed = self.board.get(sq);

            if piece_packed.is_empty() {
                continue;
            }

            let color = piece_packed.color();
            let piece_type = piece_packed.piece_type();
            let rank = sq.rank();

            // 成り駒の位置チェック
            // 注: 成り駒がどこにいても、それ自体は合法。
            // なぜなら、成った後に移動してきた可能性があるため。
            // 静的な局面検証では「成れない位置で成った」を検出できない。

            // 歩と香の最奥段チェック（未成のまま配置は不正）
            // 先手の歩/香が1段目、後手の歩/香が9段目は不正
            if (piece_type == PieceType::PAWN || piece_type == PieceType::LANCE)
                && ((color == Color::BLACK && rank == Rank::RANK_1)
                    || (color == Color::WHITE && rank == Rank::RANK_9))
            {
                return Err(ValidationError::InvalidPlacement(sq, piece_type));
            }

            // 桂馬の奥2段チェック（未成のまま配置は不正）
            // 先手の桂馬が1-2段目、後手の桂馬が8-9段目は不正
            if piece_type == PieceType::KNIGHT
                && ((color == Color::BLACK && (rank == Rank::RANK_1 || rank == Rank::RANK_2))
                    || (color == Color::WHITE && (rank == Rank::RANK_8 || rank == Rank::RANK_9)))
            {
                return Err(ValidationError::InvalidPlacement(sq, piece_type));
            }
        }

        Ok(())
    }

    /// 内部状態の整合性チェック（YaneuraOu互換）
    #[must_use]
    pub fn pos_is_ok(&self) -> bool {
        self.is_valid().is_ok()
    }

    /// PieceListとboard配列の整合性をアサートする（デバッグビルドのみ）
    ///
    /// # Panics
    ///
    /// `PieceList`の内容が`board`配列と一致しない場合にパニック
    #[cfg(debug_assertions)]
    pub fn assert_piece_list_consistency(&self) {
        use crate::types::{Color, PieceType};

        for color in [Color::BLACK, Color::WHITE] {
            for pt in 0..PieceType::PIECE_TYPE_NB {
                #[allow(clippy::cast_possible_truncation)]
                let piece_type = PieceType::new(pt as i8);
                if piece_type == PieceType::NO_PIECE_TYPE {
                    continue;
                }

                let pieces = self.piece_list.pieces(color, piece_type);
                for &sq in pieces {
                    let packed_piece = self.board.get(sq);

                    // PackedPieceから実際のPieceに変換して駒種を取得
                    // to_piece()は成りフラグを考慮して正しい駒種を返す
                    let piece_on_board = packed_piece.to_piece();
                    assert_eq!(
                        piece_on_board.color(),
                        color,
                        "PieceListの駒の色がboard配列と一致しません: {color:?} {piece_type:?} at {sq:?}, packed={packed_piece:?}"
                    );
                    assert_eq!(
                        piece_on_board.piece_type(),
                        piece_type,
                        "PieceListの駒種がboard配列と一致しません: {color:?} {piece_type:?} at {sq:?}, board has {:?}, packed={:?}",
                        piece_on_board.piece_type(),
                        packed_piece
                    );
                }
            }
        }
    }
}
