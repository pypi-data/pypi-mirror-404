use super::*;

const fn is_promoted_piece(piece: Piece) -> bool {
    matches!(
        piece.piece_type(),
        PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER
            | PieceType::HORSE
            | PieceType::DRAGON
    )
}
use crate::types::{Color, File, Hand, Piece, PieceType, Rank, Square, SQ_51, SQ_55, SQ_59};

/// `PackedPiece` の基本的なエンコード・デコード動作を検証
#[test]
fn packed_piece_encoding_roundtrip() {
    assert_eq!(PackedPiece::EMPTY.0, 0);
    assert!(PackedPiece::EMPTY.is_empty());

    let black_pawn = PackedPiece::new(PieceType::PAWN, Color::BLACK, false);
    assert_eq!(black_pawn.piece_type(), PieceType::PAWN);
    assert_eq!(black_pawn.color(), Color::BLACK);
    assert!(!black_pawn.is_promoted());

    let white_pro_silver = PackedPiece::new(PieceType::SILVER, Color::WHITE, true);
    assert_eq!(white_pro_silver.piece_type(), PieceType::SILVER);
    assert_eq!(white_pro_silver.color(), Color::WHITE);
    assert!(white_pro_silver.is_promoted());

    let pieces = [
        Piece::B_PAWN,
        Piece::W_LANCE,
        Piece::B_KNIGHT,
        Piece::W_SILVER,
        Piece::B_GOLD,
        Piece::W_BISHOP,
        Piece::B_ROOK,
        Piece::W_KING,
    ];

    for piece in pieces {
        let packed = PackedPiece::from_piece(piece);
        let converted = packed.to_piece();
        assert_eq!(piece, converted);
    }
}

/// `BoardArray` が配列として正常に動作するかを確認
#[test]
fn board_array_behaves_like_81_square_buffer() {
    let mut board = BoardArray::empty();
    let black_king = PackedPiece::from_piece(Piece::B_KING);
    board.set(SQ_55, black_king);

    assert!(!board.get(SQ_55).is_empty());
    assert_eq!(board.get(SQ_55).piece_type(), PieceType::KING);

    let non_empty_count = board.iter().filter(|(_, p)| !p.is_empty()).count();
    assert_eq!(non_empty_count, 1);
}

/// `Position::new` と `from_startpos` の初期状態を検証
#[test]
fn position_basic_state_and_startpos() {
    let pos = Position::new();
    assert_eq!(pos.side_to_move(), Color::BLACK);
    assert_eq!(pos.game_ply(), 1);
    assert_eq!(pos.hand_of(Color::BLACK), Hand::HAND_ZERO);
    assert_eq!(pos.hand_of(Color::WHITE), Hand::HAND_ZERO);

    let start = crate::board::hirate_position();

    assert_eq!(start.piece_on(SQ_59).piece_type(), PieceType::KING);
    assert_eq!(start.piece_on(SQ_59).color(), Color::BLACK);
    assert_eq!(start.piece_on(SQ_51).piece_type(), PieceType::KING);
    assert_eq!(start.piece_on(SQ_51).color(), Color::WHITE);

    assert_eq!(start.side_to_move(), Color::BLACK);
    assert_eq!(start.game_ply(), 1);
}

/// SFEN との往復と最低限の局面検証が成立するかを確認
#[test]
fn position_sfen_roundtrip_and_validation() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

    let pos = crate::board::position_from_sfen(sfen).unwrap();
    let generated = pos.sfen(None);
    assert_eq!(sfen, generated);

    let mut invalid = Position::new();
    assert!(invalid.is_valid().is_ok());

    let black_king = PackedPiece::from_piece(Piece::B_KING);
    let white_king = PackedPiece::from_piece(Piece::W_KING);
    invalid.board.set(SQ_59, black_king);
    invalid.board.set(SQ_51, white_king);
    invalid.rebuild_bitboards();

    assert!(invalid.is_valid().is_ok());
}

/// `flipped_sfen` が盤面はそのままで先後反転することを確認
#[test]
fn position_flipped_sfen_matches_yaneuraou() {
    let sfen = "lnsgk1snl/1r4g2/p1ppppb1p/6pP1/7R1/2P6/P2PPPP1P/1SG6/LN2KGSNL b BP2p 21";
    let expected = "lnsgk2nl/6gs1/p1pppp2p/6p2/1r7/1pP6/P1BPPPP1P/2G4R1/LNS1KGSNL w 2Pbp 21";

    let pos = crate::board::position_from_sfen(sfen).unwrap();
    assert_eq!(pos.flipped_sfen(None), expected);
}

/// 通常手・捕獲・打ち・成り・不正手など `do_move` 派生の基本挙動を網羅
#[test]
fn do_move_variants() {
    let mut pos = crate::board::hirate_position();

    let from = Square::from_file_rank(File::FILE_7, Rank::RANK_7);
    let to = Square::from_file_rank(File::FILE_7, Rank::RANK_6);
    let piece = pos.piece_on(from);
    let mv = Move::make(from, to, piece);

    let initial_ply = pos.game_ply();
    pos.do_move(mv);
    assert_eq!(pos.piece_on(from), Piece::NO_PIECE);
    assert_eq!(pos.piece_on(to), piece);
    assert_eq!(pos.side_to_move(), Color::WHITE);
    assert_eq!(pos.game_ply(), initial_ply + 1);

    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/4p4/4P4/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    let mut capture_pos = crate::board::position_from_sfen(sfen).unwrap();

    let from = Square::from_file_rank(File::FILE_5, Rank::RANK_6);
    let to = Square::from_file_rank(File::FILE_5, Rank::RANK_5);
    let piece = capture_pos.piece_on(from);
    let captured = capture_pos.piece_on(to);
    let mv = Move::make(from, to, piece);
    capture_pos.do_move(mv);
    let state_stack = capture_pos.state_stack();
    let state = state_stack.current();
    assert_eq!(state.captured().map(PackedPiece::to_piece), Some(captured));
    assert_eq!(capture_pos.hand_of(Color::BLACK).pawn_count(), 1);

    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPP1PPPP/1B5R1/LNSGKGSNL b P 1";
    let mut drop_pos = crate::board::position_from_sfen(sfen).unwrap();
    let to = Square::from_file_rank(File::FILE_5, Rank::RANK_5);
    let mv = Move::make_drop(PieceType::PAWN, to, Color::BLACK);
    let initial_hand = drop_pos.hand_of(Color::BLACK);
    drop_pos.do_move(mv);
    let placed_piece = drop_pos.piece_on(to);
    assert_eq!(placed_piece, Piece::B_PAWN);
    assert_eq!(drop_pos.hand_of(Color::BLACK).pawn_count(), initial_hand.pawn_count() - 1);
    assert_eq!(drop_pos.state_stack().current().captured, PackedPiece::EMPTY);

    let sfen = "lnsgkgsnl/1r5b1/2R6/ppppppppp/9/9/PPPPPPPPP/1B7/LNSGKGSNL b - 1";
    let mut promote_pos = crate::board::position_from_sfen(sfen).unwrap();
    let from = Square::from_file_rank(File::FILE_7, Rank::RANK_3);
    let to = Square::from_file_rank(File::FILE_7, Rank::RANK_2);
    let piece = promote_pos.piece_on(from);
    let mv = Move::make_promote(from, to, piece);
    promote_pos.do_move(mv);
    assert!(is_promoted_piece(promote_pos.piece_on(to)));

    let invalid_move_pos = crate::board::hirate_position();

    let from = Square::from_file_rank(File::FILE_5, Rank::RANK_5);
    let to = Square::from_file_rank(File::FILE_5, Rank::RANK_4);
    let mv = Move::make(from, to, Piece::B_PAWN);
    assert!(!invalid_move_pos.is_legal(mv));

    let to = Square::from_file_rank(File::FILE_5, Rank::RANK_5);
    let mv = Move::make_drop(PieceType::PAWN, to, Color::BLACK);
    assert!(!invalid_move_pos.is_legal(mv));
}
