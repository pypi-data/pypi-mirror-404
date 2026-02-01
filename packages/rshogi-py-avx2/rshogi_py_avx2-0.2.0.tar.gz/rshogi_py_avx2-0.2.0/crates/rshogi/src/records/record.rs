use crate::records::error::RecordError;
use crate::types::{GameResult, Move};

/// 1手分の記録。
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MoveRecord {
    /// 指し手（32bit Move）。
    mv: Move,
    /// 評価値（先手視点）。
    eval: Option<i32>,
}

impl MoveRecord {
    /// `Move` と任意の評価値から構築します。
    #[must_use]
    pub fn new(mv: Move, eval: Option<i32>) -> Self {
        Self { mv, eval }
    }

    /// 指し手を取得します。
    #[must_use]
    pub const fn mv(&self) -> Move {
        self.mv
    }

    /// 評価値を取得します。
    #[must_use]
    pub const fn eval(&self) -> Option<i32> {
        self.eval
    }
}

/// 終局情報。
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RecordResult {
    /// 結果コード
    result: GameResult,
    /// 終局理由（任意）
    reason: Option<String>,
    /// 指し手数（半手）
    ply_count: Option<usize>,
}

impl RecordResult {
    #[must_use]
    pub fn new(result: GameResult, reason: Option<String>, ply_count: Option<usize>) -> Self {
        Self { result, reason, ply_count }
    }

    /// 結果コードを取得します。
    #[must_use]
    pub const fn result(&self) -> GameResult {
        self.result
    }

    /// 終局理由を取得します。
    #[must_use]
    pub fn reason(&self) -> Option<&str> {
        self.reason.as_deref()
    }

    /// 指し手数（半手）を取得します。
    #[must_use]
    pub const fn ply_count(&self) -> Option<usize> {
        self.ply_count
    }
}

/// 棋譜全体。
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Record {
    init_position_sfen: String,
    moves: Vec<MoveRecord>,
    result: RecordResult,
}

impl Record {
    /// 新しい棋譜を構築します。
    pub fn new(
        init_position_sfen: String,
        moves: Vec<MoveRecord>,
        result: RecordResult,
    ) -> Result<Self, RecordError> {
        if init_position_sfen.is_empty() {
            return Err(RecordError::EmptyInitPosition);
        }

        if let Some(expected) = result.ply_count {
            if expected != moves.len() {
                return Err(RecordError::PlyCountMismatch { expected, actual: moves.len() });
            }
        }

        Ok(Self { init_position_sfen, moves, result })
    }

    /// 指し手数（半手）
    #[must_use]
    pub fn num_moves(&self) -> usize {
        self.moves.len()
    }

    /// 初期局面 SFEN を取得します。
    #[must_use]
    pub fn init_position_sfen(&self) -> &str {
        &self.init_position_sfen
    }

    /// 指し手一覧を取得します。
    #[must_use]
    pub fn moves(&self) -> &[MoveRecord] {
        &self.moves
    }

    /// 終局情報を取得します。
    #[must_use]
    pub const fn result(&self) -> &RecordResult {
        &self.result
    }
}
