//! EvalList（USE_EVAL_LIST互換）

use crate::board::bona::{BonaPiece, ExtBonaPiece, FE_HAND_END, KPP_BOARD_INDEX, KPP_HAND_INDEX};
use crate::types::{Color, Piece, PieceType, Square};

pub type PieceNumber = u8;

pub const PIECE_NUMBER_PAWN: PieceNumber = 0;
pub const PIECE_NUMBER_LANCE: PieceNumber = 18;
pub const PIECE_NUMBER_KNIGHT: PieceNumber = 22;
pub const PIECE_NUMBER_SILVER: PieceNumber = 26;
pub const PIECE_NUMBER_GOLD: PieceNumber = 30;
pub const PIECE_NUMBER_BISHOP: PieceNumber = 34;
pub const PIECE_NUMBER_ROOK: PieceNumber = 36;
pub const PIECE_NUMBER_KING: PieceNumber = 38;
pub const PIECE_NUMBER_BKING: PieceNumber = 38;
pub const PIECE_NUMBER_WKING: PieceNumber = 39;
pub const PIECE_NUMBER_ZERO: PieceNumber = 0;
pub const PIECE_NUMBER_NB: PieceNumber = 40;

const MAX_LENGTH: usize = 40;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ChangedBonaPiece {
    pub old_piece: ExtBonaPiece,
    pub new_piece: ExtBonaPiece,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DirtyEvalPiece {
    pub changed_piece: [ChangedBonaPiece; 2],
    pub piece_no: [PieceNumber; 2],
    pub dirty_num: u8,
}

#[derive(Clone, Copy, Debug)]
pub struct EvalList {
    piece_list_fb: [BonaPiece; MAX_LENGTH],
    piece_list_fw: [BonaPiece; MAX_LENGTH],
    piece_no_list_hand: [PieceNumber; FE_HAND_END as usize],
    piece_no_list_board: [PieceNumber; Square::SQ_NB_PLUS1],
}

impl EvalList {
    #[must_use]
    pub const fn new() -> Self {
        Self {
            piece_list_fb: [0; MAX_LENGTH],
            piece_list_fw: [0; MAX_LENGTH],
            piece_no_list_hand: [PIECE_NUMBER_NB; FE_HAND_END as usize],
            piece_no_list_board: [PIECE_NUMBER_NB; Square::SQ_NB_PLUS1],
        }
    }

    pub fn clear(&mut self) {
        self.piece_list_fb.fill(0);
        self.piece_list_fw.fill(0);
        self.piece_no_list_hand.fill(PIECE_NUMBER_NB);
        self.piece_no_list_board.fill(PIECE_NUMBER_NB);
    }

    #[must_use]
    pub const fn piece_list_fb(&self) -> &[BonaPiece] {
        &self.piece_list_fb
    }

    #[must_use]
    pub const fn piece_list_fw(&self) -> &[BonaPiece] {
        &self.piece_list_fw
    }

    #[must_use]
    pub fn bona_piece(&self, piece_no: PieceNumber) -> ExtBonaPiece {
        let idx = usize::from(piece_no);
        ExtBonaPiece { fb: self.piece_list_fb[idx], fw: self.piece_list_fw[idx] }
    }

    pub fn put_piece_on_board(&mut self, piece_no: PieceNumber, sq: Square, piece: Piece) {
        let ext = KPP_BOARD_INDEX[piece.to_index()];
        let offset = i32::try_from(sq.to_board_index()).expect("square index fits in i32");
        let inv_offset =
            i32::try_from(sq.inv().to_board_index()).expect("square index fits in i32");
        let fb = ext.fb + offset;
        let fw = ext.fw + inv_offset;
        self.set_piece_on_board(piece_no, fb, fw, sq);
    }

    pub fn put_piece_on_hand(
        &mut self,
        piece_no: PieceNumber,
        color: Color,
        piece_type: PieceType,
        index: usize,
    ) {
        let ext = KPP_HAND_INDEX[color.to_index()][piece_type.to_index()];
        let offset = i32::try_from(index).expect("hand index fits in i32");
        let fb = ext.fb + offset;
        let fw = ext.fw + offset;
        self.set_piece_on_hand(piece_no, fb, fw);
    }

    #[must_use]
    pub fn piece_no_of_hand(&self, bp: BonaPiece) -> PieceNumber {
        if bp < 0 {
            return PIECE_NUMBER_NB;
        }
        let idx = usize::try_from(bp).unwrap_or(usize::MAX);
        self.piece_no_list_hand.get(idx).copied().unwrap_or(PIECE_NUMBER_NB)
    }

    #[must_use]
    pub fn piece_no_of_board(&self, sq: Square) -> PieceNumber {
        self.piece_no_list_board[sq.to_board_index()]
    }

    fn set_piece_on_board(
        &mut self,
        piece_no: PieceNumber,
        fb: BonaPiece,
        fw: BonaPiece,
        sq: Square,
    ) {
        let idx = usize::from(piece_no);
        self.piece_list_fb[idx] = fb;
        self.piece_list_fw[idx] = fw;
        self.piece_no_list_board[sq.to_board_index()] = piece_no;
    }

    fn set_piece_on_hand(&mut self, piece_no: PieceNumber, fb: BonaPiece, fw: BonaPiece) {
        let idx = usize::from(piece_no);
        self.piece_list_fb[idx] = fb;
        self.piece_list_fw[idx] = fw;
        let hand_idx = usize::try_from(fb).expect("hand bona piece must be non-negative");
        self.piece_no_list_hand[hand_idx] = piece_no;
    }
}

impl Default for EvalList {
    fn default() -> Self {
        Self::new()
    }
}
