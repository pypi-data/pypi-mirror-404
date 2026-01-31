use proptest::prelude::*;

use rshogi_core::board::{self, generate_moves, MoveList, NonEvasionsAll};

proptest! {
    #[test]
    fn generated_move_sequences_do_not_panic_on_apply(seq in proptest::collection::vec(any::<u8>(), 0..24)) {
        let mut pos = board::hirate_position();
        let mut history = Vec::new();

        for byte in seq {
            let mut moves = MoveList::new();
            generate_moves::<NonEvasionsAll>(&pos, &mut moves);

            if moves.is_empty() {
                break;
            }

            let legal: Vec<_> = moves.iter().copied().filter(|&mv| pos.is_legal(mv)).collect();
            if legal.is_empty() {
                break;
            }
            let idx = (byte as usize) % legal.len();
            let mv = legal[idx];
            pos.do_move(mv);
            history.push(mv);
        }

        while let Some(mv) = history.pop() {
            pos.undo_move(mv).expect("generated move must be undoable");
        }

        // `undo_move` restores the root Zobrist; ensure stack head is back at root.
        prop_assert_eq!(pos.state_stack().current().prev, None);
    }
}
