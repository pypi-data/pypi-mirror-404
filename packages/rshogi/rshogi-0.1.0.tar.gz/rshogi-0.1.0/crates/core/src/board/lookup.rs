use crate::types::{Bitboard, Square};
use std::convert::TryFrom;
use std::sync::OnceLock;

const BETWEEN_BB_SIZE: usize = 785;

struct BetweenTables {
    index: [[u16; Square::SQ_NB_PLUS1]; Square::SQ_NB_PLUS1],
    bb: [Bitboard; BETWEEN_BB_SIZE],
}

struct LineTables {
    bb: [[Bitboard; 4]; Square::SQ_NB],
}

static BETWEEN_TABLE: OnceLock<BetweenTables> = OnceLock::new();
static LINE_TABLE: OnceLock<LineTables> = OnceLock::new();

fn build_between_table() -> BetweenTables {
    let mut index = [[0u16; Square::SQ_NB_PLUS1]; Square::SQ_NB_PLUS1];
    let mut bb = [Bitboard::EMPTY; BETWEEN_BB_SIZE];
    let mut between_index: u16 = 1;

    for (s1, row) in index.iter_mut().enumerate().take(Square::SQ_NB) {
        for (s2, entry) in row.iter_mut().enumerate().take(Square::SQ_NB) {
            if s1 >= s2 {
                continue;
            }
            let sq1 = Square(i8::try_from(s1).expect("square index fits in i8"));
            let sq2 = Square(i8::try_from(s2).expect("square index fits in i8"));
            let Some(delta) = between_delta(sq1, sq2) else {
                continue;
            };
            let mut line = Bitboard::EMPTY;
            let mut sq = sq1;
            loop {
                sq = Square(sq.0 + delta);
                if sq == sq2 {
                    break;
                }
                line.set(sq);
            }
            if line.is_empty() {
                continue;
            }
            let idx = usize::from(between_index);
            *entry = between_index;
            bb[idx] = line;
            between_index += 1;
        }
    }

    debug_assert_eq!(usize::from(between_index), BETWEEN_BB_SIZE, "BetweenBB size mismatch");

    for s1 in 0..Square::SQ_NB {
        for s2 in 0..Square::SQ_NB {
            if s1 > s2 {
                index[s1][s2] = index[s2][s1];
            }
        }
    }

    BetweenTables { index, bb }
}

fn build_line_table() -> LineTables {
    let mut bb = [[Bitboard::EMPTY; 4]; Square::SQ_NB];
    for (s1, row) in bb.iter_mut().enumerate().take(Square::SQ_NB) {
        let sq1 = Square(i8::try_from(s1).expect("square index fits in i8"));
        row[0] = line_from_delta(sq1, -1, -1);
        row[1] = line_from_delta(sq1, -1, 0);
        row[2] = line_from_delta(sq1, -1, 1);
        row[3] = line_from_delta(sq1, 0, -1);
    }
    LineTables { bb }
}

#[inline]
fn between_table() -> &'static BetweenTables {
    BETWEEN_TABLE.get_or_init(build_between_table)
}

#[inline]
fn line_table() -> &'static LineTables {
    LINE_TABLE.get_or_init(build_line_table)
}

fn between_delta(from: Square, to: Square) -> Option<i8> {
    if from == to {
        return None;
    }
    let from_file = from.0 / 9;
    let from_rank = from.0 % 9;
    let to_file = to.0 / 9;
    let to_rank = to.0 % 9;

    let file_diff = to_file - from_file;
    let rank_diff = to_rank - from_rank;

    if file_diff == 0 {
        return Some(rank_diff.signum());
    }
    if rank_diff == 0 {
        return Some(file_diff.signum() * 9);
    }
    if file_diff.abs() == rank_diff.abs() {
        return Some(file_diff.signum() * 9 + rank_diff.signum());
    }
    None
}

fn line_from_delta(sq: Square, file_step: i8, rank_step: i8) -> Bitboard {
    let mut line = Bitboard::EMPTY;
    line.set(sq);

    for sign in [-1, 1] {
        let mut file = sq.0 / 9;
        let mut rank = sq.0 % 9;
        loop {
            file += file_step * sign;
            rank += rank_step * sign;
            if !(0..9).contains(&file) || !(0..9).contains(&rank) {
                break;
            }
            let idx = file * 9 + rank;
            line.set(Square(idx));
        }
    }

    line
}

const fn line_direction_index(from: Square, to: Square) -> Option<usize> {
    let from_file = from.0 / 9;
    let from_rank = from.0 % 9;
    let to_file = to.0 / 9;
    let to_rank = to.0 % 9;

    let file_diff = to_file - from_file;
    let rank_diff = to_rank - from_rank;

    if file_diff == 0 {
        return Some(3);
    }
    if rank_diff == 0 {
        return Some(1);
    }
    if file_diff == rank_diff || file_diff == -rank_diff {
        let same_sign = (file_diff > 0 && rank_diff > 0) || (file_diff < 0 && rank_diff < 0);
        return Some(if same_sign { 0 } else { 2 });
    }
    None
}

#[inline]
pub(super) fn between(from: Square, to: Square) -> Bitboard {
    let tables = between_table();
    tables.bb[usize::from(tables.index[from.to_index()][to.to_index()])]
}

#[inline]
pub(super) fn line(sq1: Square, sq2: Square) -> Bitboard {
    if sq1 == sq2 {
        return Bitboard::from_square(sq1);
    }
    let Some(dir) = line_direction_index(sq1, sq2) else {
        return Bitboard::EMPTY;
    };
    line_table().bb[sq1.to_index()][dir]
}

pub(super) fn init_lookup_tables() {
    let _ = between_table();
    let _ = line_table();
}

impl Bitboard {
    /// 2つのマスの間のマスを表すビットボードを取得（端点は含まない）
    #[must_use]
    pub fn between(from: Square, to: Square) -> Self {
        debug_assert!(from.is_ok(), "Invalid square: {from:?}");
        debug_assert!(to.is_ok(), "Invalid square: {to:?}");
        between(from, to)
    }

    /// 2つのマスを結ぶ直線上の全マスを返す（両端含む）
    ///
    /// # Arguments
    /// * `sq1` - マス1
    /// * `sq2` - マス2
    ///
    /// # Returns
    /// 2つのマスが同じ直線上（縦・横・斜め）にある場合、その直線上の全マスのBitboard
    /// そうでない場合は空のBitboard
    #[must_use]
    pub fn line(sq1: Square, sq2: Square) -> Self {
        debug_assert!(sq1.is_ok(), "Invalid square: {sq1:?}");
        debug_assert!(sq2.is_ok(), "Invalid square: {sq2:?}");
        line(sq1, sq2)
    }

    /// `between`/`line` テーブルを事前計算する（YaneuraOu互換の初期化パス用）
    pub fn init_tables() {
        init_lookup_tables();
    }
}
