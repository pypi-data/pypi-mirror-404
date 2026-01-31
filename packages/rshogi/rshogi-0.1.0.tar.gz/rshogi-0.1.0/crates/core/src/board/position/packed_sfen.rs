use super::{Ply, Position};
use crate::board::material;
use crate::board::parser::generate_sfen;
use crate::board::position::BoardArray;
use crate::types::{Color, EnteringKingRule, Hand, HandPiece, Piece, PieceType, Square};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct PackedSfen {
    pub data: [u8; 32],
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PackedSfenError {
    InvalidCursor,
    InvalidPieceCode,
}

struct BitWriter<'a> {
    data: &'a mut [u8; 32],
    cursor: usize,
}

impl<'a> BitWriter<'a> {
    fn new(data: &'a mut [u8; 32]) -> Self {
        Self { data, cursor: 0 }
    }

    fn write_one_bit(&mut self, bit: bool) {
        if bit {
            let idx = self.cursor / 8;
            let offset = self.cursor & 7;
            self.data[idx] |= 1 << offset;
        }
        self.cursor += 1;
    }

    fn write_n_bits(&mut self, value: u16, bits: u8) {
        for i in 0..bits {
            let bit = (value >> i) & 1;
            self.write_one_bit(bit != 0);
        }
    }

    const fn cursor(&self) -> usize {
        self.cursor
    }
}

struct BitReader<'a> {
    data: &'a [u8; 32],
    cursor: usize,
}

impl<'a> BitReader<'a> {
    const fn new(data: &'a [u8; 32]) -> Self {
        Self { data, cursor: 0 }
    }

    fn read_one_bit(&mut self) -> Result<bool, PackedSfenError> {
        if self.cursor >= 256 {
            return Err(PackedSfenError::InvalidCursor);
        }
        let idx = self.cursor / 8;
        let offset = self.cursor & 7;
        let bit = (self.data[idx] >> offset) & 1;
        self.cursor += 1;
        Ok(bit != 0)
    }

    fn read_n_bits(&mut self, bits: u8) -> Result<u16, PackedSfenError> {
        let mut value = 0u16;
        for i in 0..bits {
            if self.read_one_bit()? {
                value |= 1 << i;
            }
        }
        Ok(value)
    }

    const fn cursor(&self) -> usize {
        self.cursor
    }
}

#[derive(Clone, Copy)]
struct HuffmanPiece {
    code: u8,
    bits: u8,
}

const HUFFMAN_TABLE: [HuffmanPiece; 8] = [
    HuffmanPiece { code: 0x00, bits: 1 }, // NO_PIECE
    HuffmanPiece { code: 0x01, bits: 2 }, // PAWN
    HuffmanPiece { code: 0x03, bits: 4 }, // LANCE
    HuffmanPiece { code: 0x0b, bits: 4 }, // KNIGHT
    HuffmanPiece { code: 0x07, bits: 4 }, // SILVER
    HuffmanPiece { code: 0x1f, bits: 6 }, // BISHOP
    HuffmanPiece { code: 0x3f, bits: 6 }, // ROOK
    HuffmanPiece { code: 0x0f, bits: 5 }, // GOLD
];

const HUFFMAN_TABLE_PIECEBOX: [HuffmanPiece; 8] = [
    HuffmanPiece { code: 0x00, bits: 1 }, // NOT USED
    HuffmanPiece { code: 0x02, bits: 2 }, // PAWN
    HuffmanPiece { code: 0x09, bits: 4 }, // LANCE
    HuffmanPiece { code: 0x0d, bits: 4 }, // KNIGHT
    HuffmanPiece { code: 0x0b, bits: 4 }, // SILVER
    HuffmanPiece { code: 0x2f, bits: 6 }, // BISHOP
    HuffmanPiece { code: 0x3f, bits: 6 }, // ROOK
    HuffmanPiece { code: 0x1b, bits: 5 }, // GOLD (piecebox)
];

const APERY_PIECES: [PieceType; 8] = [
    PieceType::NO_PIECE_TYPE,
    PieceType::PAWN,
    PieceType::LANCE,
    PieceType::KNIGHT,
    PieceType::SILVER,
    PieceType::GOLD,
    PieceType::BISHOP,
    PieceType::ROOK,
];

const fn huffman_index(piece_type: PieceType) -> Option<usize> {
    match piece_type {
        PieceType::NO_PIECE_TYPE => Some(0),
        PieceType::PAWN => Some(1),
        PieceType::LANCE => Some(2),
        PieceType::KNIGHT => Some(3),
        PieceType::SILVER => Some(4),
        PieceType::BISHOP => Some(5),
        PieceType::ROOK => Some(6),
        PieceType::GOLD => Some(7),
        _ => None,
    }
}

const fn is_promoted_piece(piece: Piece) -> bool {
    piece.piece_type().raw() >= 9
}

const fn raw_piece_type(piece: Piece) -> PieceType {
    piece.piece_type().demote()
}

impl Position {
    #[must_use]
    pub fn sfen_pack(&self) -> PackedSfen {
        let mut packed = PackedSfen { data: [0; 32] };
        let mut writer = BitWriter::new(&mut packed.data);

        writer.write_one_bit(self.side_to_move().raw() != 0);

        for color in [Color::BLACK, Color::WHITE] {
            let king_sq = self.king_square(color);
            let king_idx = u16::try_from(king_sq.raw()).expect("square fits in u16");
            writer.write_n_bits(king_idx, 7);
        }

        let mut piecebox_count = [0i32; 8];
        piecebox_count[1] = 18;
        piecebox_count[2] = 4;
        piecebox_count[3] = 4;
        piecebox_count[4] = 4;
        piecebox_count[5] = 2;
        piecebox_count[6] = 2;
        piecebox_count[7] = 4;

        for sq_idx in 0..Square::SQ_NB {
            let sq = Square::from_index(sq_idx);
            let piece = self.piece_on(sq);
            if piece.piece_type() == PieceType::KING {
                continue;
            }
            write_board_piece(&mut writer, piece);
            if piece != Piece::NO_PIECE {
                let raw = raw_piece_type(piece);
                if let Some(idx) = huffman_index(raw) {
                    piecebox_count[idx] -= 1;
                }
            }
        }

        for color in [Color::BLACK, Color::WHITE] {
            for &piece_type in APERY_PIECES.iter().skip(1) {
                let hand_piece =
                    HandPiece::from_piece_type(piece_type).expect("hand piece must exist");
                let count = self.hands[color.to_index()].count(hand_piece);
                for _ in 0..count {
                    let piece = Piece::make(color, piece_type);
                    write_hand_piece(&mut writer, piece);
                }
                let count_i32 = i32::try_from(count).expect("hand count fits in i32");
                if let Some(idx) = huffman_index(piece_type) {
                    piecebox_count[idx] -= count_i32;
                }
            }
        }

        for &piece_type in APERY_PIECES.iter().skip(1) {
            let idx = huffman_index(piece_type).expect("piecebox piece must be encodable");
            let count = piecebox_count[idx];
            for _ in 0..count {
                write_piecebox_piece(&mut writer, piece_type);
            }
        }

        debug_assert!(writer.cursor() == 256, "packed sfen must be 256 bits");
        packed
    }

    pub fn sfen_unpack(packed: &PackedSfen) -> Result<String, PackedSfenError> {
        let mut reader = BitReader::new(&packed.data);
        let (board, hands, side_to_move) = unpack_raw(&mut reader)?;
        let mut pos = Self::new();
        pos.board = board;
        pos.hands = hands;
        pos.side_to_move = side_to_move;
        pos.ply = 0;
        Ok(generate_sfen(&pos))
    }

    pub fn set_from_packed_sfen(
        &mut self,
        packed: &PackedSfen,
        mirror: bool,
        ply: Ply,
    ) -> Result<(), PackedSfenError> {
        let mut reader = BitReader::new(&packed.data);
        let (mut board, hands, side_to_move) = unpack_raw(&mut reader)?;

        if mirror {
            let mut mirrored = BoardArray::empty();
            for sq_idx in 0..Square::SQ_NB {
                let sq = Square::from_index(sq_idx);
                let msq = sq.mir();
                let piece = board.get(sq);
                if piece.is_empty() {
                    continue;
                }
                mirrored.set(msq, piece);
            }
            board = mirrored;
        }

        self.board = board;
        self.hands = hands;
        self.side_to_move = side_to_move;
        self.ply = ply;
        self.entering_king_rule = EnteringKingRule::None;
        self.entering_king_point = [0, 0];

        self.rebuild_bitboards();
        self.rebuild_piece_list();
        self.rebuild_eval_list();

        let keys = self.compute_keys();
        let (board_key, hand_key) = (keys.board_key, keys.hand_key);
        self.board_key = board_key;
        self.hand_key = hand_key;
        self.pawn_key = keys.pawn_key;
        self.minor_piece_key = keys.minor_piece_key;
        self.non_pawn_key = keys.non_pawn_key;
        self.material_key = keys.material_key;
        self.zobrist = board_key ^ hand_key;

        let (st_index, state_snapshot) = {
            let mut stack = self.state_stack_mut();
            stack.reset();
            let st_index = stack.current_index();
            let state = stack.current_mut();
            state.board_key = self.board_key;
            state.hand_key = self.hand_key;
            state.pawn_key = self.pawn_key;
            state.minor_piece_key = self.minor_piece_key;
            state.non_pawn_key = self.non_pawn_key;
            state.material_key = self.material_key;
            state.dirty_eval_piece = crate::board::eval_list::DirtyEvalPiece::default();
            state.material_value = material::material_value(self);
            self.compute_caches_for_state(state);
            state.hand = self.hands[self.side_to_move.to_index()];
            (st_index, state.clone())
        };
        self.sync_caches_from_state(&state_snapshot);
        self.st_index = st_index;
        self.update_entering_point();

        Ok(())
    }
}

fn unpack_raw(
    reader: &mut BitReader<'_>,
) -> Result<(BoardArray, [Hand; Color::COLOR_NB], Color), PackedSfenError> {
    let side_to_move = if reader.read_one_bit()? { Color::WHITE } else { Color::BLACK };

    let mut board = BoardArray::empty();
    for color in [Color::BLACK, Color::WHITE] {
        let sq = reader.read_n_bits(7)?;
        let sq = Square::new(i8::try_from(sq).expect("square fits in i8"));
        if !sq.is_none() {
            board.set(sq, super::PackedPiece::from_piece(Piece::make(color, PieceType::KING)));
        }
    }

    for sq_idx in 0..Square::SQ_NB {
        let sq = Square::from_index(sq_idx);
        let packed = board.get(sq);
        if packed.to_piece().piece_type() == PieceType::KING {
            continue;
        }
        let piece = read_board_piece(reader)?;
        if piece != Piece::NO_PIECE {
            board.set(sq, super::PackedPiece::from_piece(piece));
        }
    }

    let mut hands = [Hand::HAND_ZERO; Color::COLOR_NB];
    while reader.cursor() < 256 {
        let piece = read_hand_piece(reader)?;
        if is_promoted_piece(piece) {
            continue;
        }
        let hp =
            HandPiece::from_piece_type(piece.piece_type()).expect("hand piece must be promotable");
        let idx = piece.color().to_index();
        hands[idx].add(hp, 1);
    }

    if reader.cursor() != 256 {
        return Err(PackedSfenError::InvalidCursor);
    }

    Ok((board, hands, side_to_move))
}

fn write_board_piece(writer: &mut BitWriter<'_>, piece: Piece) {
    let raw = raw_piece_type(piece);
    let idx = huffman_index(raw).expect("board piece must be encodable");
    let code = HUFFMAN_TABLE[idx].code;
    let bits = HUFFMAN_TABLE[idx].bits;
    writer.write_n_bits(u16::from(code), bits);
    if piece == Piece::NO_PIECE {
        return;
    }
    if raw != PieceType::GOLD {
        writer.write_one_bit(is_promoted_piece(piece));
    }
    writer.write_one_bit(piece.color().raw() != 0);
}

fn write_hand_piece(writer: &mut BitWriter<'_>, piece: Piece) {
    let raw = raw_piece_type(piece);
    let idx = huffman_index(raw).expect("hand piece must be encodable");
    let code = HUFFMAN_TABLE[idx].code >> 1;
    let bits = HUFFMAN_TABLE[idx].bits - 1;
    writer.write_n_bits(u16::from(code), bits);
    if raw != PieceType::GOLD {
        writer.write_one_bit(false);
    }
    writer.write_one_bit(piece.color().raw() != 0);
}

fn write_piecebox_piece(writer: &mut BitWriter<'_>, piece_type: PieceType) {
    let idx = huffman_index(piece_type).expect("piecebox piece must be encodable");
    let code = HUFFMAN_TABLE_PIECEBOX[idx].code;
    let bits = HUFFMAN_TABLE_PIECEBOX[idx].bits;
    writer.write_n_bits(u16::from(code), bits);
    if piece_type != PieceType::GOLD {
        writer.write_one_bit(false);
    }
}

fn read_board_piece(reader: &mut BitReader<'_>) -> Result<Piece, PackedSfenError> {
    let mut code: u8 = 0;
    let mut bits: u8 = 0;
    let pr = loop {
        code |= u8::from(reader.read_one_bit()?) << bits;
        bits += 1;
        let mut found = None;
        for (idx, entry) in HUFFMAN_TABLE.iter().enumerate() {
            if entry.code == code && entry.bits == bits {
                found = Some(match idx {
                    0 => PieceType::NO_PIECE_TYPE,
                    1 => PieceType::PAWN,
                    2 => PieceType::LANCE,
                    3 => PieceType::KNIGHT,
                    4 => PieceType::SILVER,
                    5 => PieceType::BISHOP,
                    6 => PieceType::ROOK,
                    7 => PieceType::GOLD,
                    _ => return Err(PackedSfenError::InvalidPieceCode),
                });
                break;
            }
        }
        if let Some(pr) = found {
            break pr;
        }
        if bits > 6 {
            return Err(PackedSfenError::InvalidPieceCode);
        }
    };

    if pr == PieceType::NO_PIECE_TYPE {
        return Ok(Piece::NO_PIECE);
    }

    let promoted = if pr == PieceType::GOLD { false } else { reader.read_one_bit()? };
    let color = if reader.read_one_bit()? { Color::WHITE } else { Color::BLACK };
    let piece_type = if promoted { pr.promote() } else { pr };
    Ok(Piece::make(color, piece_type))
}

fn read_hand_piece(reader: &mut BitReader<'_>) -> Result<Piece, PackedSfenError> {
    let mut code: u8 = 0;
    let mut bits: u8 = 0;
    let pr = loop {
        code |= u8::from(reader.read_one_bit()?) << bits;
        bits += 1;
        let mut found = None;
        for (idx, entry) in HUFFMAN_TABLE.iter().enumerate().skip(1) {
            if entry.code >> 1 == code && entry.bits - 1 == bits {
                found = Some(match idx {
                    1 => PieceType::PAWN,
                    2 => PieceType::LANCE,
                    3 => PieceType::KNIGHT,
                    4 => PieceType::SILVER,
                    5 => PieceType::BISHOP,
                    6 => PieceType::ROOK,
                    7 => PieceType::GOLD,
                    _ => return Err(PackedSfenError::InvalidPieceCode),
                });
                break;
            }
        }
        if let Some(pr) = found {
            break pr;
        }
        if bits > 6 {
            return Err(PackedSfenError::InvalidPieceCode);
        }
    };

    let promoted = if pr == PieceType::GOLD { false } else { reader.read_one_bit()? };
    let color = if reader.read_one_bit()? { Color::WHITE } else { Color::BLACK };
    let piece_type = if promoted { pr.promote() } else { pr };
    Ok(Piece::make(color, piece_type))
}
