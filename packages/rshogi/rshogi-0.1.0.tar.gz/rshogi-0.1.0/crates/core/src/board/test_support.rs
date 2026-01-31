use crate::board::Position;
use crate::types::{Move, Move16};

/// USI文字列から`Move`を生成する。
///
/// - 成功した場合は`Some(Move)`を返す。
/// - 解析に失敗した場合は`None`を返す。
#[must_use]
pub fn move_from_usi(pos: &Position, usi: &str) -> Option<Move> {
    let mv16 = Move16::from_usi(usi)?;

    if mv16.is_drop() {
        let piece_type = mv16.dropped_piece()?;
        Some(Move::make_drop(piece_type, mv16.to_sq(), pos.side_to_move()))
    } else {
        let from = mv16.from_sq();
        let to = mv16.to_sq();
        let piece = pos.piece_on(from);

        if mv16.is_promote() {
            Some(Move::make_promote(from, to, piece))
        } else {
            Some(Move::make(from, to, piece))
        }
    }
}

/// `move_from_usi` の `expect` 版。
#[must_use]
pub fn move_from_usi_expect(pos: &Position, usi: &str) -> Move {
    move_from_usi(pos, usi).unwrap_or_else(|| panic!("invalid USI move: {usi}"))
}

/// USI手を適用する。
///
/// - 適用した`Move`を返す。
pub fn apply_usi_move(pos: &mut Position, usi: &str) -> Move {
    let mv = move_from_usi(pos, usi).unwrap_or_else(|| panic!("invalid USI move: {usi}"));
    debug_assert!(pos.is_legal(mv), "apply_usi_move expects a legal move");
    pos.do_move(mv);
    mv
}

/// `apply_usi_move` の `expect` 版。
pub fn apply_usi_move_expect(pos: &mut Position, usi: &str) -> Move {
    apply_usi_move(pos, usi)
}

/// 指定したUSI手順を順に適用する。
pub fn play_sequence(pos: &mut Position, sequence: &[&str]) {
    for usi in sequence {
        apply_usi_move_expect(pos, usi);
    }
}
