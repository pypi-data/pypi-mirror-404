use super::*;
use crate::board::MoveList;
use crate::types::{Move, PieceType, Square};
use std::str::FromStr;

#[test]
fn recaptures_exclude_drop_on_empty_target() {
    let sfen = "4k4/9/9/9/9/9/9/9/4K4 b P 1";
    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    let target = Square::from_str("5e").expect("valid square");

    let mut list = MoveList::new();
    generate_recaptures(&pos, target, &mut list);

    let expected = Move::make_drop(PieceType::PAWN, target, pos.side_to_move());
    assert!(
        !list.iter().any(|m| *m == expected),
        "recaptures should exclude pawn drop to empty target"
    );
}

#[test]
fn recaptures_include_pawn_promotion() {
    let sfen = "4k4/9/2P6/9/9/9/9/9/4K4 b - 1";
    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    let from = Square::from_str("7c").expect("valid square");
    let target = Square::from_str("7b").expect("valid square");

    let mut list = MoveList::new();
    generate_recaptures(&pos, target, &mut list);

    let piece = pos.piece_on(from);
    let promote = Move::make_promote(from, target, piece);

    assert!(list.iter().any(|m| *m == promote), "recaptures should include promotable pawn move");
}

#[test]
fn recaptures_all_include_pawn_non_promotion() {
    let sfen = "4k4/9/2P6/9/9/9/9/9/4K4 b - 1";
    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    let from = Square::from_str("7c").expect("valid square");
    let target = Square::from_str("7b").expect("valid square");

    let mut list = MoveList::new();
    generate_recaptures_all(&pos, target, &mut list);

    let piece = pos.piece_on(from);
    let unpromote = Move::make(from, target, piece);

    assert!(
        list.iter().any(|m| *m == unpromote),
        "recaptures_all should include non-promoted pawn move"
    );
}
