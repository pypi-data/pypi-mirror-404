//! 対局結果の型定義

use super::Color;

/// 対局結果（ShogiArenaの値互換）
#[repr(u8)]
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum GameResult {
    /// 先手勝ち
    BlackWin = 0,
    /// 後手勝ち
    WhiteWin = 1,
    /// 千日手による引き分け
    DrawByRepetition = 2,
    /// エラー
    Error = 3,
    /// 先手宣言勝ち
    BlackWinByDeclaration = 4,
    /// 後手宣言勝ち
    WhiteWinByDeclaration = 5,
    /// 最大手数（半手）または持将棋による引き分け
    DrawByMaxPlies = 6,
    /// 無効対局
    Invalid = 7,
    /// 先手不戦勝
    BlackWinByForfeit = 8,
    /// 後手不戦勝
    WhiteWinByForfeit = 9,
    /// 中断
    Paused = 10,
    /// 先手反則勝ち
    BlackWinByIllegalMove = 12,
    /// 後手反則勝ち
    WhiteWinByIllegalMove = 13,
    /// 先手時間切れ勝ち
    BlackWinByTimeout = 16,
    /// 後手時間切れ勝ち
    WhiteWinByTimeout = 17,
}

impl GameResult {
    /// 先手勝ちか？
    #[must_use]
    pub const fn is_black_win(self) -> bool {
        matches!(
            self,
            Self::BlackWin
                | Self::BlackWinByDeclaration
                | Self::BlackWinByForfeit
                | Self::BlackWinByIllegalMove
                | Self::BlackWinByTimeout
        )
    }

    /// 後手勝ちか？
    #[must_use]
    pub const fn is_white_win(self) -> bool {
        matches!(
            self,
            Self::WhiteWin
                | Self::WhiteWinByDeclaration
                | Self::WhiteWinByForfeit
                | Self::WhiteWinByIllegalMove
                | Self::WhiteWinByTimeout
        )
    }

    /// 引き分けか？
    #[must_use]
    pub const fn is_draw(self) -> bool {
        matches!(self, Self::DrawByRepetition | Self::DrawByMaxPlies)
    }

    /// どちらかが勝利したか？
    #[must_use]
    pub const fn is_win(self) -> bool {
        self.is_black_win() || self.is_white_win()
    }

    /// 宣言勝ちか？
    #[must_use]
    pub const fn is_win_by_declaration(self) -> bool {
        matches!(self, Self::BlackWinByDeclaration | Self::WhiteWinByDeclaration)
    }

    /// 勝利した手番を返す（勝敗が付かない場合はNone）
    #[must_use]
    pub const fn winner_color(self) -> Option<Color> {
        if self.is_black_win() {
            Some(Color::BLACK)
        } else if self.is_white_win() {
            Some(Color::WHITE)
        } else {
            None
        }
    }

    /// 指定した手番から見たスコアを返す。
    ///
    /// 勝ちを1、負けを0、引き分けを0.5として返す。中断局などは-1。
    #[must_use]
    pub fn to_score(self, color: Color) -> f32 {
        if color == Color::BLACK {
            if self.is_black_win() {
                return 1.0;
            }
            if self.is_white_win() {
                return 0.0;
            }
        } else if color == Color::WHITE {
            if self.is_white_win() {
                return 1.0;
            }
            if self.is_black_win() {
                return 0.0;
            }
        }
        if self.is_draw() {
            return 0.5;
        }
        -1.0
    }

    /// 勝利した手番から結果を生成
    #[must_use]
    pub const fn win_from_color(color: Color) -> Self {
        if color.raw() == Color::BLACK.raw() {
            Self::BlackWin
        } else {
            Self::WhiteWin
        }
    }

    /// 宣言勝ちの結果を生成
    #[must_use]
    pub const fn win_by_declaration_from_color(color: Color) -> Self {
        if color.raw() == Color::BLACK.raw() {
            Self::BlackWinByDeclaration
        } else {
            Self::WhiteWinByDeclaration
        }
    }

    /// 不戦勝の結果を生成
    #[must_use]
    pub const fn win_by_forfeit_from_color(color: Color) -> Self {
        if color.raw() == Color::BLACK.raw() {
            Self::BlackWinByForfeit
        } else {
            Self::WhiteWinByForfeit
        }
    }

    /// 反則勝ちの結果を生成
    #[must_use]
    pub const fn win_by_illegal_move_from_color(color: Color) -> Self {
        if color.raw() == Color::BLACK.raw() {
            Self::BlackWinByIllegalMove
        } else {
            Self::WhiteWinByIllegalMove
        }
    }

    /// 時間切れ勝ちの結果を生成
    #[must_use]
    pub const fn win_by_timeout_from_color(color: Color) -> Self {
        if color.raw() == Color::BLACK.raw() {
            Self::BlackWinByTimeout
        } else {
            Self::WhiteWinByTimeout
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_game_result_winner() {
        assert_eq!(GameResult::BlackWin.winner_color(), Some(Color::BLACK));
        assert_eq!(GameResult::WhiteWinByTimeout.winner_color(), Some(Color::WHITE));
        assert_eq!(GameResult::DrawByRepetition.winner_color(), None);
    }

    #[test]
    fn test_game_result_flags() {
        assert!(GameResult::BlackWin.is_black_win());
        assert!(GameResult::WhiteWin.is_white_win());
        assert!(GameResult::DrawByMaxPlies.is_draw());
        assert!(GameResult::BlackWinByDeclaration.is_win_by_declaration());
        assert!(!GameResult::Paused.is_win());
    }

    #[test]
    fn test_game_result_score() {
        assert_eq!(GameResult::BlackWin.to_score(Color::BLACK), 1.0);
        assert_eq!(GameResult::BlackWin.to_score(Color::WHITE), 0.0);
        assert_eq!(GameResult::DrawByRepetition.to_score(Color::BLACK), 0.5);
        assert_eq!(GameResult::Paused.to_score(Color::BLACK), -1.0);
    }
}
