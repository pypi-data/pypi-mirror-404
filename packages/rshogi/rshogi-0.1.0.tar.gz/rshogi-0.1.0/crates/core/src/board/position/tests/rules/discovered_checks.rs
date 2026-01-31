use crate::board::test_support::move_from_usi_expect;

#[test]
fn gives_check_detects_discovered_check() {
    let pos =
        crate::board::position_from_sfen("4k4/9/9/9/9/9/4S4/9/4R3K b - 1").expect("valid SFEN");

    let mv = move_from_usi_expect(&pos, "5g4f");
    assert!(pos.gives_check(mv), "discovered check should be detected");

    let mut next = pos;
    next.init_stack();
    next.do_move(mv);
    assert!(!next.checkers().is_empty(), "move must give check on board");
}

#[test]
fn gives_check_does_not_trigger_when_still_aligned() {
    let pos =
        crate::board::position_from_sfen("4k4/9/9/9/9/9/4S4/9/4R3K b - 1").expect("valid SFEN");

    let mv = move_from_usi_expect(&pos, "5g5f");
    assert!(!pos.gives_check(mv), "moving along the line must not be a discovered check");

    let mut next = pos;
    next.init_stack();
    next.do_move(mv);
    assert!(next.checkers().is_empty(), "move must not give check on board");
}
