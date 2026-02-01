use super::types::Ply;
use super::Position;
use crate::board::bitboard_set::BitboardSet;
use crate::board::eval_list::EvalList;
use crate::board::piece_list::PieceList;
use crate::board::zobrist::ZobristKey;
use crate::types::{Bitboard, Color, File, Hand, Move, Piece, PieceType, Square};

impl Position {
    /// 指定マスのPieceを取得（YaneuraOu互換名）。
    #[inline]
    #[must_use]
    pub fn piece_on(&self, sq: Square) -> Piece {
        if sq.is_none() {
            return Piece::NO_PIECE;
        }
        self.board.get(sq).to_piece()
    }

    /// 指定マスが空かどうかを返す（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn empty(&self, sq: Square) -> bool {
        self.piece_on(sq) == Piece::NO_PIECE
    }

    /// 駒がない升が1になっているBitboardを返す（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn empties(&self) -> Bitboard {
        !self.bitboards().occupied()
    }

    /// 持ち駒を取得（YaneuraOu互換名）。
    #[inline]
    #[must_use]
    pub const fn hand_of(&self, color: Color) -> Hand {
        self.hands[color.to_index()]
    }

    /// 持ち駒を取得（const-generic版）。
    #[must_use]
    pub fn hand_of_const<const C: i8>(&self) -> Hand {
        let color = Color::new(C);
        debug_assert!(color.is_ok(), "invalid color");
        self.hand_of(color)
    }

    /// 手番を取得
    #[inline]
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.side_to_move
    }

    /// 指定色の玉の位置を取得
    #[inline]
    #[must_use]
    pub const fn king_square(&self, color: Color) -> Square {
        self.king_square[color.to_index()]
    }

    /// 指定色・駒種の場所を取得（YaneuraOu互換、KING専用）。
    #[must_use]
    pub fn square(&self, color: Color, piece_type: PieceType) -> Square {
        debug_assert!(
            piece_type == PieceType::KING,
            "Position::square only supports KING in shogi mode"
        );
        self.king_square(color)
    }

    /// 指定筋に指定色の歩が存在するか判定（二歩判定用）
    #[must_use]
    pub fn has_pawn_on_file(&self, color: Color, file: File) -> bool {
        use crate::types::PieceType;

        // 指定色の歩のBitboardを取得
        let pawns = self.bitboards.pieces_of(PieceType::PAWN, color);

        // 指定筋のBitboardを作成
        let file_mask = Bitboard::file_mask(file);

        // 交差判定
        !(pawns & file_mask).is_empty()
    }

    /// Null move pruningのガード用に、歩以外の駒が残っているかを判定する。
    /// 平手初期局面からの手数を取得（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn game_ply(&self) -> Ply {
        self.ply
    }

    /// 局面のキーを取得（YaneuraOu互換名）。
    #[inline]
    #[must_use]
    pub fn key(&self) -> ZobristKey {
        self.board_key ^ self.hand_key
    }

    /// 指し手で移動させる駒（移動前）を返す（YaneuraOu互換）。
    #[must_use]
    pub fn moved_piece_before(&self, mv: Move) -> Piece {
        if mv.is_drop() {
            let Some(pt) = mv.dropped_piece() else {
                return Piece::NO_PIECE;
            };
            return Piece::make(self.side_to_move(), pt);
        }

        let from = mv.from_sq();
        if from.is_none() {
            return Piece::NO_PIECE;
        }
        self.piece_on(from)
    }

    /// 指し手で移動させる駒（移動後）を返す（YaneuraOu互換）。
    #[must_use]
    pub fn moved_piece_after(&self, mv: Move) -> Piece {
        mv.moved_after_piece()
    }

    /// 指し手で移動させる駒（移動後）を返す（YaneuraOu互換）。
    #[must_use]
    pub fn moved_piece(&self, mv: Move) -> Piece {
        self.moved_piece_after(mv)
    }

    /// 直前の指し手で捕獲された駒を取得（YaneuraOu互換）。
    #[must_use]
    pub fn captured_piece(&self) -> Piece {
        let stack = self.state_stack();
        stack.get(self.st_index).captured.to_piece()
    }

    /// 直前の指し手を取得（YaneuraOu互換）。
    #[must_use]
    pub fn last_move(&self) -> Move {
        let stack = self.state_stack();
        stack.get(self.st_index).last_move
    }

    /// 直前に動かした駒種を取得（YaneuraOu互換）。
    #[must_use]
    pub fn last_moved_piece_type(&self) -> PieceType {
        let stack = self.state_stack();
        stack.get(self.st_index).last_moved_piece_type
    }

    /// 駒割り評価値を取得（先手視点、YaneuraOu互換）。
    #[must_use]
    pub fn material_value(&self) -> i32 {
        let stack = self.state_stack();
        stack.get(self.st_index).material_value
    }

    /// ビットボードを取得
    #[inline]
    #[must_use]
    pub const fn bitboards(&self) -> &BitboardSet {
        &self.bitboards
    }

    /// 盤上にある全駒のビットボードを取得（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn pieces(&self) -> Bitboard {
        self.bitboards().occupied()
    }

    /// 指定した駒種のビットボードを取得（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn pieces_by_type(&self, piece_type: PieceType) -> Bitboard {
        self.bitboards().pieces(piece_type)
    }

    /// 指定した駒種のビットボードを取得（const-generic版）。
    #[must_use]
    pub fn pieces_const<const PT: i8>(&self) -> Bitboard {
        let piece_type = PieceType::new(PT);
        debug_assert!(piece_type.is_ok(), "invalid piece type");
        self.pieces_by_type(piece_type)
    }

    /// 指定した複数の駒種のビットボードを取得（YaneuraOu互換）。
    #[must_use]
    pub fn pieces_by_types(&self, piece_types: &[PieceType]) -> Bitboard {
        let mut out = Bitboard::EMPTY;
        for &piece_type in piece_types {
            out = out | self.bitboards().pieces(piece_type);
        }
        out
    }

    /// 指定した複数の駒種のビットボードを取得（配列版）。
    #[must_use]
    pub fn pieces_many<const N: usize>(&self, piece_types: [PieceType; N]) -> Bitboard {
        let mut out = Bitboard::EMPTY;
        for &piece_type in &piece_types {
            out = out | self.bitboards().pieces(piece_type);
        }
        out
    }

    /// 指定色の駒全体のビットボードを取得（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn pieces_by_color(&self, color: Color) -> Bitboard {
        self.bitboards().color_pieces(color)
    }

    /// 指定色の駒全体のビットボードを取得（const-generic版）。
    #[must_use]
    pub fn pieces_color_const<const C: i8>(&self) -> Bitboard {
        let color = Color::new(C);
        debug_assert!(color.is_ok(), "invalid color");
        self.pieces_by_color(color)
    }

    /// 指定色・駒種のビットボードを取得（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn pieces_of(&self, piece_type: PieceType, color: Color) -> Bitboard {
        self.bitboards().pieces_of(piece_type, color)
    }

    /// 指定色・駒種のビットボードを取得（const-generic版）。
    #[must_use]
    pub fn pieces_of_const<const C: i8, const PT: i8>(&self) -> Bitboard {
        let color = Color::new(C);
        let piece_type = PieceType::new(PT);
        debug_assert!(color.is_ok(), "invalid color");
        debug_assert!(piece_type.is_ok(), "invalid piece type");
        self.pieces_of(piece_type, color)
    }

    /// 金相当の駒（歩成りなどを含む、YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn golds(&self) -> Bitboard {
        self.bitboards().golds()
    }

    /// 馬・龍・玉（HDK、YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn hdk(&self) -> Bitboard {
        self.bitboards().hdk()
    }

    /// 角・馬（BISHOP_HORSE、YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn bishop_horse(&self) -> Bitboard {
        self.bitboards().bishop_horse()
    }

    /// 飛・龍（ROOK_DRAGON、YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub fn rook_dragon(&self) -> Bitboard {
        self.bitboards().rook_dragon()
    }

    /// 指定色・複数駒種のビットボードを取得（YaneuraOu互換）。
    #[must_use]
    pub fn pieces_of_types(&self, color: Color, piece_types: &[PieceType]) -> Bitboard {
        let mut out = Bitboard::EMPTY;
        for &piece_type in piece_types {
            out = out | self.bitboards().pieces_of(piece_type, color);
        }
        out
    }

    /// 指定色・複数駒種のビットボードを取得（配列版）。
    #[must_use]
    pub fn pieces_of_many<const N: usize>(
        &self,
        color: Color,
        piece_types: [PieceType; N],
    ) -> Bitboard {
        let mut out = Bitboard::EMPTY;
        for &piece_type in &piece_types {
            out = out | self.bitboards().pieces_of(piece_type, color);
        }
        out
    }

    /// `PieceList` への参照を取得
    #[must_use]
    pub const fn piece_list(&self) -> &PieceList {
        &self.piece_list
    }

    /// `EvalList` への参照を取得
    #[must_use]
    pub const fn eval_list(&self) -> &EvalList {
        &self.eval_list
    }
}
