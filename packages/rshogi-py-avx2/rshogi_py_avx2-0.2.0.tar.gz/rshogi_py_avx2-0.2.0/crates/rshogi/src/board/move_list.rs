//! `MoveList` - 固定長の合法手リスト

use crate::types::Move;
use arrayvec::ArrayVec;

/// 最大合法手数（将棋の理論上限）
pub const MAX_MOVES: usize = 600;

/// 指し手とスコアのペア（YaneuraOu の ExtMove 相当）
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExtMove {
    mv: Move,
    value: i32,
}

impl ExtMove {
    #[must_use]
    pub const fn new(mv: Move, value: i32) -> Self {
        Self { mv, value }
    }

    #[must_use]
    pub const fn mv(self) -> Move {
        self.mv
    }

    #[must_use]
    pub const fn value(self) -> i32 {
        self.value
    }

    pub fn set_value(&mut self, value: i32) {
        self.value = value;
    }
}

impl From<Move> for ExtMove {
    fn from(mv: Move) -> Self {
        Self::new(mv, 0)
    }
}

/// 固定長の合法手リスト
#[derive(Debug, Clone)]
pub struct MoveList {
    moves: ArrayVec<Move, MAX_MOVES>,
}

impl MoveList {
    /// 新しい空の`MoveList`を作成
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self { moves: ArrayVec::new() }
    }

    /// リストをクリア
    #[inline]
    pub fn clear(&mut self) {
        self.moves.clear();
    }

    /// 手を追加
    #[inline]
    pub fn push(&mut self, m: Move) {
        self.moves.push(m);
    }

    /// 手数を取得
    #[inline]
    #[must_use]
    pub const fn len(&self) -> usize {
        self.moves.len()
    }

    /// 空かどうか判定
    #[inline]
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.moves.is_empty()
    }

    /// イテレータを取得
    #[inline]
    pub fn iter(&self) -> impl Iterator<Item = &Move> {
        self.moves.iter()
    }

    /// スライスを取得
    #[inline]
    #[must_use]
    pub fn as_slice(&self) -> &[Move] {
        self.moves.as_slice()
    }

    /// 条件を満たす手だけを残す
    pub fn retain<F>(&mut self, mut f: F)
    where
        F: FnMut(Move) -> bool,
    {
        let mut i = 0;
        while i < self.moves.len() {
            let m = self.moves[i];
            if f(m) {
                i += 1;
            } else {
                self.moves.remove(i);
            }
        }
    }

    /// 条件を満たす手だけを残す（順序は保持しない）
    pub fn retain_unordered<F>(&mut self, mut f: F)
    where
        F: FnMut(Move) -> bool,
    {
        let mut i = 0;
        while i < self.moves.len() {
            let m = self.moves[i];
            if f(m) {
                i += 1;
            } else {
                self.moves.swap_remove(i);
            }
        }
    }
}

impl Default for MoveList {
    fn default() -> Self {
        Self::new()
    }
}

/// スコア付きの合法手リスト
#[derive(Debug, Clone)]
pub struct ExtMoveList {
    moves: ArrayVec<ExtMove, MAX_MOVES>,
}

impl ExtMoveList {
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self { moves: ArrayVec::new() }
    }

    #[inline]
    pub fn clear(&mut self) {
        self.moves.clear();
    }

    #[inline]
    pub fn push(&mut self, m: ExtMove) {
        self.moves.push(m);
    }

    #[inline]
    #[must_use]
    pub const fn len(&self) -> usize {
        self.moves.len()
    }

    #[inline]
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.moves.is_empty()
    }

    #[inline]
    pub fn iter(&self) -> impl Iterator<Item = &ExtMove> {
        self.moves.iter()
    }

    #[inline]
    pub fn iter_mut(&mut self) -> impl Iterator<Item = &mut ExtMove> {
        self.moves.iter_mut()
    }

    #[inline]
    #[must_use]
    pub fn as_slice(&self) -> &[ExtMove] {
        self.moves.as_slice()
    }

    #[inline]
    #[must_use]
    pub fn as_mut_slice(&mut self) -> &mut [ExtMove] {
        self.moves.as_mut_slice()
    }

    /// 条件を満たす手だけを残す（順序は保持しない）
    pub fn retain_unordered<F>(&mut self, mut f: F)
    where
        F: FnMut(Move) -> bool,
    {
        let mut i = 0;
        while i < self.moves.len() {
            let mv = self.moves[i].mv;
            if f(mv) {
                i += 1;
            } else {
                self.moves.swap_remove(i);
            }
        }
    }
}

impl Default for ExtMoveList {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::square::{SQ_26, SQ_27, SQ_76, SQ_77};
    use crate::types::Piece;

    #[test]
    fn test_move_list_new() {
        let list = MoveList::new();
        assert!(list.is_empty());
        assert_eq!(list.len(), 0);
    }

    #[test]
    fn test_move_list_push() {
        let mut list = MoveList::new();
        let m = Move::make(SQ_77, SQ_76, Piece::B_PAWN);

        list.push(m);
        assert_eq!(list.len(), 1);
        assert!(!list.is_empty());
    }

    #[test]
    fn test_move_list_clear() {
        let mut list = MoveList::new();
        let m = Move::make(SQ_77, SQ_76, Piece::B_PAWN);

        list.push(m);
        assert_eq!(list.len(), 1);

        list.clear();
        assert_eq!(list.len(), 0);
        assert!(list.is_empty());
    }

    #[test]
    fn test_move_list_iter() {
        let mut list = MoveList::new();
        let m1 = Move::make(SQ_77, SQ_76, Piece::B_PAWN);
        let m2 = Move::make(SQ_27, SQ_26, Piece::B_PAWN);

        list.push(m1);
        list.push(m2);

        let moves: Vec<_> = list.iter().copied().collect();
        assert_eq!(moves.len(), 2);
        assert_eq!(moves[0], m1);
        assert_eq!(moves[1], m2);
    }
}
