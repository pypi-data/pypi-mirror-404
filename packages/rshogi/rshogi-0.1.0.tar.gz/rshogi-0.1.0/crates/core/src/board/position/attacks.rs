use super::Position;
use crate::types::{Bitboard, Color, PieceType, Square};

impl Position {
    /// 指定マスを攻撃している駒の`Bitboard`を返す
    ///
    /// # Arguments
    /// * `sq` - 攻撃対象のマス
    /// * `occupied` - 盤面占有状態の`Bitboard`
    ///
    /// # Returns
    /// 指定マスを攻撃している全駒の`Bitboard`
    #[must_use]
    pub fn attackers_to(&self, sq: Square, occupied: Bitboard) -> Bitboard {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};
        use crate::board::attack_tables::{
            GOLD_ATTACKS, KNIGHT_ATTACKS, PAWN_ATTACKS, SILVER_ATTACKS,
        };
        if sq.is_none() {
            return Bitboard::EMPTY;
        }

        let sq_idx = sq.to_index();
        let bb = self.bitboards();
        let mut attackers = Bitboard::EMPTY;
        let pawns = bb.pieces(PieceType::PAWN);
        let knights = bb.pieces(PieceType::KNIGHT);
        let silvers = bb.pieces(PieceType::SILVER);
        let golds = bb.golds();
        let hdk = bb.hdk();
        let bishops_horse = bb.bishop_horse();
        let rooks_dragon = bb.rook_dragon();
        let lances = bb.pieces(PieceType::LANCE);

        let silver_hdk = silvers | hdk;
        let golds_hdk = golds | hdk;

        for &color in &[Color::BLACK, Color::WHITE] {
            let them = color.flip();
            let color_mask = bb.color_pieces(color);

            let step_attacks = (PAWN_ATTACKS[sq_idx][them.to_index()] & pawns)
                | (KNIGHT_ATTACKS[sq_idx][them.to_index()] & knights)
                | (SILVER_ATTACKS[sq_idx][them.to_index()] & silver_hdk)
                | (GOLD_ATTACKS[sq_idx][them.to_index()] & golds_hdk);

            let bishop_atk = bishop_attacks(sq, occupied) & bishops_horse;
            let lance_line = lance_attacks(sq, Bitboard::EMPTY, them) & lances;
            let rook_atk = rook_attacks(sq, occupied) & (rooks_dragon | lance_line);

            attackers = attackers | ((step_attacks | bishop_atk | rook_atk) & color_mask);
        }

        attackers
    }

    /// 指定マスを攻撃している指定色の駒を返す（occupiedは指定の盤面）。
    #[must_use]
    pub fn attackers_to_color(&self, color: Color, sq: Square, occupied: Bitboard) -> Bitboard {
        self.attackers_to(sq, occupied).and(self.bitboards().color_pieces(color))
    }

    /// 指定マスを攻撃している指定色の駒を返す（現在の盤面）。
    #[must_use]
    pub fn attackers_to_color_current(&self, color: Color, sq: Square) -> Bitboard {
        self.attackers_to_color(color, sq, self.bitboards().occupied())
    }

    /// 指定マスが指定色に攻撃されているか判定
    ///
    /// # Arguments
    /// * `sq` - 判定対象のマス
    /// * `by_color` - 攻撃側の色
    ///
    /// # Returns
    /// 攻撃されている場合`true`
    #[must_use]
    pub fn is_attacked_by(&self, sq: Square, by_color: Color) -> bool {
        self.effected_to(by_color, sq)
    }

    pub(in crate::board) fn attackers_to_pawn(&self, color: Color, sq: Square) -> Bitboard {
        use crate::board::attack_tables::{bishop_attacks, rook_attacks};
        use crate::board::attack_tables::{GOLD_ATTACKS, KNIGHT_ATTACKS, SILVER_ATTACKS};
        if sq.is_none() {
            return Bitboard::EMPTY;
        }

        let them = color.flip();
        let bb = self.bitboards();
        let occupied = bb.occupied();

        let bb_hd = bb.pieces(PieceType::HORSE) | bb.pieces(PieceType::DRAGON);
        let knights = KNIGHT_ATTACKS[sq.to_index()][them.to_index()] & bb.pieces(PieceType::KNIGHT);
        let silvers =
            SILVER_ATTACKS[sq.to_index()][them.to_index()] & (bb.pieces(PieceType::SILVER) | bb_hd);
        let golds = GOLD_ATTACKS[sq.to_index()][them.to_index()]
            & (bb.pieces(PieceType::GOLD)
                | bb.pieces(PieceType::PRO_PAWN)
                | bb.pieces(PieceType::PRO_LANCE)
                | bb.pieces(PieceType::PRO_KNIGHT)
                | bb.pieces(PieceType::PRO_SILVER)
                | bb_hd);
        let bishops = bishop_attacks(sq, occupied) & bb.bishop_horse();
        let rooks = rook_attacks(sq, occupied) & bb.rook_dragon();

        (knights | silvers | golds | bishops | rooks) & bb.color_pieces(color)
    }

    /// 指定した駒種が指定位置から攻撃する範囲を返す
    #[must_use]
    pub(crate) fn piece_attacks(
        piece_type: PieceType,
        sq: Square,
        c: Color,
        occupied: Bitboard,
    ) -> Bitboard {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};
        use crate::board::attack_tables::{
            GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS, PAWN_ATTACKS, SILVER_ATTACKS,
        };

        match piece_type {
            PieceType::PAWN => PAWN_ATTACKS[sq.to_index()][c.to_index()],
            PieceType::LANCE => lance_attacks(sq, occupied, c),
            PieceType::KNIGHT => KNIGHT_ATTACKS[sq.to_index()][c.to_index()],
            PieceType::SILVER => SILVER_ATTACKS[sq.to_index()][c.to_index()],
            PieceType::GOLD
            | PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER => GOLD_ATTACKS[sq.to_index()][c.to_index()],
            PieceType::BISHOP => bishop_attacks(sq, occupied),
            PieceType::ROOK => rook_attacks(sq, occupied),
            PieceType::HORSE => {
                // 角の動き + 縦横1マス
                let bishop_moves = bishop_attacks(sq, occupied);
                let king_moves = KING_ATTACKS[sq.to_index()];
                bishop_moves | king_moves
            }
            PieceType::DRAGON => {
                // 飛車の動き + 斜め1マス
                let rook_moves = rook_attacks(sq, occupied);
                let king_moves = KING_ATTACKS[sq.to_index()];
                rook_moves | king_moves
            }
            PieceType::KING => KING_ATTACKS[sq.to_index()],
            _ => Bitboard::EMPTY,
        }
    }

    /// 指定色の駒種が攻撃しているマス集合を返す（YaneuraOu互換）。
    #[must_use]
    pub fn attacks_by(&self, color: Color, piece_type: PieceType) -> Bitboard {
        use crate::board::attack_tables::PAWN_ATTACKS;

        let occupied = self.bitboards().occupied();
        let mut attacks = Bitboard::EMPTY;
        let mut pieces = self.bitboards().pieces_of(piece_type, color);

        if piece_type == PieceType::PAWN {
            while let Some(sq) = pieces.pop_lsb() {
                attacks = attacks | PAWN_ATTACKS[sq.to_index()][color.to_index()];
            }
            return attacks;
        }

        while let Some(sq) = pieces.pop_lsb() {
            attacks = attacks | Self::piece_attacks(piece_type, sq, color, occupied);
        }

        attacks
    }

    /// 指定色の駒種が攻撃しているマス集合を返す（const-generic版）。
    #[must_use]
    pub fn attacks_by_const<const C: i8, const PT: i8>(&self) -> Bitboard {
        let color = Color::new(C);
        let piece_type = PieceType::new(PT);
        debug_assert!(color.is_ok(), "invalid color");
        debug_assert!(piece_type.is_ok(), "invalid piece type");
        self.attacks_by(color, piece_type)
    }

    /// 指定マスを攻撃している指定色の駒を返す（const-generic版）。
    #[must_use]
    pub fn attackers_to_const<const C: i8>(&self, sq: Square, occupied: Bitboard) -> Bitboard {
        let color = Color::new(C);
        debug_assert!(color.is_ok(), "invalid color");
        self.attackers_to_color(color, sq, occupied)
    }

    // --- Private helpers ---

    /// 指定色の玉に対するブロッカーとピンしている敵大駒を算出
    pub(in crate::board) fn compute_slider_info(&self, color: Color) -> (Bitboard, Bitboard) {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};

        let king_sq = self.king_square(color);
        if king_sq.is_none() {
            return (Bitboard::EMPTY, Bitboard::EMPTY);
        }

        let them = color.flip();
        let rook_like = self.bitboards().pieces_of(PieceType::ROOK, them)
            | self.bitboards().pieces_of(PieceType::DRAGON, them);
        let bishop_like = self.bitboards().pieces_of(PieceType::BISHOP, them)
            | self.bitboards().pieces_of(PieceType::HORSE, them);
        let lance_like = self.bitboards().pieces_of(PieceType::LANCE, them);

        let rook_snipers = rook_like & rook_attacks(king_sq, Bitboard::EMPTY);
        let bishop_snipers = bishop_like & bishop_attacks(king_sq, Bitboard::EMPTY);
        let lance_snipers = lance_like & lance_attacks(king_sq, Bitboard::EMPTY, color);

        let snipers = rook_snipers | bishop_snipers | lance_snipers;

        let occupancy = self.bitboards().occupied() ^ snipers;

        let mut blockers = Bitboard::EMPTY;
        let mut pinners = Bitboard::EMPTY;

        for sniper_sq in &snipers {
            let between = Bitboard::between(sniper_sq, king_sq) & occupancy;

            if between.count() == 1 {
                blockers = blockers | between;
                if between.intersects(self.bitboards().color_pieces(color)) {
                    pinners.set(sniper_sq);
                }
            }
        }

        (blockers, pinners)
    }
}
