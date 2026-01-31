use crate::types::{MOVE_NONE, MOVE_WIN};

#[test]
fn declaration_win_succeeds_for_black() {
    let sfen = "K+N5+L1/G+L+P+B1+R+P2/3+P2G2/9/2+p+n5/3s2+ss1/3+p+p1+s1+r/7g+n/6g+nk b 2L8Pb4p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_WIN, "black meets declaration win requirements");
}

#[test]
fn declaration_win_fails_on_insufficient_points() {
    let sfen = "K+N5+L1/G+L+P+B1+R+P2/3+P2G2/9/2+p+n5/3s2+ss1/3+p+p1+s1+r/7g+n/6g+nk b 2L7Pb5p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_NONE, "insufficient points should fail");
}

#[test]
fn declaration_win_fails_when_king_outside_enemy_camp() {
    let sfen =
        "1+N2+P2+L1/G1+P+B1+R+P2/1+L1+P5/K8/2+p+n5/3s2+ss1/3+p+p1+s1+r/7g+n/6g+nk b G2L7Pb4p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_NONE, "king outside enemy camp should fail");
}

#[test]
fn declaration_win_fails_on_insufficient_enemy_camp_pieces() {
    let sfen = "K+N5+L1/G+L+P+B1+R+P2/3+P5/9/2+p+n5/3s2+ss1/3+p+p1+s1+r/7g+n/6g+nk b G2L8Pb4p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_NONE, "insufficient enemy camp pieces should fail");
}

#[test]
fn declaration_win_fails_while_in_check() {
    let sfen =
        "K+N5+L1/G1+P+B1+R+P2/+P+L1+P2G2/9/2+p+n5/3s2+ss1/3+p+p1b1+r/6+sg+n/6g+nk b 2L7P4p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_NONE, "cannot declare while in check");
}

#[test]
fn declaration_win_succeeds_for_white() {
    let sfen = "K+N5+L1/G+P+P+B1+R+P2/+P+L1+P2G2/9/9/9/6b1+r/4+ss+sg+n/5+pg+nk w 2L5Psn7p 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    pos.set_ekr(crate::types::EnteringKingRule::Point27);

    assert_eq!(pos.declaration_win(), MOVE_WIN, "white meets declaration win requirements");
}
