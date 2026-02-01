use crate::types::Bitboard;
use crate::types::{Color, Piece, PieceType, Square};

/// 駒種別・先後別のビットボード集合
#[derive(Clone, Copy, Debug, Default)]
pub struct BitboardSet {
    /// 駒種別のビットボード（先後の区別なし）
    pub by_piece: [Bitboard; PieceType::PIECE_TYPE_NB],

    /// 先後別の全駒ビットボード
    pub by_color: [Bitboard; Color::COLOR_NB],

    /// 全占有マス（両者の駒すべて）
    pub occupied: Bitboard,
}

impl BitboardSet {
    /// 空のビットボード集合を作成
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// 駒を配置（ビットボードを更新）
    pub fn set_piece(&mut self, sq: Square, piece_type: PieceType, color: Color) {
        self.by_piece[piece_type.to_index()].set(sq);
        self.by_color[color.to_index()].set(sq);
        self.occupied.set(sq);
    }

    /// 駒を除去（ビットボードを更新）
    pub fn clear_piece(&mut self, sq: Square, piece_type: PieceType, color: Color) {
        self.by_piece[piece_type.to_index()].clear(sq);
        self.by_color[color.to_index()].clear(sq);
        self.occupied.clear(sq);
    }

    /// 駒を移動（fromからtoへ）
    pub fn move_piece(&mut self, from: Square, to: Square, piece_type: PieceType, color: Color) {
        let piece_bb = &mut self.by_piece[piece_type.to_index()];
        piece_bb.clear(from);
        piece_bb.set(to);

        let color_bb = &mut self.by_color[color.to_index()];
        color_bb.clear(from);
        color_bb.set(to);

        self.occupied.clear(from);
        self.occupied.set(to);
    }

    /// 指定した駒種のビットボードを取得
    #[inline]
    #[must_use]
    pub const fn pieces(&self, piece_type: PieceType) -> Bitboard {
        self.by_piece[piece_type.to_index()]
    }

    /// 指定した先後の全駒ビットボードを取得
    #[inline]
    #[must_use]
    pub const fn color_pieces(&self, color: Color) -> Bitboard {
        self.by_color[color.to_index()]
    }

    /// 指定した先後・駒種のビットボードを取得
    #[inline]
    #[must_use]
    pub fn pieces_of(&self, piece_type: PieceType, color: Color) -> Bitboard {
        self.pieces(piece_type).and(self.color_pieces(color))
    }

    /// 金相当の駒（歩成りなどを含む）
    #[inline]
    #[must_use]
    pub fn golds(&self) -> Bitboard {
        self.pieces(PieceType::GOLD)
            | self.pieces(PieceType::PRO_PAWN)
            | self.pieces(PieceType::PRO_LANCE)
            | self.pieces(PieceType::PRO_KNIGHT)
            | self.pieces(PieceType::PRO_SILVER)
    }

    /// 馬・龍・玉（HDK）
    #[inline]
    #[must_use]
    pub fn hdk(&self) -> Bitboard {
        self.pieces(PieceType::HORSE)
            | self.pieces(PieceType::DRAGON)
            | self.pieces(PieceType::KING)
    }

    /// 角・馬（BISHOP_HORSE）
    #[inline]
    #[must_use]
    pub fn bishop_horse(&self) -> Bitboard {
        self.pieces(PieceType::BISHOP) | self.pieces(PieceType::HORSE)
    }

    /// 飛・龍（ROOK_DRAGON）
    #[inline]
    #[must_use]
    pub fn rook_dragon(&self) -> Bitboard {
        self.pieces(PieceType::ROOK) | self.pieces(PieceType::DRAGON)
    }

    /// 全占有マスを取得
    #[inline]
    #[must_use]
    pub const fn occupied(&self) -> Bitboard {
        self.occupied
    }

    /// 駒を配置（簡易版）
    pub fn set(&mut self, sq: Square, piece: Piece) {
        let piece_type = piece.piece_type();
        let color = piece.color();
        self.set_piece(sq, piece_type, color);
    }

    /// 駒を除去（簡易版）
    pub fn clear(&mut self, sq: Square, piece: Piece) {
        let piece_type = piece.piece_type();
        let color = piece.color();
        self.clear_piece(sq, piece_type, color);
    }

    /// 空きマスを取得
    #[inline]
    #[must_use]
    pub const fn empty(&self) -> Bitboard {
        self.occupied.not()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{Color, PieceType, SQ_16, SQ_17, SQ_82};

    #[test]
    fn test_bitboard_set_operations() {
        let mut bbs = BitboardSet::new();

        // 先手の歩を配置
        bbs.set_piece(SQ_17, PieceType::PAWN, Color::BLACK);
        assert!(bbs.pieces(PieceType::PAWN).test(SQ_17));
        assert!(bbs.color_pieces(Color::BLACK).test(SQ_17));
        assert!(bbs.occupied().test(SQ_17));

        // 後手の飛車を配置
        bbs.set_piece(SQ_82, PieceType::ROOK, Color::WHITE);
        assert!(bbs.pieces(PieceType::ROOK).test(SQ_82));
        assert!(bbs.color_pieces(Color::WHITE).test(SQ_82));

        // 先手の歩だけを取得
        let black_pawns = bbs.pieces_of(PieceType::PAWN, Color::BLACK);
        assert!(black_pawns.test(SQ_17));
        assert!(!black_pawns.test(SQ_82));

        // 駒を移動
        bbs.move_piece(SQ_17, SQ_16, PieceType::PAWN, Color::BLACK);
        assert!(!bbs.pieces(PieceType::PAWN).test(SQ_17));
        assert!(bbs.pieces(PieceType::PAWN).test(SQ_16));

        // 駒を除去
        bbs.clear_piece(SQ_82, PieceType::ROOK, Color::WHITE);
        assert!(!bbs.pieces(PieceType::ROOK).test(SQ_82));
        assert!(!bbs.occupied().test(SQ_82));
    }
}
