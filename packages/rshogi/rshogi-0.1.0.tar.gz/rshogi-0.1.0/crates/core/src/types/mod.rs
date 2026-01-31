// types module - 将棋エンジンの基本型定義

pub mod color;
pub mod bitboard;
pub mod file;
pub mod hand;
pub mod moves;
pub mod piece;
pub mod rank;
pub mod repetition_state;
pub mod entering_king_rule;
pub mod square;

// 主要な型を再エクスポート
pub use bitboard::Bitboard;
pub use color::Color;
pub use entering_king_rule::EnteringKingRule;
pub use file::File;
pub use hand::{Hand, HandPiece, HAND_BIT_MASK, HAND_BORROW_MASK};
pub use moves::{
    Move, Move16, MOVE16_DROP_MASK, MOVE16_NONE, MOVE16_NULL, MOVE16_PROMOTE_MASK, MOVE16_RESIGN,
    MOVE16_WIN, MOVE_NONE, MOVE_NULL, MOVE_RESIGN, MOVE_WIN,
};
pub use piece::{Piece, PieceType};
pub use rank::Rank;
pub use repetition_state::RepetitionState;
pub use square::{
    Square, SQUARE_NB, SQ_11, SQ_12, SQ_13, SQ_14, SQ_15, SQ_16, SQ_17, SQ_18, SQ_19, SQ_21, SQ_22,
    SQ_23, SQ_24, SQ_25, SQ_26, SQ_27, SQ_28, SQ_29, SQ_31, SQ_32, SQ_33, SQ_34, SQ_35, SQ_36,
    SQ_37, SQ_38, SQ_39, SQ_41, SQ_42, SQ_43, SQ_44, SQ_45, SQ_46, SQ_47, SQ_48, SQ_49, SQ_51,
    SQ_52, SQ_53, SQ_54, SQ_55, SQ_56, SQ_57, SQ_58, SQ_59, SQ_61, SQ_62, SQ_63, SQ_64, SQ_65,
    SQ_66, SQ_67, SQ_68, SQ_69, SQ_71, SQ_72, SQ_73, SQ_74, SQ_75, SQ_76, SQ_77, SQ_78, SQ_79,
    SQ_81, SQ_82, SQ_83, SQ_84, SQ_85, SQ_86, SQ_87, SQ_88, SQ_89, SQ_91, SQ_92, SQ_93, SQ_94,
    SQ_95, SQ_96, SQ_97, SQ_98, SQ_99, SQ_D, SQ_L, SQ_LD, SQ_LU, SQ_NB, SQ_NB_PLUS1, SQ_NONE, SQ_R,
    SQ_RD, SQ_RU, SQ_U, SQ_ZERO,
};
