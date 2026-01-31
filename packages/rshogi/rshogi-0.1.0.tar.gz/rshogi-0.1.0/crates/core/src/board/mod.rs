//! 盤面表現と状態管理

pub mod attack_tables;
pub mod bona;
pub mod bitboard_pair;
pub mod bitboard_set;
pub mod eval_list;
pub mod material;
pub mod piece_list;
pub mod move_list;
pub mod movegen;
pub mod perft;
mod parser;
mod lookup;
pub mod zobrist;
pub mod position;
pub mod state_info;
pub mod mate_constant;
pub mod test_support;

pub use crate::mate;
pub use crate::types::Bitboard;
pub use attack_tables::{GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS, PAWN_ATTACKS, SILVER_ATTACKS};
pub use bitboard_pair::{Bitboard256, BitboardPair};
pub use bitboard_set::BitboardSet;
pub use mate::solve_mate_in_one;
pub use move_list::{ExtMove, ExtMoveList, MoveList};
pub use movegen::{
    generate_moves, generate_quiet_checks, generate_recaptures, generate_recaptures_all,
    CapturePlusPro, CapturePlusProAll, Captures, CapturesAll, Checks, ChecksAll, Evasions,
    EvasionsAll, Legal, LegalAll, MoveGenType, NonEvasions, NonEvasionsAll, QuietChecks,
    QuietChecksAll, Quiets, QuietsAll, QuietsProMinus, QuietsProMinusAll, Recaptures,
    RecapturesAll,
};
pub use piece_list::PieceList;
pub use position::{BoardArray, PackedPiece, PackedSfen, PackedSfenError, Ply, Position};
pub use state_info::{StateIndex, StateInfo, StateStack};
#[cfg(test)]
mod tests;

/// 盤面関連の事前計算を行う（YaneuraOu互換の初期化パス用）
pub fn init() {
    Bitboard::init_tables();
}

/// SFEN文字列から局面を構築する（ヘルパー）。
pub fn position_from_sfen(sfen: &str) -> Result<Position, parser::SfenError> {
    let mut pos = Position::new();
    pos.set(sfen)?;
    Ok(pos)
}

/// 平手初期局面を構築する（ヘルパー）。
#[must_use]
pub fn hirate_position() -> Position {
    let mut pos = Position::new();
    pos.set_hirate();
    pos
}
