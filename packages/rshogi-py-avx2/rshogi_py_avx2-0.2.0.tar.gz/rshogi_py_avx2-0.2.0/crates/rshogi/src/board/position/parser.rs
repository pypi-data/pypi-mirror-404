use super::types::PackedPiece;
use super::Position;
use crate::board::material;
use crate::board::parser::{generate_sfen_with_ply, parse_sfen, SfenData, SfenError};
use crate::types::{Color, EnteringKingRule, Piece};

impl Position {
    /// SFEN文字列で盤面を設定する（既存局面の上書き）
    pub fn set(&mut self, sfen: &str) -> Result<(), SfenError> {
        let data = parse_sfen(sfen)?;
        self.apply_sfen_data(&data);
        Ok(())
    }

    /// 平手初期局面に設定する（YaneuraOu互換）
    pub fn set_hirate(&mut self) {
        let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
        self.set(sfen).expect("Invalid startpos SFEN");
    }

    fn apply_sfen_data(&mut self, data: &SfenData) {
        self.board = data.board;
        self.hands = data.hands;
        self.side_to_move = data.side_to_move;
        self.ply = data.ply;
        self.entering_king_rule = EnteringKingRule::None;
        self.entering_king_point = [0, 0];

        // ビットボードを再構築
        self.rebuild_bitboards();

        // PieceListを再構築
        self.rebuild_piece_list();

        // EvalListを再構築
        self.rebuild_eval_list();

        // Zobristハッシュを計算
        let keys = self.compute_keys();
        let (board_key, hand_key) = (keys.board_key, keys.hand_key);
        self.board_key = board_key;
        self.hand_key = hand_key;
        self.pawn_key = keys.pawn_key;
        self.minor_piece_key = keys.minor_piece_key;
        self.non_pawn_key = keys.non_pawn_key;
        self.material_key = keys.material_key;
        self.zobrist = board_key ^ hand_key;

        // StateStackをリセット
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
    }

    /// SFEN文字列に変換（YaneuraOu互換）。
    #[must_use]
    /// `None` の場合は現在の手数を使用する。
    /// `Some(x)` で負数を指定した場合は手数を出力しない。
    pub fn sfen(&self, game_ply: Option<i32>) -> String {
        let ply = game_ply.unwrap_or_else(|| i32::from(self.ply));
        let ply = if ply < 0 { None } else { Some(ply) };
        generate_sfen_with_ply(self, ply)
    }

    /// 先後反転（盤面を180度回転し、駒色と手番を反転）したSFENを取得
    #[must_use]
    /// `None` の場合は現在の手数を使用する。
    /// `Some(x)` で負数を指定した場合は手数を出力しない。
    pub fn flipped_sfen(&self, game_ply: Option<i32>) -> String {
        let mut flipped = Self::new();

        for (sq, packed) in self.board.iter() {
            if packed.is_empty() {
                continue;
            }
            let piece = packed.to_piece();
            let flipped_piece = Piece::make(piece.color().flip(), piece.piece_type());
            flipped.board.set(sq.inv(), PackedPiece::from_piece(flipped_piece));
        }

        flipped.hands[Color::BLACK.to_index()] = self.hands[Color::WHITE.to_index()];
        flipped.hands[Color::WHITE.to_index()] = self.hands[Color::BLACK.to_index()];
        flipped.side_to_move = self.side_to_move.flip();
        flipped.ply = self.ply;

        let ply = game_ply.unwrap_or_else(|| i32::from(self.ply));
        let ply = if ply < 0 { None } else { Some(ply) };
        generate_sfen_with_ply(&flipped, ply)
    }

    /// SFEN文字列を先後反転したSFENに変換する
    pub fn sfen_to_flipped_sfen(sfen: &str) -> Result<String, SfenError> {
        let mut pos = Self::new();
        pos.set(sfen)?;
        Ok(pos.flipped_sfen(None))
    }
}
