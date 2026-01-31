use super::*;
use crate::types::square::SQ_55;

#[test]
fn attackers_to_startpos_is_empty() {
    let pos = crate::board::hirate_position();
    let occupied = pos.bitboards().occupied();

    // 初期局面で5五を攻撃している駒はいない
    let attackers = pos.attackers_to(SQ_55, occupied);
    assert!(attackers.is_empty());
}

#[test]
fn square_not_attacked_in_startpos() {
    let pos = crate::board::hirate_position();

    // 初期局面で5五は攻撃されていない
    assert!(!pos.is_attacked_by(SQ_55, Color::BLACK));
    assert!(!pos.is_attacked_by(SQ_55, Color::WHITE));
}
