use std::env;

use rshogi_core::board::test_support::move_from_usi;
use rshogi_core::board::zobrist::ZobristKey;
use rshogi_core::board::{material, position_from_sfen};

fn format_key(key: ZobristKey) -> String {
    format!("{}:{}", key.high_u64(), key.low_u64())
}

fn main() {
    let mut sfen = None;
    let mut moves_arg = None;

    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--sfen" => {
                sfen = args.next();
            }
            "--moves" => {
                moves_arg = args.next();
            }
            _ => {
                eprintln!("Unknown argument: {arg}");
                std::process::exit(2);
            }
        }
    }

    let sfen = sfen.unwrap_or_else(|| {
        eprintln!("--sfen is required");
        std::process::exit(2);
    });

    let mut pos = position_from_sfen(&sfen).expect("valid sfen");
    pos.init_stack();

    if let Some(moves_arg) = moves_arg {
        for token in moves_arg.split_whitespace() {
            let mv = move_from_usi(&pos, token).unwrap_or_else(|| {
                eprintln!("Invalid USI move: {token}");
                std::process::exit(3);
            });
            if !pos.is_legal(mv) {
                eprintln!("Illegal move for position: {token}");
                std::process::exit(3);
            }
            pos.do_move(mv);
        }
    }

    let stack = pos.state_stack();
    let st = stack.current();

    let board_key = format_key(st.board_key);
    let hand_key = format_key(st.hand_key);
    let pawn_key = format_key(st.pawn_key);
    let minor_piece_key = format_key(st.minor_piece_key);
    let non_pawn_key_b = format_key(st.non_pawn_key[0]);
    let non_pawn_key_w = format_key(st.non_pawn_key[1]);
    let material_key = format_key(st.material_key);
    let key = format_key(st.board_key ^ st.hand_key);

    println!(
        "board_key={board_key} hand_key={hand_key} pawnKey={pawn_key} minorPieceKey={minor_piece_key} \
nonPawnKeyB={non_pawn_key_b} nonPawnKeyW={non_pawn_key_w} materialKey={material_key} key={key} \
materialValue={}",
        material::material_value(&pos)
    );
}
