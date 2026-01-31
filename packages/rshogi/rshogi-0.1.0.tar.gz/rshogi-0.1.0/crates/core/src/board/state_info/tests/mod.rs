use super::*;
use crate::board::test_support::move_from_usi_expect;
use crate::types::{Color, Hand, PieceType, MOVE_NONE};

#[allow(clippy::cognitive_complexity)]
fn assert_state_info_matches(actual: &StateInfo, expected: &StateInfo) {
    assert_eq!(actual.board_key, expected.board_key);
    assert_eq!(actual.hand_key, expected.hand_key);
    assert_eq!(actual.pawn_key, expected.pawn_key);
    assert_eq!(actual.minor_piece_key, expected.minor_piece_key);
    assert_eq!(actual.non_pawn_key, expected.non_pawn_key);
    assert_eq!(actual.material_key, expected.material_key);
    assert_eq!(actual.material_value, expected.material_value);
    assert_eq!(actual.checkers, expected.checkers);
    assert_eq!(actual.pinners, expected.pinners);
    assert_eq!(actual.blockers_for_king, expected.blockers_for_king);
    assert_eq!(actual.check_squares, expected.check_squares);
    assert_eq!(actual.continuous_check, expected.continuous_check);
    assert_eq!(actual.dirty_eval_piece, expected.dirty_eval_piece);
    assert_eq!(actual.repetition_counter, expected.repetition_counter);
    assert_eq!(actual.repetition_distance, expected.repetition_distance);
    assert_eq!(actual.repetition_times, expected.repetition_times);
    assert_eq!(actual.plies_from_null, expected.plies_from_null);
    assert_eq!(actual.hand, expected.hand);
    assert_eq!(actual.repetition_type, expected.repetition_type);
    assert_eq!(actual.last_move, expected.last_move);
    assert_eq!(actual.last_moved_piece_type, expected.last_moved_piece_type);
}

#[test]
#[allow(clippy::cognitive_complexity)]
fn test_state_info_default() {
    let info = StateInfo::default();
    assert_eq!(info.prev, None);
    assert_eq!(info.captured, PackedPiece::EMPTY);
    assert_eq!(info.board_key, ZobristKey::default());
    assert_eq!(info.hand_key, ZobristKey::default());
    assert_eq!(info.pawn_key, ZobristKey::default());
    assert_eq!(info.minor_piece_key, ZobristKey::default());
    assert_eq!(info.non_pawn_key, [ZobristKey::default(); Color::COLOR_NB]);
    assert_eq!(info.material_key, ZobristKey::default());
    assert_eq!(info.material_value, 0);
    assert_eq!(info.repetition_counter, 0);
    assert_eq!(info.repetition_distance, 0);
    assert_eq!(info.repetition_times, 0);
    assert_eq!(info.plies_from_null, 0);
    assert_eq!(info.checkers, Bitboard::EMPTY);
    assert_eq!(info.pinners, [Bitboard::EMPTY; Color::COLOR_NB]);
    assert_eq!(info.blockers_for_king, [Bitboard::EMPTY; Color::COLOR_NB]);
    assert_eq!(info.check_squares, [Bitboard::EMPTY; PieceType::PIECE_TYPE_NB]);
    // 連続王手カウンタのデフォルト値確認
    assert_eq!(info.continuous_check, [0u16, 0u16]);
    assert_eq!(info.dirty_eval_piece, crate::board::eval_list::DirtyEvalPiece::default());
    assert_eq!(info.hand, Hand::HAND_ZERO);
    // 千日手状態のデフォルト値確認
    assert_eq!(info.repetition_type, RepetitionState::None);
    assert_eq!(info.last_move, MOVE_NONE);
    assert_eq!(info.last_moved_piece_type, PieceType::NO_PIECE_TYPE);
}

#[test]
fn test_state_stack_new() {
    let stack = StateStack::new();
    assert_eq!(stack.depth(), 0);
    assert_eq!(stack.current().prev, None);
}

#[test]
fn test_state_stack_push_pop() {
    let mut stack = StateStack::new();

    // 初期状態
    assert_eq!(stack.depth(), 0);

    // プッシュ
    let idx1 = stack.push_empty();
    assert_eq!(idx1, 1);
    assert_eq!(stack.depth(), 1);
    assert_eq!(stack.current().prev, Some(0));

    // さらにプッシュ
    let idx2 = stack.push_empty();
    assert_eq!(idx2, 2);
    assert_eq!(stack.depth(), 2);
    assert_eq!(stack.current().prev, Some(1));

    // ポップ
    let popped = stack.pop();
    assert_eq!(popped, Some(2));
    assert_eq!(stack.depth(), 1);

    // もう一度ポップ
    let popped = stack.pop();
    assert_eq!(popped, Some(1));
    assert_eq!(stack.depth(), 0);

    // 空の状態でポップ
    let popped = stack.pop();
    assert_eq!(popped, None);
}

#[test]
fn test_state_stack_reset() {
    let mut stack = StateStack::new();

    // いくつかプッシュ
    stack.push_empty();
    stack.push_empty();
    stack.push_empty();
    assert_eq!(stack.depth(), 3);

    // リセット
    stack.reset();
    assert_eq!(stack.depth(), 0);
    assert_eq!(stack.current().prev, None);
}

#[test]
fn state_stack_reset_with_position_matches_init_stack() {
    let mut stack_from_reset = StateStack::new();
    let mut pos = crate::board::hirate_position();

    pos.init_stack();
    stack_from_reset.reset_with_position(&mut pos);

    let init_state = pos.state_stack().current().clone();
    let reset_state = stack_from_reset.current();
    assert_state_info_matches(reset_state, &init_state);
}

#[test]
fn state_stack_apply_and_undo_restore_state() {
    let mut pos = crate::board::hirate_position();
    pos.init_stack();

    let initial = pos.state_stack().current().clone();
    let mv = move_from_usi_expect(&pos, "7g7f");
    pos.do_move(mv);
    pos.undo_move(mv).expect("undo move");

    let stack = pos.state_stack();
    let restored = stack.current();
    assert_state_info_matches(restored, &initial);
}

#[test]
fn state_info_records_captured_piece() {
    let sfen = "ln1g3nl/1r3kg2/p2pppsp1/3s2p1p/1pp4P1/P1P1SP2P/1PSPP1P2/2GK3R1/LN3G1NL b Bb 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.init_stack();

    let mv = move_from_usi_expect(&pos, "7f7e");
    pos.do_move(mv);

    let captured = pos.state_stack().current().captured().expect("captured piece");
    assert_eq!(captured.to_piece().color(), Color::WHITE);
}

#[test]
fn test_state_stack_get_mut() {
    let mut stack = StateStack::new();

    // プッシュして値を設定
    let idx = stack.push_empty();
    {
        let entry = stack.get_mut(idx);
        entry.repetition_counter = 3;
        entry.plies_from_null = 10;
    }

    // 取得して確認
    let entry = stack.get(idx);
    assert_eq!(entry.repetition_counter, 3);
    assert_eq!(entry.plies_from_null, 10);
}

#[test]
fn test_state_stack_reuse_memory() {
    let mut stack = StateStack::new();

    // 深くプッシュ
    for _ in 0..10 {
        stack.push_empty();
    }

    // 特定の値を設定
    stack.current_mut().repetition_counter = 42;

    // リセット
    stack.reset();

    // 再度プッシュ（メモリは再利用される）
    for _ in 0..10 {
        stack.push_empty();
    }

    // 前の値が残っている可能性があるが、それは仕様
    // （reset時に全クリアしないため）
    // 重要なのは正しくprev chainが構築されること
    assert_eq!(stack.depth(), 10);
    assert_eq!(stack.current().prev, Some(9));
}

#[test]
#[should_panic(expected = "StateStack overflow")]
fn test_state_stack_overflow() {
    let mut stack = StateStack::new();

    // MAX_STATE_PLYまでプッシュ
    for _ in 0..MAX_STATE_PLY {
        stack.push_empty();
    }

    // オーバーフローでパニック
    stack.push_empty();
}

#[test]
fn test_continuous_check_counter() {
    let mut info = StateInfo::default();

    // 初期値は両者とも0
    assert_eq!(info.continuous_check[Color::BLACK.to_index()], 0u16);
    assert_eq!(info.continuous_check[Color::WHITE.to_index()], 0u16);

    // 連続王手カウンタを更新
    info.continuous_check[Color::BLACK.to_index()] = 2u16;
    assert_eq!(info.continuous_check[Color::BLACK.to_index()], 2u16);
    assert_eq!(info.continuous_check[Color::WHITE.to_index()], 0u16);

    // リセット
    info.reset();
    assert_eq!(info.continuous_check[Color::BLACK.to_index()], 0u16);
    assert_eq!(info.continuous_check[Color::WHITE.to_index()], 0u16);
}

#[test]
fn test_repetition_type_field() {
    let mut info = StateInfo::default();

    // 初期値はNone
    assert_eq!(info.repetition_type, RepetitionState::None);

    // 千日手状態を更新
    info.repetition_type = RepetitionState::Win;
    assert_eq!(info.repetition_type, RepetitionState::Win);

    info.repetition_type = RepetitionState::Draw;
    assert_eq!(info.repetition_type, RepetitionState::Draw);

    // リセット
    info.reset();
    assert_eq!(info.repetition_type, RepetitionState::None);
}
