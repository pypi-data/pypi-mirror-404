use criterion::{criterion_group, criterion_main, BatchSize, Criterion};
use rshogi_core::board;
use rshogi_core::types::{Move, PieceType, Square};

fn bench_do_move(c: &mut Criterion) {
    c.bench_function("do_move_startpos", |b| {
        b.iter_batched(
            board::hirate_position,
            |mut pos| {
                let from = Square::from_usi("7g").unwrap();
                let to = Square::from_usi("7f").unwrap();
                let piece = pos.piece_on(from);
                let mv = Move::make(from, to, piece);
                pos.do_move(mv);
            },
            BatchSize::SmallInput,
        );
    });
}

fn bench_do_and_undo(c: &mut Criterion) {
    c.bench_function("do_undo_drop", |b| {
        b.iter_batched(
            || {
                let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b P 1";
                board::position_from_sfen(sfen).unwrap()
            },
            |mut pos| {
                let to = Square::from_usi("5e").unwrap();
                let mv = Move::make_drop(PieceType::PAWN, to, pos.side_to_move());
                pos.do_move(mv);
                pos.undo_move(mv).unwrap();
            },
            BatchSize::SmallInput,
        );
    });
}

criterion_group!(core_benches, bench_do_move, bench_do_and_undo);
criterion_main!(core_benches);
