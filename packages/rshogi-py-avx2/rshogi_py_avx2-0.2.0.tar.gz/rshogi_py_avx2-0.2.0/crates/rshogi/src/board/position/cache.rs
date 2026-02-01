use super::Position;
use crate::board::state_info::StateInfo;
use crate::types::Bitboard;
use crate::types::{Color, PieceType, Square};

impl Position {
    /// 現在王手をかけている駒のBitboardを返す
    ///
    /// # Returns
    /// 手番側の玉に王手をかけている駒のBitboard
    #[must_use]
    pub const fn checkers(&self) -> Bitboard {
        self.checkers_cache
    }

    /// check_squares のキャッシュを取得
    #[must_use]
    pub const fn check_squares_cache(&self) -> &[Bitboard; PieceType::PIECE_TYPE_NB] {
        &self.check_squares_cache
    }

    /// 指定した駒種の check_squares を取得
    #[must_use]
    pub const fn check_squares(&self, piece_type: PieceType) -> Bitboard {
        self.check_squares_cache[piece_type.to_index()]
    }

    /// ピンされている駒のBitboardを返す（キャッシュ済み）
    #[must_use]
    pub fn pinned_pieces(&self, c: Color) -> Bitboard {
        self.blockers_for_king[c.to_index()].and(self.bitboards.color_pieces(c))
    }

    /// 回避対象を除外してピンされている駒を返す（YaneuraOu互換）。
    #[must_use]
    pub fn pinned_pieces_avoid(&self, c: Color, avoid: Square) -> Bitboard {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};

        let king_sq = self.king_square(c);
        if king_sq.is_none() {
            return Bitboard::EMPTY;
        }

        let them = c.flip();
        let rook_like = self.bitboards().pieces_of(PieceType::ROOK, them)
            | self.bitboards().pieces_of(PieceType::DRAGON, them);
        let bishop_like = self.bitboards().pieces_of(PieceType::BISHOP, them)
            | self.bitboards().pieces_of(PieceType::HORSE, them);
        let lance_like = self.bitboards().pieces_of(PieceType::LANCE, them);

        let avoid_bb =
            if avoid.is_none() { Bitboard::ALL } else { Bitboard::from_square(avoid).not() };
        let rook_snipers = rook_like & rook_attacks(king_sq, Bitboard::EMPTY) & avoid_bb;
        let bishop_snipers = bishop_like & bishop_attacks(king_sq, Bitboard::EMPTY) & avoid_bb;
        let lance_snipers = lance_like & lance_attacks(king_sq, Bitboard::EMPTY, c) & avoid_bb;

        let snipers = rook_snipers | bishop_snipers | lance_snipers;
        let occupancy = self.bitboards().occupied() & avoid_bb;
        let mut result = Bitboard::EMPTY;

        for sniper_sq in &snipers {
            let between = Bitboard::between(sniper_sq, king_sq) & occupancy;
            if between.count() == 1 {
                result = result | (between & self.bitboards.color_pieces(c));
            }
        }

        result
    }

    /// from->to の移動を仮定したピン状態を返す（YaneuraOu互換）。
    #[must_use]
    pub fn pinned_pieces_after_move(&self, c: Color, from: Square, to: Square) -> Bitboard {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};

        let king_sq = self.king_square(c);
        if king_sq.is_none() {
            return Bitboard::EMPTY;
        }

        let them = c.flip();
        let rook_like = self.bitboards().pieces_of(PieceType::ROOK, them)
            | self.bitboards().pieces_of(PieceType::DRAGON, them);
        let bishop_like = self.bitboards().pieces_of(PieceType::BISHOP, them)
            | self.bitboards().pieces_of(PieceType::HORSE, them);
        let lance_like = self.bitboards().pieces_of(PieceType::LANCE, them);

        let avoid_bb =
            if from.is_none() { Bitboard::ALL } else { Bitboard::from_square(from).not() };
        let rook_snipers = rook_like & rook_attacks(king_sq, Bitboard::EMPTY) & avoid_bb;
        let bishop_snipers = bishop_like & bishop_attacks(king_sq, Bitboard::EMPTY) & avoid_bb;
        let lance_snipers = lance_like & lance_attacks(king_sq, Bitboard::EMPTY, c) & avoid_bb;

        let snipers = rook_snipers | bishop_snipers | lance_snipers;
        let mut occupancy = self.bitboards().occupied() & avoid_bb;
        if !to.is_none() {
            occupancy = occupancy | Bitboard::from_square(to);
        }

        let mut result = Bitboard::EMPTY;
        for sniper_sq in &snipers {
            let between = Bitboard::between(sniper_sq, king_sq) & occupancy;
            if between.count() == 1 {
                result = result | (between & self.bitboards.color_pieces(c));
            }
        }

        result
    }

    /// 玉を守っているブロッカー（pin候補を含む）を返す
    #[must_use]
    pub const fn blockers_for_king(&self, c: Color) -> Bitboard {
        self.blockers_for_king[c.to_index()]
    }

    /// 玉に対してピンしている敵の大駒を返す
    #[must_use]
    pub const fn pinners(&self, c: Color) -> Bitboard {
        self.pinners_cache[c.to_index()]
    }

    /// 現局面で王手がかかっているかを返す（YaneuraOu互換）。
    #[must_use]
    pub const fn in_check(&self) -> bool {
        !self.checkers().is_empty()
    }

    /// 指し手が空き王手になる候補かを判定する（YaneuraOu互換）。
    #[must_use]
    pub fn is_discovery_check_on_king(&self, c: Color, mv: crate::types::Move) -> bool {
        self.blockers_for_king(c).test(mv.from_sq())
    }

    /// check_squares を計算する（YaneuraOu互換）
    /// 各駒種について、その駒を配置すると敵玉に王手となるマスのビットボードを計算
    pub(crate) fn compute_check_squares(&self) -> [Bitboard; PieceType::PIECE_TYPE_NB] {
        use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};
        use crate::board::attack_tables::{
            GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS, PAWN_ATTACKS, SILVER_ATTACKS,
        };

        let mut check_squares = [Bitboard::EMPTY; PieceType::PIECE_TYPE_NB];

        // 敵玉の位置を取得
        let them = self.side_to_move.flip();
        let ksq = self.king_square(them);
        if ksq.is_none() {
            // 玉がない場合は空のビットボードを返す
            return check_squares;
        }

        let occupied = self.bitboards().occupied();

        // 各駒種について、敵玉から逆向きに攻撃範囲を計算
        // YaneuraOuの set_check_info() 実装に基づく
        check_squares[PieceType::PAWN.to_index()] = PAWN_ATTACKS[ksq.to_index()][them.to_index()];
        check_squares[PieceType::KNIGHT.to_index()] =
            KNIGHT_ATTACKS[ksq.to_index()][them.to_index()];
        check_squares[PieceType::SILVER.to_index()] =
            SILVER_ATTACKS[ksq.to_index()][them.to_index()];
        check_squares[PieceType::GOLD.to_index()] = GOLD_ATTACKS[ksq.to_index()][them.to_index()];
        check_squares[PieceType::BISHOP.to_index()] = bishop_attacks(ksq, occupied);
        check_squares[PieceType::ROOK.to_index()] = rook_attacks(ksq, occupied);

        // 香は飛車の利きを香のstep effectでマスク
        check_squares[PieceType::LANCE.to_index()] =
            check_squares[PieceType::ROOK.to_index()] & lance_attacks(ksq, Bitboard::EMPTY, them);

        // 玉を移動させて直接王手になることはない（自殺手）
        check_squares[PieceType::KING.to_index()] = Bitboard::EMPTY;

        // 成り駒の check_squares を設定
        check_squares[PieceType::PRO_PAWN.to_index()] = check_squares[PieceType::GOLD.to_index()];
        check_squares[PieceType::PRO_LANCE.to_index()] = check_squares[PieceType::GOLD.to_index()];
        check_squares[PieceType::PRO_KNIGHT.to_index()] = check_squares[PieceType::GOLD.to_index()];
        check_squares[PieceType::PRO_SILVER.to_index()] = check_squares[PieceType::GOLD.to_index()];
        check_squares[PieceType::HORSE.to_index()] =
            check_squares[PieceType::BISHOP.to_index()] | KING_ATTACKS[ksq.to_index()];
        check_squares[PieceType::DRAGON.to_index()] =
            check_squares[PieceType::ROOK.to_index()] | KING_ATTACKS[ksq.to_index()];

        check_squares
    }

    pub(super) fn compute_checkers_for(&self, color: Color) -> Bitboard {
        let us = color;
        let them = us.flip();
        let occupied = self.bitboards.occupied();

        let king_sq = self.king_square(us);
        if king_sq.is_none() {
            return Bitboard::EMPTY;
        }

        let attackers = self.attackers_to(king_sq, occupied);
        attackers.and(self.bitboards.color_pieces(them))
    }

    pub(super) fn recompute_caches(&mut self) {
        let mut state = StateInfo::default();
        self.compute_caches_for_state(&mut state);
        self.sync_caches_from_state(&state);
    }

    pub(crate) fn compute_caches_for_state(&self, state: &mut StateInfo) {
        for color in [Color::BLACK, Color::WHITE] {
            let (blockers, pinners) = self.compute_slider_info(color);
            state.blockers_for_king[color.to_index()] = blockers;
            state.pinners[color.to_index()] = pinners;
        }

        state.checkers = self.compute_checkers_for(self.side_to_move);
        state.check_squares = self.compute_check_squares();
    }

    pub(crate) fn compute_caches_for_state_no_checkers(&self, state: &mut StateInfo) {
        for color in [Color::BLACK, Color::WHITE] {
            let (blockers, pinners) = self.compute_slider_info(color);
            state.blockers_for_king[color.to_index()] = blockers;
            state.pinners[color.to_index()] = pinners;
        }

        state.check_squares = self.compute_check_squares();
    }

    pub(crate) fn sync_caches_from_state(&mut self, state: &StateInfo) {
        self.checkers_cache = state.checkers;
        self.check_squares_cache = state.check_squares;
        self.pinners_cache = state.pinners;
        self.blockers_for_king = state.blockers_for_king;
    }
}
