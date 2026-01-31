#![deny(unsafe_code)]
#![allow(clippy::doc_markdown)]

//! rshogi コアクレートの入口となるクレートです。
//!
//! - 盤面表現と差分更新、合法手生成といったローレベル機能を `board` モジュールに集約しています。
//! - エンジンや評価関数とは分離し、局面管理や共通ユーティリティに専念します。
//! - 開発フローやビルド手順は `DEVELOPMENT.md` を参照してください。

pub mod board;
pub mod mate;
pub(crate) mod simd;
pub mod types;

// Re-export movegen types at crate root for easier access
pub use board::movegen;

/// 核となるエンジンのハンドル。USI インターフェースからの操作を受け取る窓口となります。
pub struct Engine {
    name: &'static str,
}

impl Default for Engine {
    fn default() -> Self {
        Self { name: "rshogi" }
    }
}

impl Engine {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// エンジンの識別名。USI `usi` コマンドに応答する際に利用します。
    #[must_use]
    pub const fn name(&self) -> &'static str {
        self.name
    }
}
