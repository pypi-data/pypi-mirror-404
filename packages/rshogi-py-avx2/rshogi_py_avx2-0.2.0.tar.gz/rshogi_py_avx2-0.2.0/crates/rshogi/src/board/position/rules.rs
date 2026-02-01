use super::types::Ply;
use super::Position;
use crate::board::attack_tables::KING_ATTACKS;
use crate::types::Bitboard;
use crate::types::{
    Color, EnteringKingRule, Hand, HandPiece, Move, Piece, PieceType, Rank, RepetitionState,
    Square, MOVE_NONE, MOVE_WIN, SQ_51, SQ_59,
};
use std::sync::atomic::{AtomicU16, Ordering};

/// 千日手判定で遡る最大手数（YaneuraOu互換）
const DEFAULT_MAX_REPETITION_PLY: Ply = 16;
static MAX_REPETITION_PLY: AtomicU16 = AtomicU16::new(DEFAULT_MAX_REPETITION_PLY);

#[inline]
fn max_repetition_ply() -> Ply {
    MAX_REPETITION_PLY.load(Ordering::Relaxed)
}

pub(in crate::board) struct RepetitionInfo {
    pub counter: i32,
    pub distance: i32,
    pub times: i32,
    pub rep_type: RepetitionState,
}

impl Position {
    /// 指定マスが指定色に攻撃されているか判定
    #[must_use]
    pub fn effected_to(&self, by_color: Color, sq: Square) -> bool {
        let occupied = self.bitboards().occupied();
        let attackers = self.attackers_to(sq, occupied);
        attackers.intersects(self.bitboards().color_pieces(by_color))
    }

    /// 指定マスが指定色に攻撃されているか判定（玉の移動用）
    #[must_use]
    pub fn effected_to_with_king(&self, by_color: Color, sq: Square, king_sq: Square) -> bool {
        let occupied = self.bitboards().occupied();
        let occupied_without_king = occupied.and_not(Bitboard::from_square(king_sq));
        let attackers = self.attackers_to(sq, occupied_without_king);
        attackers.intersects(self.bitboards().color_pieces(by_color))
    }

    /// 指定した手が王手をかけるか判定
    ///
    /// # Arguments
    /// * `m` - 判定対象の手
    ///
    /// # Returns
    /// 王手をかける場合`true`
    #[must_use]
    pub fn gives_check(&self, m: Move) -> bool {
        self.gives_check_with_check_squares(m, &self.check_squares_cache)
    }

    /// 指定した手が王手をかけるか判定（check_squares を利用）
    ///
    /// # Arguments
    /// * `m` - 判定対象の手
    /// * `check_squares` - 現局面の check_squares
    ///
    /// # Returns
    /// 王手をかける場合`true`
    #[must_use]
    pub fn gives_check_with_check_squares(
        &self,
        m: Move,
        check_squares: &[Bitboard; PieceType::PIECE_TYPE_NB],
    ) -> bool {
        let us = self.side_to_move();
        let them = us.flip();

        // 相手玉の位置を取得
        let king_sq = self.king_square(them);
        if king_sq.is_none() {
            return false; // 玉がない場合（異常な局面）
        }

        if m.is_drop() {
            // 打ち駒の場合
            let Some(piece_type) = m.dropped_piece() else {
                return false;
            };
            let to = m.to_sq();

            // 打った駒が直接王手をかけるか確認
            check_squares[piece_type.to_index()].test(to)
        } else {
            // 移動手の場合
            let from = m.from_sq();
            let to = m.to_sq();
            let piece = self.piece_on(from);
            if piece == Piece::NO_PIECE {
                return false;
            }
            let moved_pt =
                if m.is_promote() { piece.piece_type().promote() } else { piece.piece_type() };

            // 1) 直接王手: 移動後の駒が敵玉に利くか
            let direct_check = check_squares[moved_pt.to_index()].test(to);

            // 2) 開き王手: 移動元が敵玉へのスライダーのブロッカーで、移動が玉と直線上でない
            // YaneuraOu互換: blockers_for_king[them] と aligned(from,to,king) で判定
            let discovered_check =
                self.blockers_for_king(them).test(from) && !Bitboard::line(from, king_sq).test(to);

            direct_check || discovered_check
        }
    }

    /// from->to の移動が空き王手になるかを判定する（YaneuraOu互換）。
    #[must_use]
    pub fn discovered(&self, from: Square, to: Square, our_king: Square, pinned: Bitboard) -> bool {
        pinned.test(from) && !Bitboard::line(from, our_king).test(to)
    }

    /// 捕獲する指し手かどうか
    #[must_use]
    pub fn capture(&self, m: Move) -> bool {
        debug_assert!(m.is_ok(), "capture expects a normal move");
        !m.is_drop() && self.piece_on(m.to_sq()) != Piece::NO_PIECE
    }

    /// 捕獲または成りの指し手かどうか
    #[must_use]
    pub fn capture_or_promotion(&self, m: Move) -> bool {
        m.is_promote() || self.capture(m)
    }

    /// 歩の成り指し手かどうか
    #[must_use]
    pub fn pawn_promotion(&self, m: Move) -> bool {
        m.is_promote() && m.moved_after_piece().piece_type().demote() == PieceType::PAWN
    }

    /// 捕獲または歩の成り指し手かどうか
    #[must_use]
    pub fn capture_or_pawn_promotion(&self, m: Move) -> bool {
        self.pawn_promotion(m) || self.capture(m)
    }

    /// 捕獲または価値のある駒の成り（歩・角・飛）かどうか
    #[must_use]
    pub fn capture_or_valuable_promotion(&self, m: Move) -> bool {
        if m.is_promote() {
            let raw = m.moved_after_piece().piece_type().demote();
            if matches!(raw, PieceType::PAWN | PieceType::BISHOP | PieceType::ROOK) {
                return true;
            }
        }
        self.capture(m)
    }

    /// MovePickerのcapture段階で生成される指し手かどうか
    #[must_use]
    pub fn capture_stage(&self, m: Move) -> bool {
        self.capture(m)
    }

    /// 指定された手が合法かどうかを判定（自殺手チェックのみ）。
    #[must_use]
    pub fn legal(&self, m: Move) -> bool {
        if m.is_drop() {
            return true;
        }

        let us = self.side_to_move();
        let from = m.from_sq();
        let to = m.to_sq();
        let piece = self.piece_on(from);
        if piece.piece_type() == PieceType::KING {
            return self.is_legal_king_move(us, from, to);
        }

        self.is_legal_non_king_move(us, from, to)
    }

    fn is_legal_king_move(&self, us: Color, from: Square, to: Square) -> bool {
        !self.effected_to_with_king(us.flip(), to, from)
    }

    fn is_legal_non_king_move(&self, us: Color, from: Square, to: Square) -> bool {
        let pinned = self.blockers_for_king(us);
        if !pinned.test(from) {
            return true;
        }
        let king_sq = self.king_square(us);
        if king_sq.is_none() {
            return true;
        }
        Bitboard::line(king_sq, from).test(to)
    }

    #[inline]
    pub(super) fn can_promote(from: Square, to: Square, us: Color) -> bool {
        let from_rank = from.rank().raw();
        let to_rank = to.rank().raw();

        match us {
            Color::BLACK => from_rank <= 2 || to_rank <= 2,
            Color::WHITE => from_rank >= 6 || to_rank >= 6,
            _ => false,
        }
    }

    /// 成りの条件を満たしているか判定する。
    #[must_use]
    pub fn legal_promote(&self, m: Move) -> bool {
        if !m.is_promote() {
            return true;
        }
        let us = self.side_to_move();
        let from = m.from_sq();
        let to = m.to_sq();
        Self::can_promote(from, to, us)
    }

    /// 指定された手が合法かどうかを判定（pseudo-legal + 自殺手チェック）。
    #[must_use]
    pub fn is_legal(&self, m: Move) -> bool {
        self.pseudo_legal(m, true) && self.legal_promote(m) && self.legal(m)
    }

    pub(crate) fn legal_pawn_drop(&self, us: Color, to: Square) -> bool {
        use crate::board::attack_tables::PAWN_ATTACKS;

        let file_bb = Bitboard::file_mask(to.file());
        let nifu = !self.bitboards().pieces_of(PieceType::PAWN, us).and(file_bb).is_empty();
        if nifu {
            return false;
        }

        let them = us.flip();
        let king_sq = self.king_square(them);
        if king_sq.is_none() {
            return true;
        }
        let pawn_effect = PAWN_ATTACKS[to.to_index()][us.to_index()];
        if pawn_effect.test(king_sq) && !self.legal_drop(to) {
            return false;
        }

        true
    }

    pub(crate) fn legal_drop(&self, to: Square) -> bool {
        use crate::board::attack_tables::KING_ATTACKS;

        let us = self.side_to_move();
        let them = us.flip();

        if !self.is_attacked_by(to, us) {
            return true;
        }

        let attackers = self.attackers_to_pawn(them, to);
        let pinned = self.blockers_for_king(them);
        let file_bb = Bitboard::file_mask(to.file());
        if !attackers.and(pinned.not().or(file_bb)).is_empty() {
            return true;
        }

        let king_sq = self.king_square(them);
        if king_sq.is_none() {
            return true;
        }
        let mut escape_bb =
            KING_ATTACKS[king_sq.to_index()].and_not(self.bitboards().color_pieces(them));
        escape_bb.clear(to);

        let mut occupied = self.bitboards().occupied();
        occupied.set(to);

        while let Some(king_to) = escape_bb.pop_lsb() {
            let attackers =
                self.attackers_to(king_to, occupied) & self.bitboards().color_pieces(us);
            if attackers.is_empty() {
                return true;
            }
        }

        false
    }

    pub(in crate::board) fn compute_repetition_info(
        &self,
        stack: &crate::board::state_info::StateStack,
        current_idx: crate::board::state_info::StateIndex,
        plies_from_null: Ply,
    ) -> RepetitionInfo {
        if plies_from_null < 4 {
            return RepetitionInfo {
                counter: 0,
                distance: 0,
                times: 0,
                rep_type: RepetitionState::None,
            };
        }

        let limit = plies_from_null.min(max_repetition_ply());
        let mut distance: Ply = 0;
        let mut repetition_counter: i32 = 0;
        let mut repetition_distance: i32 = 0;
        let mut repetition_times: i32 = 0;
        let mut repetition_type = RepetitionState::None;
        let mut idx_opt = stack.get(current_idx).prev;

        let current_state = stack.get(current_idx);
        let current_hand = current_state.hand;
        let current_continuous_check = current_state.continuous_check;
        let current_board_key = self.board_key;

        while let Some(idx) = idx_opt {
            distance += 1;
            if distance > limit {
                break;
            }

            let state = stack.get(idx);

            if distance >= 4 && distance % 2 == 0 {
                if state.board_key == current_board_key {
                    if state.hand == current_hand {
                        repetition_times = state.repetition_times + 1;
                        repetition_counter = repetition_times;
                        repetition_distance = if repetition_times >= 3 {
                            -i32::from(distance)
                        } else {
                            i32::from(distance)
                        };

                        let us = self.side_to_move;
                        repetition_type = if distance <= current_continuous_check[us.to_index()] {
                            RepetitionState::Lose
                        } else if distance <= current_continuous_check[us.flip().to_index()] {
                            RepetitionState::Win
                        } else {
                            RepetitionState::Draw
                        };

                        if state.repetition_times > 0 && repetition_type != state.repetition_type {
                            repetition_type = RepetitionState::Draw;
                        }
                        break;
                    }

                    if Hand::hand_is_equal_or_superior(current_hand, state.hand) {
                        repetition_type = RepetitionState::Superior;
                        repetition_distance = i32::from(distance);
                        break;
                    }

                    if Hand::hand_is_equal_or_superior(state.hand, current_hand) {
                        repetition_type = RepetitionState::Inferior;
                        repetition_distance = i32::from(distance);
                        break;
                    }
                }

                if state.plies_from_null == 0 {
                    break;
                }
            }

            idx_opt = state.prev;
        }

        RepetitionInfo {
            counter: repetition_counter,
            distance: repetition_distance,
            times: repetition_times,
            rep_type: repetition_type,
        }
    }

    /// 千日手判定
    ///
    /// 現在の局面が指定回数以上繰り返されているかをチェック
    ///
    /// # Arguments
    /// * `threshold` - 千日手と判定する繰り返し回数（通常は3）
    #[must_use]
    pub fn is_repetition(&self, threshold: u8) -> bool {
        if threshold == 0 {
            return true;
        }

        let stack = self.state_stack();
        stack.get(self.st_index).repetition_counter >= i32::from(threshold)
    }

    /// 千日手の詳細な状態を判定（探索用、ply制約付き）
    ///
    /// YaneuraOu互換: `Position::is_repetition(int ply)` と同等の機能を提供。
    /// 同一局面の繰り返しを検出し、連続王手の千日手や優等/劣等局面も判定する。
    ///
    /// # Arguments
    /// * `stack` - 状態スタック
    /// * `ply` - rootからの手数（この手数以内に遡って検出）
    ///
    /// # Returns
    /// * `RepetitionState::None`: 千日手ではない、または ply 手以内に遡っても検出されなかった
    /// * その他: 千日手の状態（Win/Lose/Draw/Superior/Inferior）
    ///
    /// # 実装詳細
    /// - `repetition_counter >= 3` の場合は ply に関わらず千日手を検出（強制的に打ち切る必要があるため）
    /// - そうでない場合は、最大でも `min(ply, plies_from_null, max_repetition_ply)` まで遡って検出
    #[must_use]
    pub fn get_repetition_state_with_ply(&self, ply: usize) -> RepetitionState {
        let stack = self.state_stack();
        // 千日手判定の前提条件：repetition_counter >= 3（4回目の出現）
        // 4回目の同一局面の場合は強制的に千日手となるため、plyに関わらず検出
        if stack.get(self.st_index).repetition_counter >= 3 {
            return self.get_repetition_state();
        }

        // 遡り可能な手数を計算
        // YaneuraOu互換: min(ply, plies_from_null, max_repetition_ply)
        let plies_from_null = stack.get(self.st_index).plies_from_null;
        let ply_limit = ply.min(plies_from_null as usize).min(max_repetition_ply() as usize);

        // 少なくとも4手かけないと千日手にはならない
        if ply_limit < 4 {
            return RepetitionState::None;
        }

        let current_state = stack.get(self.st_index);
        let current_hand = current_state.hand;
        let current_continuous_check = current_state.continuous_check;
        let current_board_key = self.board_key;

        // スタックを遡って同一局面を検索
        // 4手前から、2手ずつ遡る（同一局面に戻るためには偶数手必要）
        let mut idx_opt = current_state.prev;
        let mut distance = 1usize;

        while let Some(idx) = idx_opt {
            if distance > ply_limit {
                break;
            }

            let state = stack.get(idx);

            // 4手以上遡り、かつ偶数手の場合のみチェック
            if distance >= 4 && distance % 2 == 0 {
                if state.board_key == current_board_key {
                    if state.hand == current_hand {
                        let us = self.side_to_move;
                        let repetition_type =
                            if distance <= usize::from(current_continuous_check[us.to_index()]) {
                                RepetitionState::Lose
                            } else if distance
                                <= usize::from(current_continuous_check[us.flip().to_index()])
                            {
                                RepetitionState::Win
                            } else {
                                RepetitionState::Draw
                            };

                        if state.repetition_times > 0 && repetition_type != state.repetition_type {
                            return RepetitionState::Draw;
                        }

                        return repetition_type;
                    }

                    if Hand::hand_is_equal_or_superior(current_hand, state.hand) {
                        return RepetitionState::Superior;
                    }

                    if Hand::hand_is_equal_or_superior(state.hand, current_hand) {
                        return RepetitionState::Inferior;
                    }
                }

                // plies_from_null == 0 に到達したら終了
                if state.plies_from_null == 0 {
                    break;
                }
            }

            distance += 1;
            idx_opt = state.prev;
        }

        RepetitionState::None
    }

    /// 千日手の詳細な状態を判定（YaneuraOu互換名）。
    #[must_use]
    pub fn is_repetition_with_ply(&self, ply: usize) -> RepetitionState {
        self.get_repetition_state_with_ply(ply)
    }

    /// 千日手の詳細な状態を判定（YaneuraOu互換）
    ///
    /// 同一局面の繰り返しを検出し、連続王手の千日手や優等/劣等局面も判定する。
    #[must_use]
    pub fn get_repetition_state(&self) -> RepetitionState {
        let stack = self.state_stack();
        let current_state = stack.get(self.st_index);
        let repetition_type = current_state.repetition_type;

        if matches!(repetition_type, RepetitionState::Superior | RepetitionState::Inferior) {
            return repetition_type;
        }

        if current_state.repetition_counter >= 3 {
            return repetition_type;
        }

        RepetitionState::None
    }

    /// 千日手の詳細な状態を判定（YaneuraOu互換名）。
    #[must_use]
    pub fn is_repetition_state(&self) -> RepetitionState {
        self.get_repetition_state()
    }

    /// 千日手判定で遡る最大手数を設定する（YaneuraOu互換）。
    pub fn set_max_repetition_ply(&self, ply: Ply) {
        MAX_REPETITION_PLY.store(ply, Ordering::Relaxed);
    }

    /// 千日手があったかを判定する（YaneuraOu互換）。
    #[must_use]
    pub fn has_repeated(&self) -> bool {
        let stack = self.state_stack();
        let current_state = stack.get(self.st_index);
        let limit = max_repetition_ply().min(current_state.plies_from_null);
        let mut remaining = i32::from(limit);
        let mut idx_opt = Some(self.st_index);

        while remaining >= 4 {
            if let Some(idx) = idx_opt {
                let state = stack.get(idx);
                if state.repetition_distance != 0 {
                    return true;
                }
                idx_opt = state.prev;
            } else {
                break;
            }
            remaining -= 1;
        }

        false
    }

    /// 千日手の種類と検出距離を返す（YaneuraOu互換）。
    #[must_use]
    pub fn get_repetition_state_with_found_ply(&self, ply: usize) -> (RepetitionState, usize) {
        let stack = self.state_stack();
        let current_state = stack.get(self.st_index);

        let ply_u32 = u32::try_from(ply).unwrap_or(u32::MAX);
        if current_state.repetition_distance != 0
            && current_state.repetition_distance.unsigned_abs() < ply_u32
        {
            let found = usize::try_from(current_state.repetition_distance.unsigned_abs())
                .unwrap_or(usize::MAX);
            return (current_state.repetition_type, found);
        }

        (RepetitionState::None, 0)
    }

    /// 宣言勝ち判定
    #[must_use]
    pub fn declaration_win(&self) -> Move {
        match self.entering_king_rule {
            EnteringKingRule::None | EnteringKingRule::Unset => {
                return MOVE_NONE;
            }
            EnteringKingRule::TryRule => {
                let us = self.side_to_move;
                let king_try_sq = if us == Color::BLACK { SQ_51 } else { SQ_59 };
                let king_sq = self.king_square(us);
                if king_sq.is_none() {
                    return MOVE_NONE;
                }

                if !KING_ATTACKS[king_sq.to_index()].test(king_try_sq) {
                    return MOVE_NONE;
                }
                if self.bitboards().color_pieces(us).test(king_try_sq) {
                    return MOVE_NONE;
                }
                if self.effected_to_with_king(us.flip(), king_try_sq, king_sq) {
                    return MOVE_NONE;
                }

                return Move::make(king_sq, king_try_sq, Piece::make(us, PieceType::KING));
            }
            EnteringKingRule::Point24
            | EnteringKingRule::Point24Handicap
            | EnteringKingRule::Point27
            | EnteringKingRule::Point27Handicap => {}
        }

        let us = self.side_to_move;

        // 条件5: 玉に王手がかかっていない
        if !self.checkers().is_empty() {
            return MOVE_NONE;
        }

        // 条件1: 宣言側の手番である（自明）

        // 玉の位置を取得
        let king_sq = self.king_square(us);
        if king_sq.is_none() {
            return MOVE_NONE; // 玉がない場合（異常な局面）
        }

        // 条件2: 宣言側の玉が敵陣三段目以内に入っている
        // 先手（BLACK）の敵陣 = 後手の陣地1-3段目 = rank 0-2（内部表現）
        // 後手（WHITE）の敵陣 = 先手の陣地1-3段目 = rank 6-8（内部表現）
        let king_rank = king_sq.rank();
        let in_enemy_camp = match us {
            Color::BLACK => king_rank.0 <= 2, // 後手の1-3段目（rank 0-2）
            Color::WHITE => king_rank.0 >= 6, // 先手の1-3段目（rank 6-8）
            _ => unreachable!("invalid color"),
        };

        if !in_enemy_camp {
            return MOVE_NONE;
        }

        // 条件3と4: 持点計算と駒数カウント
        let hand = self.hand_of(us);
        let mut points: i32 = 0;

        // 持ち駒の点数計算（点数のみ、駒数は敵陣の駒だけ）
        let hand_pieces = [
            (HandPiece::HAND_ROOK, PieceType::ROOK, 5),
            (HandPiece::HAND_BISHOP, PieceType::BISHOP, 5),
            (HandPiece::HAND_GOLD, PieceType::GOLD, 1),
            (HandPiece::HAND_SILVER, PieceType::SILVER, 1),
            (HandPiece::HAND_KNIGHT, PieceType::KNIGHT, 1),
            (HandPiece::HAND_LANCE, PieceType::LANCE, 1),
            (HandPiece::HAND_PAWN, PieceType::PAWN, 1),
        ];

        for (hand_piece, _, value) in hand_pieces {
            let count = i32::try_from(hand.count(hand_piece)).expect("hand count fits in i32");
            points += count * value;
            // 持ち駒は点数に加算するが、駒数には加算しない
        }

        // 盤上の敵陣三段目以内の駒をカウント（玉を除く）
        // 先手（BLACK）の敵陣 = 後手の陣地1-3段目 = rank 0-2（内部表現）
        // 後手（WHITE）の敵陣 = 先手の陣地1-3段目 = rank 6-8（内部表現）
        let enemy_camp_mask = match us {
            Color::BLACK => {
                // 後手の1-3段目（rank 0-2）
                Bitboard::rank_mask(Rank::new(0))
                    | Bitboard::rank_mask(Rank::new(1))
                    | Bitboard::rank_mask(Rank::new(2))
            }
            Color::WHITE => {
                // 先手の1-3段目（rank 6-8）
                Bitboard::rank_mask(Rank::new(6))
                    | Bitboard::rank_mask(Rank::new(7))
                    | Bitboard::rank_mask(Rank::new(8))
            }
            _ => unreachable!("invalid color"),
        };

        let our_pieces_in_camp = self.bitboards().color_pieces(us) & enemy_camp_mask;
        let p1 = i32::try_from(our_pieces_in_camp.count()).expect("camp piece count fits in i32");
        if p1 < 11 {
            return MOVE_NONE;
        }

        let majors_in_camp = (self.bitboards().pieces_of(PieceType::BISHOP, us)
            | self.bitboards().pieces_of(PieceType::HORSE, us)
            | self.bitboards().pieces_of(PieceType::ROOK, us)
            | self.bitboards().pieces_of(PieceType::DRAGON, us))
            & enemy_camp_mask;
        let p2 = i32::try_from(majors_in_camp.count()).expect("camp major count fits in i32");

        points += p1 + p2 * 4 - 1;

        let required_points = self.entering_king_point[us.to_index()];
        if points >= required_points {
            MOVE_WIN
        } else {
            MOVE_NONE
        }
    }

    pub fn set_ekr(&mut self, rule: EnteringKingRule) {
        self.entering_king_rule = rule;
        self.update_entering_point();
    }

    pub(super) fn update_entering_point(&mut self) {
        let mut points = [0i32; Color::COLOR_NB];

        match self.entering_king_rule {
            EnteringKingRule::Point24 | EnteringKingRule::Point24Handicap => {
                points[Color::BLACK.to_index()] = 31;
                points[Color::WHITE.to_index()] = 31;
            }
            EnteringKingRule::Point27 | EnteringKingRule::Point27Handicap => {
                points[Color::BLACK.to_index()] = 28;
                points[Color::WHITE.to_index()] = 27;
            }
            EnteringKingRule::Unset | EnteringKingRule::None | EnteringKingRule::TryRule => {
                return;
            }
        }

        let p1 =
            i32::try_from(self.bitboards().occupied().count()).expect("piece count fits in i32");
        let majors = self.bitboards().pieces(PieceType::BISHOP)
            | self.bitboards().pieces(PieceType::HORSE)
            | self.bitboards().pieces(PieceType::ROOK)
            | self.bitboards().pieces(PieceType::DRAGON);
        let p2 = i32::try_from(majors.count()).expect("major count fits in i32");

        let mut total = p1 + p2 * 4;

        for color in [Color::BLACK, Color::WHITE] {
            let hand = self.hands[color.to_index()];
            total +=
                i32::try_from(hand.count(HandPiece::HAND_PAWN)).expect("pawn count fits in i32");
            total +=
                i32::try_from(hand.count(HandPiece::HAND_LANCE)).expect("lance count fits in i32");
            total += i32::try_from(hand.count(HandPiece::HAND_KNIGHT))
                .expect("knight count fits in i32");
            total += i32::try_from(hand.count(HandPiece::HAND_SILVER))
                .expect("silver count fits in i32");
            total +=
                i32::try_from(hand.count(HandPiece::HAND_GOLD)).expect("gold count fits in i32");
            total += i32::try_from(hand.count(HandPiece::HAND_BISHOP))
                .expect("bishop count fits in i32")
                * 5;
            total += i32::try_from(hand.count(HandPiece::HAND_ROOK))
                .expect("rook count fits in i32")
                * 5;
        }

        if total != 56
            && matches!(
                self.entering_king_rule,
                EnteringKingRule::Point24Handicap | EnteringKingRule::Point27Handicap
            )
        {
            points[Color::WHITE.to_index()] -= 56 - total;
        }

        self.entering_king_point = points;
    }

    /// 現局面で指し手がないかをテストする
    #[must_use]
    pub fn is_mated(&self) -> bool {
        use crate::board::movegen::{generate_moves, Legal};
        use crate::board::MoveList;

        let mut list = MoveList::new();
        generate_moves::<Legal>(self, &mut list);
        list.is_empty()
    }
}
