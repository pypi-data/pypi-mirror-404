//! 駒位置管理データ構造
//!
//! `YaneuraOu` の `piece_list_fb/fw` を参考に、駒種ごとの駒位置を高速にアクセスできるデータ構造を提供する。
//! これにより、NNUE特徴抽出で81マス全体を走査する必要がなくなり、O(駒数)でアクセスできるようになる。
//!
//! ## 参照元
//! - `YaneuraOu`: `position.h` の `piece_list_fb`, `piece_list_fw`
//! - 設計: `.kiro/specs/p12-yaneuraou-alignment/design.md` Phase 1

use crate::types::{Color, PieceType, Square};

/// 駒種ごとの駒位置リスト
///
/// # データ構造
/// - `fw`: forward list - `fw[color][piece_type][index]` = Square
///   駒種ごとに駒の位置を配列で管理
/// - `fb`: backward list - `fb[color][square]` = index
///   マスから駒種内インデックスへの逆引き
/// - `count`: 駒数 - `count[color][piece_type]`
///   各駒種の駒数
///
/// # 不変条件
/// - `count[c][pt]` == `fw[c][pt]` の有効要素数
/// - `fb[c][sq]` < `count[c][sq上の駒種]`（駒が存在する場合）
/// - `fw[c][pt][fb[c][sq]]` == `sq`（駒が存在する場合）
///
/// # メモリレイアウト
/// - forward list: 2 * 16 * 18 * 1byte = 576 bytes
/// - backward list: 2 * 81 * 1byte = 162 bytes
/// - count: 2 * 16 * 1byte = 32 bytes
/// - 合計: 770 bytes
#[derive(Clone, Debug)]
pub struct PieceList {
    /// forward list: [先後2][駒種16][最大18個] = Square
    fw: [[[Square; 18]; PieceType::PIECE_TYPE_NB]; Color::COLOR_NB],

    /// backward list: [先後2][81マス] = index
    fb: [[u8; Square::SQ_NB]; Color::COLOR_NB],

    /// 駒数: [先後2][駒種16] = count
    count: [[u8; PieceType::PIECE_TYPE_NB]; Color::COLOR_NB],
}

impl PieceList {
    /// 空の `PieceList` を生成
    ///
    /// # 事後条件
    /// - 全ての駒数が0
    /// - fw/fbは未初期化（駒追加時に設定される）
    #[must_use]
    pub const fn new() -> Self {
        Self {
            fw: [[[Square::SQ_NONE; 18]; PieceType::PIECE_TYPE_NB]; Color::COLOR_NB],
            fb: [[0; Square::SQ_NB]; Color::COLOR_NB],
            count: [[0; PieceType::PIECE_TYPE_NB]; Color::COLOR_NB],
        }
    }

    /// 駒を追加
    ///
    /// # 事前条件
    /// - `square` に駒が存在しない
    /// - `count[color][piece_type]` < 18
    ///
    /// # 事後条件
    /// - `fw[color][piece_type][count]` = `square`
    /// - `fb[color][square]` = `count`
    /// - `count[color][piece_type]` += 1
    ///
    /// # Panics
    /// デバッグビルドでは、事前条件違反時にパニック
    pub fn add_piece(&mut self, color: Color, piece_type: PieceType, square: Square) {
        let c_idx = color.to_index();
        let pt_idx = piece_type.to_index();
        let sq_idx = square.to_index();
        let current_count = self.count[c_idx][pt_idx];

        debug_assert!(
            current_count < 18,
            "駒数が上限を超えています: color={color:?}, piece_type={piece_type:?}, count={current_count}"
        );

        // forward listに追加
        self.fw[c_idx][pt_idx][current_count as usize] = square;

        // backward listを更新
        self.fb[c_idx][sq_idx] = current_count;

        // 駒数をインクリメント
        self.count[c_idx][pt_idx] += 1;
    }

    /// 駒を削除
    ///
    /// # 事前条件
    /// - `square` に駒が存在する
    ///
    /// # 事後条件
    /// - 削除された駒の位置に最後の駒を移動（O(1)削除）
    /// - `count[color][piece_type]` -= 1
    ///
    /// # Panics
    /// デバッグビルドでは、事前条件違反時にパニック
    pub fn remove_piece(&mut self, color: Color, piece_type: PieceType, square: Square) {
        let c_idx = color.to_index();
        let pt_idx = piece_type.to_index();
        let sq_idx = square.to_index();

        debug_assert!(
            self.count[c_idx][pt_idx] > 0,
            "削除対象の駒種の駒が存在しません: color={color:?}, piece_type={piece_type:?}"
        );

        // 削除する駒のインデックス
        let remove_idx = self.fb[c_idx][sq_idx] as usize;

        // 駒数をデクリメント
        self.count[c_idx][pt_idx] -= 1;
        let last_idx = self.count[c_idx][pt_idx] as usize;

        // 最後の駒を削除位置に移動（O(1)削除）
        if remove_idx != last_idx {
            let last_square = self.fw[c_idx][pt_idx][last_idx];
            self.fw[c_idx][pt_idx][remove_idx] = last_square;
            #[allow(clippy::cast_possible_truncation)]
            {
                self.fb[c_idx][last_square.to_index()] = remove_idx as u8;
            }
        }

        // 削除された位置をクリア（デバッグ用）
        self.fw[c_idx][pt_idx][last_idx] = Square::SQ_NONE;
    }

    /// 駒を移動
    ///
    /// # 事前条件
    /// - `from_square` に駒が存在する
    /// - `to_square` に駒が存在しない
    ///
    /// # 事後条件
    /// - `from_square` の駒が `to_square` に移動
    /// - forward/backward listが更新される
    pub fn move_piece(
        &mut self,
        color: Color,
        piece_type: PieceType,
        from_square: Square,
        to_square: Square,
    ) {
        let c_idx = color.to_index();
        let pt_idx = piece_type.to_index();
        let from_idx = from_square.to_index();
        let to_idx = to_square.to_index();

        // 駒のインデックスを取得
        let piece_idx = self.fb[c_idx][from_idx] as usize;

        // forward listを更新
        self.fw[c_idx][pt_idx][piece_idx] = to_square;

        // backward listを更新
        #[allow(clippy::cast_possible_truncation)]
        {
            self.fb[c_idx][to_idx] = piece_idx as u8;
        }
    }

    /// 駒種の全駒位置を取得
    ///
    /// # 不変条件
    /// - 返される配列の長さは `count[color][piece_type]`
    #[must_use]
    pub fn pieces(&self, color: Color, piece_type: PieceType) -> &[Square] {
        let c_idx = color.to_index();
        let pt_idx = piece_type.to_index();
        let count = self.count[c_idx][pt_idx] as usize;
        &self.fw[c_idx][pt_idx][..count]
    }

    /// 駒数を取得
    #[must_use]
    pub const fn piece_count(&self, color: Color, piece_type: PieceType) -> u8 {
        self.count[color.to_index()][piece_type.to_index()]
    }
}

impl Default for PieceList {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_piece_list() {
        let piece_list = PieceList::new();

        // 全ての駒数が0であることを確認
        for color in [Color::BLACK, Color::WHITE] {
            for pt in 0..PieceType::PIECE_TYPE_NB {
                #[allow(clippy::cast_possible_truncation)]
                let piece_type = PieceType::new(pt as i8);
                assert_eq!(piece_list.piece_count(color, piece_type), 0);
            }
        }
    }

    #[test]
    fn test_add_remove_piece() {
        let mut piece_list = PieceList::new();

        // 駒を追加
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(0)); // 1一
        assert_eq!(piece_list.piece_count(Color::BLACK, PieceType::PAWN), 1);

        let pieces = piece_list.pieces(Color::BLACK, PieceType::PAWN);
        assert_eq!(pieces.len(), 1);
        assert_eq!(pieces[0], Square(0));

        // 駒を削除
        piece_list.remove_piece(Color::BLACK, PieceType::PAWN, Square(0));
        assert_eq!(piece_list.piece_count(Color::BLACK, PieceType::PAWN), 0);
    }

    #[test]
    fn test_move_piece() {
        let mut piece_list = PieceList::new();

        // 駒を追加
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(0)); // 1一

        // 駒を移動
        piece_list.move_piece(Color::BLACK, PieceType::PAWN, Square(0), Square(1)); // 1一 -> 1二

        let pieces = piece_list.pieces(Color::BLACK, PieceType::PAWN);
        assert_eq!(pieces.len(), 1);
        assert_eq!(pieces[0], Square(1));
    }

    #[test]
    fn test_backward_list_consistency() {
        let mut piece_list = PieceList::new();

        // 複数の駒を追加
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(0)); // 1一
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(9)); // 2一
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(18)); // 3一

        // backward listの整合性を確認
        let c_idx = Color::BLACK.to_index();
        let pt_idx = PieceType::PAWN.to_index();

        for i in 0..3 {
            let sq = piece_list.fw[c_idx][pt_idx][i];
            let back_idx = piece_list.fb[c_idx][sq.to_index()] as usize;
            assert_eq!(back_idx, i, "backward list inconsistency at index {i}");
        }
    }

    #[test]
    fn test_forward_list_compaction() {
        let mut piece_list = PieceList::new();

        // 3つの駒を追加
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(0)); // 1一
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(9)); // 2一
        piece_list.add_piece(Color::BLACK, PieceType::PAWN, Square(18)); // 3一

        // 中央の駒を削除
        piece_list.remove_piece(Color::BLACK, PieceType::PAWN, Square(9));

        // 駒数が2になっていることを確認
        assert_eq!(piece_list.piece_count(Color::BLACK, PieceType::PAWN), 2);

        // forward listが詰められていることを確認
        let pieces = piece_list.pieces(Color::BLACK, PieceType::PAWN);
        assert_eq!(pieces.len(), 2);
        assert!(pieces.contains(&Square(0)));
        assert!(pieces.contains(&Square(18)));

        // backward listの整合性を確認
        let c_idx = Color::BLACK.to_index();
        let pt_idx = PieceType::PAWN.to_index();
        for i in 0..2 {
            let sq = piece_list.fw[c_idx][pt_idx][i];
            let back_idx = piece_list.fb[c_idx][sq.to_index()] as usize;
            assert_eq!(back_idx, i, "backward list inconsistency after deletion");
        }
    }
}
