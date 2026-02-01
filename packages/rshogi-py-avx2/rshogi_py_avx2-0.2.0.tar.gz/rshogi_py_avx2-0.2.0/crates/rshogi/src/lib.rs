#![deny(unsafe_code)]
#![allow(clippy::doc_markdown)]

//! rshogi の入口クレートです（crates.io で公開する単一クレート）。
//!
//! - 盤面表現と差分更新、合法手生成といったローレベル機能を `board` モジュールに集約しています。
//! - エンジンや評価関数とは分離し、局面管理や共通ユーティリティに専念します。
//! - 開発フローやビルド手順は `DEVELOPMENT.md` を参照してください。

pub mod board;
pub mod mate;
pub(crate) mod simd;
pub mod types;
pub mod records;

// Re-export movegen types at crate root for easier access
pub use board::movegen;

/// 互換性と分かりやすさのため、コアAPIを `rshogi::core::*` にも公開します。
///
/// 現状の実装は crate 直下（`rshogi::board` / `rshogi::types` など）が実体で、
/// `rshogi::core` はそれらへの薄いエイリアスです。
pub mod core {
    pub use super::board;
    pub use super::mate;
    pub use super::movegen;
    pub use super::types;
    pub use super::Engine;
}

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
