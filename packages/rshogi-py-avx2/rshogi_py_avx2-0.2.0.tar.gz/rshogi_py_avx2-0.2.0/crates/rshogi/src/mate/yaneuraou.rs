//! YaneuraOu互換の1手詰め判定（LONG_EFFECT_LIBRARY無効時のロジック）

use crate::board::attack_tables::{
    bishop_attacks, lance_attacks, rook_attacks, GOLD_ATTACKS, KING_ATTACKS, KNIGHT_ATTACKS,
    PAWN_ATTACKS, SILVER_ATTACKS,
};
#[cfg(feature = "mate1ply-full")]
use crate::board::movegen::{generate_moves, Evasions, NonEvasionsAll};
#[cfg(feature = "mate1ply-full")]
use crate::board::MoveList;
use crate::board::Position;
#[cfg(feature = "mate1ply-full")]
use crate::types::Hand;
use crate::types::{Bitboard, Color, File, HandPiece, Move, Piece, PieceType, Rank, Square};
use std::sync::OnceLock;

const PT_CHECK_PAWN_WITH_NO_PRO: usize = 0;
const PT_CHECK_PAWN_WITH_PRO: usize = 1;
const PT_CHECK_LANCE: usize = 2;
const PT_CHECK_KNIGHT: usize = 3;
const PT_CHECK_SILVER: usize = 4;
const PT_CHECK_GOLD: usize = 5;
const PT_CHECK_NON_SLIDER: usize = 10;
const PT_CHECK_NB: usize = 11;

type CheckCandTable = [[[Bitboard; Color::COLOR_NB]; PT_CHECK_NB]; Square::SQ_NB_PLUS1];

static CHECK_CAND_BB: OnceLock<Box<CheckCandTable>> = OnceLock::new();

fn check_cand_bb(color: Color, kind: usize, king_sq: Square) -> Bitboard {
    CHECK_CAND_BB.get_or_init(init_check_cand_bb)[king_sq.to_index()][kind][color.to_index()]
}

#[cfg(feature = "mate1ply-full")]
const AROUND_PAWN: usize = 0;
#[cfg(feature = "mate1ply-full")]
const AROUND_LANCE: usize = 1;
#[cfg(feature = "mate1ply-full")]
const AROUND_KNIGHT: usize = 2;
#[cfg(feature = "mate1ply-full")]
const AROUND_SILVER: usize = 3;
#[cfg(feature = "mate1ply-full")]
const AROUND_BISHOP: usize = 4;
#[cfg(feature = "mate1ply-full")]
const AROUND_ROOK: usize = 5;
#[cfg(feature = "mate1ply-full")]
const AROUND_GOLD: usize = 6;
#[cfg(feature = "mate1ply-full")]
const AROUND_KING: usize = 7;
#[cfg(feature = "mate1ply-full")]
const AROUND_NB: usize = 8;

#[cfg(feature = "mate1ply-full")]
type CheckAroundTable = [[[Bitboard; Color::COLOR_NB]; AROUND_NB]; Square::SQ_NB_PLUS1];
#[cfg(feature = "mate1ply-full")]
static CHECK_AROUND_BB: OnceLock<Box<CheckAroundTable>> = OnceLock::new();

#[cfg(feature = "mate1ply-full")]
type NextSquareTable = [[Square; Square::SQ_NB_PLUS1]; Square::SQ_NB_PLUS1];
#[cfg(feature = "mate1ply-full")]
static NEXT_SQUARE: OnceLock<Box<NextSquareTable>> = OnceLock::new();

#[cfg(feature = "mate1ply-full")]
type Around24Table = [Bitboard; Square::SQ_NB_PLUS1];
#[cfg(feature = "mate1ply-full")]
static AROUND24_BB: OnceLock<Box<Around24Table>> = OnceLock::new();

#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_RU: u8 = 1 << 0;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_R: u8 = 1 << 1;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_RD: u8 = 1 << 2;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_U: u8 = 1 << 3;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_D: u8 = 1 << 4;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_LU: u8 = 1 << 5;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_L: u8 = 1 << 6;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_LD: u8 = 1 << 7;
#[cfg(feature = "mate1ply-full")]
const DIRECTIONS_DIAG: u8 = DIRECTIONS_RU | DIRECTIONS_RD | DIRECTIONS_LU | DIRECTIONS_LD;

#[cfg(feature = "mate1ply-full")]
const fn sgn(val: i8) -> i8 {
    (val > 0) as i8 - (val < 0) as i8
}

#[cfg(feature = "mate1ply-full")]
fn check_around_index(piece_type: PieceType) -> Option<usize> {
    match piece_type {
        PieceType::PAWN => Some(AROUND_PAWN),
        PieceType::LANCE => Some(AROUND_LANCE),
        PieceType::KNIGHT => Some(AROUND_KNIGHT),
        PieceType::SILVER => Some(AROUND_SILVER),
        PieceType::BISHOP => Some(AROUND_BISHOP),
        PieceType::ROOK => Some(AROUND_ROOK),
        PieceType::GOLD => Some(AROUND_GOLD),
        PieceType::KING => Some(AROUND_KING),
        _ => None,
    }
}

#[cfg(feature = "mate1ply-full")]
fn check_around_bb(color: Color, piece_type: PieceType, king_sq: Square) -> Bitboard {
    let idx = match check_around_index(piece_type) {
        Some(idx) => idx,
        None => return Bitboard::EMPTY,
    };
    CHECK_AROUND_BB.get_or_init(init_check_around_bb)[king_sq.to_index()][idx][color.to_index()]
}

#[cfg(feature = "mate1ply-full")]
fn init_check_around_bb() -> Box<CheckAroundTable> {
    let mut table = [[[Bitboard::EMPTY; Color::COLOR_NB]; AROUND_NB]; Square::SQ_NB_PLUS1];

    for piece_type in [
        PieceType::PAWN,
        PieceType::LANCE,
        PieceType::KNIGHT,
        PieceType::SILVER,
        PieceType::BISHOP,
        PieceType::ROOK,
        PieceType::GOLD,
        PieceType::KING,
    ] {
        let idx = check_around_index(piece_type).expect("piece type should map to index");
        for (sq_idx, row) in table.iter_mut().enumerate().take(Square::SQ_NB) {
            let sq = Square::from_index(sq_idx);
            for &color in &[Color::BLACK, Color::WHITE] {
                let mut bb = Bitboard::EMPTY;
                let them = color.flip();

                match piece_type {
                    PieceType::PAWN => {
                        bb = king_effect(sq);
                        bb = pawn_bb_effect(color, bb);
                        bb = bb.and(Bitboard::ALL);
                    }
                    PieceType::LANCE => {
                        bb = lance_step_effect(them, sq);
                        if sq.file() != File::FILE_1 {
                            let next = square_offset(sq, -1, 0);
                            if !next.is_none() {
                                bb = bb
                                    | lance_step_effect(them, next)
                                    | Bitboard::from_square(next);
                            }
                        }
                        if sq.file() != File::FILE_9 {
                            let next = square_offset(sq, 1, 0);
                            if !next.is_none() {
                                bb = bb
                                    | lance_step_effect(them, next)
                                    | Bitboard::from_square(next);
                            }
                        }
                    }
                    PieceType::KNIGHT => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | knight_effect(them, to);
                        }
                    }
                    PieceType::SILVER => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | silver_effect(them, to);
                        }
                    }
                    PieceType::GOLD => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | gold_effect(them, to);
                        }
                    }
                    PieceType::BISHOP => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | bishop_step_effect(to);
                        }
                    }
                    PieceType::ROOK => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | rook_step_effect(to);
                        }
                    }
                    PieceType::KING => {
                        let mut tmp = king_effect(sq);
                        while let Some(to) = tmp.pop_lsb() {
                            bb = bb | king_effect(to);
                        }
                    }
                    _ => {}
                }

                bb = bb.and_not(Bitboard::from_square(sq));
                row[idx][color.to_index()] = bb;
            }
        }
    }

    Box::new(table)
}

#[cfg(feature = "mate1ply-full")]
fn init_next_square() -> Box<NextSquareTable> {
    let mut table = [[Square::SQ_NONE; Square::SQ_NB_PLUS1]; Square::SQ_NB_PLUS1];

    for s1_idx in 0..Square::SQ_NB {
        let s1 = Square::from_index(s1_idx);
        for s2_idx in 0..Square::SQ_NB {
            let s2 = Square::from_index(s2_idx);
            let mut next_sq = Square::SQ_NONE;
            if queen_step_effect(s1).test(s2) {
                let df = sgn(s2.file().raw() - s1.file().raw());
                let dr = sgn(s2.rank().raw() - s1.rank().raw());
                let candidate = square_offset(s2, df, dr);
                if !candidate.is_none() {
                    next_sq = candidate;
                }
            }
            table[s1_idx][s2_idx] = next_sq;
        }
    }

    Box::new(table)
}

#[cfg(feature = "mate1ply-full")]
fn next_square(sq1: Square, sq2: Square) -> Square {
    NEXT_SQUARE.get_or_init(init_next_square)[sq1.to_index()][sq2.to_index()]
}

#[cfg(feature = "mate1ply-full")]
fn init_around24_bb() -> Box<Around24Table> {
    let mut table = [Bitboard::EMPTY; Square::SQ_NB_PLUS1];
    for sq_idx in 0..Square::SQ_NB {
        let sq = Square::from_index(sq_idx);
        let mut bb = Bitboard::EMPTY;
        for df in -2..=2 {
            for dr in -2..=2 {
                if df == 0 && dr == 0 {
                    continue;
                }
                let target = square_offset(sq, df, dr);
                if !target.is_none() {
                    bb = bb | Bitboard::from_square(target);
                }
            }
        }
        table[sq_idx] = bb;
    }
    Box::new(table)
}

#[cfg(feature = "mate1ply-full")]
fn around24_bb(sq: Square) -> Bitboard {
    AROUND24_BB.get_or_init(init_around24_bb)[sq.to_index()]
}
#[allow(clippy::too_many_lines)]
fn init_check_cand_bb() -> Box<CheckCandTable> {
    let mut table = [[[Bitboard::EMPTY; Color::COLOR_NB]; PT_CHECK_NB]; Square::SQ_NB_PLUS1];

    for kind in 0..PT_CHECK_NB {
        for (sq_idx, row) in table.iter_mut().enumerate().take(Square::SQ_NB) {
            let sq = Square::from_index(sq_idx);
            for &color in &[Color::BLACK, Color::WHITE] {
                let mut bb = Bitboard::EMPTY;
                let enemy_bb = enemy_field(color);
                let them = color.flip();
                let color_idx = color.to_index();

                match kind {
                    PT_CHECK_PAWN_WITH_NO_PRO => {
                        bb = pawn_effect(them, sq).and_not(enemy_bb);
                        if !bb.is_empty() {
                            let to = bb.pop_lsb().unwrap();
                            bb = pawn_effect(them, to);
                        }
                    }
                    PT_CHECK_PAWN_WITH_PRO => {
                        bb = gold_effect(them, sq) & enemy_bb;
                        bb = pawn_bb_effect(them, bb);
                    }
                    PT_CHECK_LANCE => {
                        bb = lance_step_effect(them, sq);
                        if !(enemy_bb ^ Bitboard::from_square(sq)).is_empty() {
                            if sq.file() != File::FILE_1 {
                                let next = square_offset(sq, -1, 0);
                                if !next.is_none() {
                                    bb = bb | lance_step_effect(them, next);
                                }
                            }
                            if sq.file() != File::FILE_9 {
                                let next = square_offset(sq, 1, 0);
                                if !next.is_none() {
                                    bb = bb | lance_step_effect(them, next);
                                }
                            }
                        }
                    }
                    PT_CHECK_KNIGHT => {
                        let mut tmp = knight_effect(them, sq);
                        while let Some(step) = tmp.pop_lsb() {
                            bb = bb | knight_effect(them, step);
                        }
                        let mut tmp = gold_effect(them, sq) & enemy_bb;
                        while let Some(step) = tmp.pop_lsb() {
                            bb = bb | knight_effect(them, step);
                        }
                    }
                    PT_CHECK_SILVER => {
                        let mut tmp = silver_effect(them, sq);
                        while let Some(step) = tmp.pop_lsb() {
                            bb = bb | silver_effect(them, step);
                        }
                        let mut tmp = gold_effect(them, sq) & enemy_bb;
                        while let Some(step) = tmp.pop_lsb() {
                            bb = bb | silver_effect(them, step);
                        }
                        let rank = if color == Color::BLACK { Rank::RANK_4 } else { Rank::RANK_6 };
                        if sq.rank() == rank {
                            let target_rank =
                                if color == Color::BLACK { Rank::RANK_3 } else { Rank::RANK_7 };
                            let to = Square::from_file_rank(sq.file(), target_rank);
                            if !to.is_none() {
                                bb = bb | Bitboard::from_square(to);
                                bb = bb | cross45_step_effect(to);
                                if to.file().raw() >= File::FILE_3.raw() {
                                    let next = square_offset(to, -2, 0);
                                    if !next.is_none() {
                                        bb = bb | Bitboard::from_square(next);
                                    }
                                }
                                if to.file().raw() <= File::FILE_7.raw() {
                                    let next = square_offset(to, 2, 0);
                                    if !next.is_none() {
                                        bb = bb | Bitboard::from_square(next);
                                    }
                                }
                            }
                        }
                        if sq.rank() == Rank::RANK_5 {
                            bb = bb | knight_effect(color, sq);
                        }
                    }
                    PT_CHECK_GOLD => {
                        let mut tmp = gold_effect(them, sq);
                        while let Some(step) = tmp.pop_lsb() {
                            bb = bb | gold_effect(them, step);
                        }
                    }
                    PT_CHECK_NON_SLIDER => {
                        bb = row[PT_CHECK_GOLD][color_idx]
                            | row[PT_CHECK_KNIGHT][color_idx]
                            | row[PT_CHECK_SILVER][color_idx]
                            | row[PT_CHECK_PAWN_WITH_NO_PRO][color_idx]
                            | row[PT_CHECK_PAWN_WITH_PRO][color_idx];
                    }
                    _ => {}
                }

                bb = bb.and_not(Bitboard::from_square(sq));
                row[kind][color_idx] = bb;
            }
        }
    }

    Box::new(table)
}

fn enemy_field(color: Color) -> Bitboard {
    let ranks = if color == Color::BLACK {
        [Rank::RANK_1, Rank::RANK_2, Rank::RANK_3]
    } else {
        [Rank::RANK_7, Rank::RANK_8, Rank::RANK_9]
    };
    let mut bb = Bitboard::EMPTY;
    for rank in ranks {
        bb = bb | Bitboard::rank_mask(rank);
    }
    bb
}

fn pawn_effect(color: Color, sq: Square) -> Bitboard {
    PAWN_ATTACKS[sq.to_index()][color.to_index()]
}

fn pawn_bb_effect(color: Color, mut bb: Bitboard) -> Bitboard {
    let mut out = Bitboard::EMPTY;
    while let Some(sq) = bb.pop_lsb() {
        out = out | pawn_effect(color, sq);
    }
    out
}

fn knight_effect(color: Color, sq: Square) -> Bitboard {
    KNIGHT_ATTACKS[sq.to_index()][color.to_index()]
}

fn silver_effect(color: Color, sq: Square) -> Bitboard {
    SILVER_ATTACKS[sq.to_index()][color.to_index()]
}

fn gold_effect(color: Color, sq: Square) -> Bitboard {
    GOLD_ATTACKS[sq.to_index()][color.to_index()]
}

fn king_effect(sq: Square) -> Bitboard {
    KING_ATTACKS[sq.to_index()]
}

fn lance_step_effect(color: Color, sq: Square) -> Bitboard {
    lance_attacks(sq, Bitboard::EMPTY, color)
}

fn bishop_step_effect(sq: Square) -> Bitboard {
    bishop_attacks(sq, Bitboard::EMPTY)
}

fn rook_step_effect(sq: Square) -> Bitboard {
    rook_attacks(sq, Bitboard::EMPTY)
}

#[cfg(feature = "mate1ply-full")]
fn queen_step_effect(sq: Square) -> Bitboard {
    rook_step_effect(sq) | bishop_step_effect(sq)
}

fn cross45_step_effect(sq: Square) -> Bitboard {
    bishop_step_effect(sq) & king_effect(sq)
}

fn lance_effect(color: Color, sq: Square, occupied: Bitboard) -> Bitboard {
    lance_attacks(sq, occupied, color)
}

fn bishop_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    bishop_attacks(sq, occupied)
}

fn rook_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    rook_attacks(sq, occupied)
}

fn horse_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    bishop_attacks(sq, occupied) | king_effect(sq)
}

fn dragon_effect(sq: Square, occupied: Bitboard) -> Bitboard {
    rook_attacks(sq, occupied) | king_effect(sq)
}

#[cfg(feature = "mate1ply-full")]
fn directions_of(from: Square, to: Square) -> u8 {
    let df = to.file().raw() - from.file().raw();
    let dr = to.rank().raw() - from.rank().raw();
    if df == 0 && dr == 0 {
        return 0;
    }
    if df == 0 {
        return if dr > 0 { DIRECTIONS_D } else { DIRECTIONS_U };
    }
    if dr == 0 {
        return if df > 0 { DIRECTIONS_R } else { DIRECTIONS_L };
    }
    if df.abs() == dr.abs() {
        return match (df > 0, dr > 0) {
            (true, true) => DIRECTIONS_RD,
            (true, false) => DIRECTIONS_RU,
            (false, true) => DIRECTIONS_LD,
            (false, false) => DIRECTIONS_LU,
        };
    }
    0
}

fn square_offset(sq: Square, file_delta: i8, rank_delta: i8) -> Square {
    let file = sq.file().raw() + file_delta;
    let rank = sq.rank().raw() + rank_delta;
    Square::from_file_rank(File::new(file), Rank::new(rank))
}

fn aligned(s1: Square, s2: Square, s3: Square) -> bool {
    let line = Bitboard::line(s1, s2);
    !line.is_empty() && line.test(s3)
}

#[cfg(feature = "mate1ply-full")]
fn andnot(a: Bitboard, b: Bitboard) -> Bitboard {
    b.and_not(a)
}

fn attackers_to_color(pos: &Position, sq: Square, occ: Bitboard, color: Color) -> Bitboard {
    pos.attackers_to(sq, occ) & pos.bitboards().color_pieces(color)
}

#[cfg(feature = "mate1ply-full")]
fn hdk_of(pos: &Position, color: Color) -> Bitboard {
    pos.bitboards().hdk() & pos.bitboards().color_pieces(color)
}

#[cfg(feature = "mate1ply-full")]
fn bishop_horse_of(pos: &Position, color: Color) -> Bitboard {
    pos.bitboards().bishop_horse() & pos.bitboards().color_pieces(color)
}

#[cfg(feature = "mate1ply-full")]
fn rook_dragon_of(pos: &Position, color: Color) -> Bitboard {
    pos.bitboards().rook_dragon() & pos.bitboards().color_pieces(color)
}

#[cfg(feature = "mate1ply-full")]
fn attacks_slider(pos: &Position, color: Color, occ: Bitboard) -> Bitboard {
    let mut sum = Bitboard::EMPTY;
    let mut bb = piece_bb(pos, color, PieceType::LANCE);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | lance_effect(color, from, occ);
    }
    bb = bishop_horse_of(pos, color);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | bishop_effect(from, occ);
    }
    bb = rook_dragon_of(pos, color);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | rook_effect(from, occ);
    }
    sum
}

#[cfg(feature = "mate1ply-full")]
fn attacks_slider_avoid(
    pos: &Position,
    color: Color,
    avoid_from: Square,
    occ: Bitboard,
) -> Bitboard {
    let mut sum = Bitboard::EMPTY;
    let avoid_bb = Bitboard::from_square(avoid_from).not();
    let mut bb = piece_bb(pos, color, PieceType::LANCE) & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | lance_effect(color, from, occ);
    }
    bb = bishop_horse_of(pos, color) & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | bishop_effect(from, occ);
    }
    bb = rook_dragon_of(pos, color) & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | rook_effect(from, occ);
    }
    sum
}

#[cfg(feature = "mate1ply-full")]
fn attacks_around_king_non_slider(pos: &Position, our_king: Color) -> Bitboard {
    let sq_king = pos.king_square(our_king);
    let them = our_king.flip();
    let mut sum = pawn_bb_effect(them, piece_bb(pos, them, PieceType::PAWN));

    let mut bb =
        piece_bb(pos, them, PieceType::KNIGHT) & check_around_bb(them, PieceType::KNIGHT, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | knight_effect(them, from);
    }
    bb = piece_bb(pos, them, PieceType::SILVER) & check_around_bb(them, PieceType::SILVER, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | silver_effect(them, from);
    }
    bb = golds_of(pos, them) & check_around_bb(them, PieceType::GOLD, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | gold_effect(them, from);
    }
    bb = hdk_of(pos, them) & check_around_bb(them, PieceType::KING, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | king_effect(from);
    }
    sum
}

#[cfg(feature = "mate1ply-full")]
fn attacks_around_king_slider(pos: &Position, our_king: Color) -> Bitboard {
    let sq_king = pos.king_square(our_king);
    let them = our_king.flip();
    let mut sum = Bitboard::EMPTY;

    let mut bb =
        piece_bb(pos, them, PieceType::LANCE) & check_around_bb(them, PieceType::LANCE, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | lance_effect(them, from, pos.bitboards().occupied());
    }
    bb = bishop_horse_of(pos, them) & check_around_bb(them, PieceType::BISHOP, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | bishop_effect(from, pos.bitboards().occupied());
    }
    bb = rook_dragon_of(pos, them) & check_around_bb(them, PieceType::ROOK, sq_king);
    while let Some(from) = bb.pop_lsb() {
        sum = sum | rook_effect(from, pos.bitboards().occupied());
    }
    sum
}

#[cfg(feature = "mate1ply-full")]
fn attacks_around_king_non_slider_avoiding(
    pos: &Position,
    our_king: Color,
    avoid_from: Square,
) -> Bitboard {
    let sq_king = pos.king_square(our_king);
    let them = our_king.flip();
    let avoid_bb = Bitboard::from_square(avoid_from).not();
    let mut sum = pawn_bb_effect(them, piece_bb(pos, them, PieceType::PAWN));

    let mut bb = piece_bb(pos, them, PieceType::KNIGHT)
        & check_around_bb(them, PieceType::KNIGHT, sq_king)
        & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | knight_effect(them, from);
    }
    bb = piece_bb(pos, them, PieceType::SILVER)
        & check_around_bb(them, PieceType::SILVER, sq_king)
        & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | silver_effect(them, from);
    }
    bb = golds_of(pos, them) & check_around_bb(them, PieceType::GOLD, sq_king) & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | gold_effect(them, from);
    }
    bb = hdk_of(pos, them) & check_around_bb(them, PieceType::KING, sq_king) & avoid_bb;
    while let Some(from) = bb.pop_lsb() {
        sum = sum | king_effect(from);
    }
    sum
}

#[cfg(feature = "mate1ply-full")]
fn attacks_around_king_in_avoiding(
    pos: &Position,
    our_king: Color,
    from: Square,
    occ: Bitboard,
) -> Bitboard {
    attacks_around_king_non_slider_avoiding(pos, our_king, from)
        | attacks_slider_avoid(pos, our_king.flip(), from, occ)
}

#[cfg(feature = "mate1ply-full")]
fn can_pawn_drop(pos: &Position, us: Color, sq: Square) -> bool {
    pos.hand_of(us).count(HandPiece::HAND_PAWN) > 0
        && (piece_bb(pos, us, PieceType::PAWN) & Bitboard::file_mask(sq.file())).is_empty()
}

#[cfg(feature = "mate1ply-full")]
fn hand_only_pawns(hand: Hand) -> bool {
    hand.0 == hand.count(HandPiece::HAND_PAWN)
}

fn can_king_escape(
    pos: &Position,
    us: Color,
    to: Square,
    bb_avoid: Bitboard,
    slide: Bitboard,
) -> bool {
    let sq_king = pos.king_square(us);
    let us_pieces = pos.bitboards().color_pieces(us);
    let to_bb = Bitboard::from_square(to);
    let candidates = king_effect(sq_king).and_not(bb_avoid | to_bb | us_pieces);
    let mut bb = candidates;
    let them = us.flip();
    let slide = slide | to_bb;

    while let Some(escape) = bb.pop_lsb() {
        if attackers_to_color(pos, escape, slide, them).is_empty() {
            return true;
        }
    }
    false
}

fn can_king_escape_with_from(
    pos: &Position,
    us: Color,
    from: Square,
    to: Square,
    bb_avoid: Bitboard,
    slide: Bitboard,
) -> bool {
    let sq_king = pos.king_square(us);
    let us_pieces = pos.bitboards().color_pieces(us);
    let to_bb = Bitboard::from_square(to);
    let from_bb = Bitboard::from_square(from);
    let candidates = king_effect(sq_king).and_not(bb_avoid | to_bb | us_pieces);
    let mut bb = candidates;
    let them = us.flip();
    let slide = (slide | to_bb) ^ Bitboard::from_square(sq_king);

    while let Some(escape) = bb.pop_lsb() {
        let attackers = attackers_to_color(pos, escape, slide, them);
        if attackers.and_not(from_bb).is_empty() {
            return true;
        }
    }
    false
}

#[cfg(feature = "mate1ply-full")]
fn can_king_escape_cangoto(
    pos: &Position,
    us: Color,
    from: Square,
    to: Square,
    bb_avoid: Bitboard,
    slide: Bitboard,
) -> bool {
    let sq_king = pos.king_square(us);
    let them = us.flip();
    let slide = (slide | Bitboard::from_square(to)) ^ Bitboard::from_square(sq_king);

    let bb = king_effect(sq_king)
        .and_not(Bitboard::from_square(to))
        .and_not(bb_avoid | pos.bitboards().color_pieces(us));
    let mut candidates = bb;

    while let Some(escape) = candidates.pop_lsb() {
        let attackers = attackers_to_color(pos, escape, slide, them);
        if Bitboard::from_square(from).and_not(attackers).is_empty() {
            return true;
        }
    }
    false
}

fn can_piece_capture(
    pos: &Position,
    us: Color,
    to: Square,
    pinned: Bitboard,
    slide: Bitboard,
) -> bool {
    let sq_king = pos.king_square(us);
    let attackers = attackers_to_color(pos, to, slide, us);
    let kings = pos.bitboards().pieces(PieceType::KING);
    let mut sum = attackers.and_not(kings);

    while let Some(from) = sum.pop_lsb() {
        if pinned.is_empty() || !pinned.test(from) || aligned(from, to, sq_king) {
            return true;
        }
    }
    false
}

#[cfg(feature = "mate1ply-full")]
fn can_piece_capture_with_avoid(
    pos: &Position,
    us: Color,
    to: Square,
    avoid: Square,
    pinned: Bitboard,
    slide: Bitboard,
) -> bool {
    let sq_king = pos.king_square(us);
    let avoid_bb = Bitboard::from_square(avoid);
    let attackers = attackers_to_color(pos, to, slide, us);
    let kings = pos.bitboards().pieces(PieceType::KING);
    let mut sum = attackers.and_not(kings | avoid_bb);

    while let Some(from) = sum.pop_lsb() {
        if pinned.is_empty() || !pinned.test(from) || aligned(from, to, sq_king) {
            return true;
        }
    }
    false
}

fn can_promote_to(color: Color, sq: Square) -> bool {
    match color {
        Color::BLACK => sq.rank() <= Rank::RANK_3,
        Color::WHITE => sq.rank() >= Rank::RANK_7,
        _ => false,
    }
}

fn can_promote(color: Color, from: Square, to: Square) -> bool {
    match color {
        Color::BLACK => from.rank() <= Rank::RANK_3 || to.rank() <= Rank::RANK_3,
        Color::WHITE => from.rank() >= Rank::RANK_7 || to.rank() >= Rank::RANK_7,
        _ => false,
    }
}

#[cfg(feature = "mate1ply-full")]
fn is_promoted(piece_type: PieceType) -> bool {
    piece_type.raw() >= PieceType::PRO_PAWN.raw()
}

fn golds_of(pos: &Position, color: Color) -> Bitboard {
    pos.bitboards().golds() & pos.bitboards().color_pieces(color)
}

fn piece_bb(pos: &Position, color: Color, piece_type: PieceType) -> Bitboard {
    pos.bitboards().pieces_of(piece_type, color)
}

#[allow(clippy::too_many_lines, clippy::cognitive_complexity)]
pub fn mate_1ply(pos: &Position) -> Option<Move> {
    let us = pos.side_to_move();
    let them = us.flip();

    if !pos.checkers().is_empty() {
        return None;
    }

    let king_sq = pos.king_square(them);
    if king_sq.is_none() {
        return None;
    }

    let dc_candidates = pos.blockers_for_king(them) & pos.bitboards().color_pieces(us);
    let pinned = pos.blockers_for_king(them) & pos.bitboards().color_pieces(them);

    let mut bb;
    let mut bb_attacks: Bitboard;
    let mut bb_check;
    let mut from;
    let mut to;

    let our_hand = pos.hand_of(us);
    #[cfg(feature = "mate1ply-full")]
    let them_hand = pos.hand_of(them);
    let occupied = pos.bitboards().occupied();
    let bb_drop = occupied.not();

    if our_hand.count(HandPiece::HAND_ROOK) > 0 {
        bb = rook_step_effect(king_sq) & king_effect(king_sq) & bb_drop;
        while let Some(drop_sq) = bb.pop_lsb() {
            if attackers_to_color(pos, drop_sq, occupied, us).is_empty() {
                continue;
            }
            bb_attacks = rook_step_effect(drop_sq);
            if can_king_escape(pos, them, drop_sq, bb_attacks, occupied) {
                continue;
            }
            if can_piece_capture(pos, them, drop_sq, pinned, occupied) {
                continue;
            }
            return Some(Move::make_drop(PieceType::ROOK, drop_sq, us));
        }
    }

    if our_hand.count(HandPiece::HAND_LANCE) > 0 {
        bb = pawn_effect(them, king_sq) & bb_drop;
        if let Some(drop_sq) = bb.pop_lsb() {
            if !attackers_to_color(pos, drop_sq, occupied, us).is_empty() {
                bb_attacks = lance_step_effect(us, drop_sq);
                if !can_king_escape(pos, them, drop_sq, bb_attacks, occupied)
                    && !can_piece_capture(pos, them, drop_sq, pinned, occupied)
                {
                    return Some(Move::make_drop(PieceType::LANCE, drop_sq, us));
                }
            }
        }
    }

    if our_hand.count(HandPiece::HAND_BISHOP) > 0 {
        bb = cross45_step_effect(king_sq) & bb_drop;
        while let Some(drop_sq) = bb.pop_lsb() {
            if attackers_to_color(pos, drop_sq, occupied, us).is_empty() {
                continue;
            }
            bb_attacks = bishop_step_effect(drop_sq);
            if can_king_escape(pos, them, drop_sq, bb_attacks, occupied) {
                continue;
            }
            if can_piece_capture(pos, them, drop_sq, pinned, occupied) {
                continue;
            }
            return Some(Move::make_drop(PieceType::BISHOP, drop_sq, us));
        }
    }

    if our_hand.count(HandPiece::HAND_GOLD) > 0 {
        bb = gold_effect(them, king_sq) & bb_drop;
        if our_hand.count(HandPiece::HAND_ROOK) > 0 {
            bb = bb.and_not(pawn_effect(us, king_sq));
        }
        while let Some(drop_sq) = bb.pop_lsb() {
            if attackers_to_color(pos, drop_sq, occupied, us).is_empty() {
                continue;
            }
            bb_attacks = gold_effect(us, drop_sq);
            if can_king_escape(pos, them, drop_sq, bb_attacks, occupied) {
                continue;
            }
            if can_piece_capture(pos, them, drop_sq, pinned, occupied) {
                continue;
            }
            return Some(Move::make_drop(PieceType::GOLD, drop_sq, us));
        }
    }

    if our_hand.count(HandPiece::HAND_SILVER) > 0 {
        if our_hand.count(HandPiece::HAND_GOLD) > 0 {
            if our_hand.count(HandPiece::HAND_BISHOP) > 0 {
                bb = Bitboard::EMPTY;
            } else {
                bb = silver_effect(them, king_sq) & bb_drop.and_not(gold_effect(them, king_sq));
            }
        } else {
            bb = silver_effect(them, king_sq) & bb_drop;
        }
        while let Some(drop_sq) = bb.pop_lsb() {
            if attackers_to_color(pos, drop_sq, occupied, us).is_empty() {
                continue;
            }
            bb_attacks = silver_effect(us, drop_sq);
            if can_king_escape(pos, them, drop_sq, bb_attacks, occupied) {
                continue;
            }
            if can_piece_capture(pos, them, drop_sq, pinned, occupied) {
                continue;
            }
            return Some(Move::make_drop(PieceType::SILVER, drop_sq, us));
        }
    }

    if our_hand.count(HandPiece::HAND_KNIGHT) > 0 {
        bb = knight_effect(them, king_sq) & bb_drop;
        while let Some(drop_sq) = bb.pop_lsb() {
            if can_king_escape(pos, them, drop_sq, Bitboard::EMPTY, occupied) {
                continue;
            }
            if can_piece_capture(pos, them, drop_sq, pinned, occupied) {
                continue;
            }
            return Some(Move::make_drop(PieceType::KNIGHT, drop_sq, us));
        }
    }

    let bb_move = pos.bitboards().color_pieces(us).not();
    let our_pinned = pos.blockers_for_king(us) & pos.bitboards().color_pieces(us);
    let our_king = pos.king_square(us);

    bb = piece_bb(pos, us, PieceType::DRAGON);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        let from_bb = Bitboard::from_square(from);
        let slide = occupied ^ from_bb;
        #[cfg(feature = "mate1ply-full")]
        {
            let check_bb = rook_effect(king_sq, occupied ^ from_bb) | king_effect(king_sq);
            bb_check = dragon_effect(from, slide) & bb_move & check_bb;
        }
        #[cfg(not(feature = "mate1ply-full"))]
        {
            bb_check = dragon_effect(from, slide) & bb_move & king_effect(king_sq);
        }
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            #[cfg(feature = "mate1ply-full")]
            let need_attackers = king_effect(king_sq).test(to);
            #[cfg(not(feature = "mate1ply-full"))]
            let need_attackers = true;
            if need_attackers {
                let attackers = attackers_to_color(pos, to, slide, us);
                if (attackers ^ Bitboard::from_square(from)).is_empty() {
                    continue;
                }
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            if cross45_step_effect(king_sq).test(to) {
                bb_attacks = dragon_effect(to, slide);
            } else {
                bb_attacks = rook_step_effect(to) | king_effect(to);
            }
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            return Some(Move::make(from, to, pos.piece_on(from)));
        }
    }

    bb = piece_bb(pos, us, PieceType::ROOK);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        let from_bb = Bitboard::from_square(from);
        let slide = occupied ^ from_bb;
        #[cfg(feature = "mate1ply-full")]
        {
            let check_bb = rook_effect(king_sq, occupied ^ from_bb) | king_effect(king_sq);
            bb_check = rook_effect(from, slide) & bb_move & check_bb;
        }
        #[cfg(not(feature = "mate1ply-full"))]
        {
            bb_check = rook_effect(from, slide) & bb_move & king_effect(king_sq);
        }
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            #[cfg(feature = "mate1ply-full")]
            let need_attackers = king_effect(king_sq).test(to);
            #[cfg(not(feature = "mate1ply-full"))]
            let need_attackers = true;
            if need_attackers {
                let attackers = attackers_to_color(pos, to, slide, us);
                if (attackers ^ Bitboard::from_square(from)).is_empty() {
                    continue;
                }
            }
            if can_promote(us, from, to) {
                if cross45_step_effect(king_sq).test(to) {
                    bb_attacks = dragon_effect(to, slide);
                } else {
                    bb_attacks = rook_step_effect(to) | king_effect(to);
                }
            } else {
                bb_attacks = rook_step_effect(to);
            }
            if !bb_attacks.test(king_sq) {
                continue;
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            if !can_promote(us, from, to) {
                return Some(Move::make(from, to, pos.piece_on(from)));
            }
            return Some(Move::make_promote(from, to, pos.piece_on(from)));
        }
    }

    bb = piece_bb(pos, us, PieceType::HORSE);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        let from_bb = Bitboard::from_square(from);
        let slide = occupied ^ from_bb;
        #[cfg(feature = "mate1ply-full")]
        {
            let check_bb = bishop_effect(king_sq, occupied ^ from_bb) | king_effect(king_sq);
            bb_check = horse_effect(from, slide) & bb_move & check_bb;
        }
        #[cfg(not(feature = "mate1ply-full"))]
        {
            bb_check = horse_effect(from, slide) & bb_move & king_effect(king_sq);
        }
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            #[cfg(feature = "mate1ply-full")]
            let need_attackers = king_effect(king_sq).test(to);
            #[cfg(not(feature = "mate1ply-full"))]
            let need_attackers = true;
            if need_attackers {
                let attackers = attackers_to_color(pos, to, slide, us);
                if (attackers ^ Bitboard::from_square(from)).is_empty() {
                    continue;
                }
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            bb_attacks = bishop_step_effect(to) | king_effect(to);
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if (dc_candidates.test(from) && !aligned(from, to, king_sq))
                || !can_piece_capture(pos, them, to, new_pin, slide)
            {
                return Some(Move::make(from, to, pos.piece_on(from)));
            }
        }
    }

    bb = piece_bb(pos, us, PieceType::BISHOP);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        let from_bb = Bitboard::from_square(from);
        let slide = occupied ^ from_bb;
        #[cfg(feature = "mate1ply-full")]
        {
            let check_bb = bishop_effect(king_sq, occupied ^ from_bb) | king_effect(king_sq);
            bb_check = bishop_effect(from, slide) & bb_move & check_bb;
        }
        #[cfg(not(feature = "mate1ply-full"))]
        {
            bb_check = bishop_effect(from, slide) & bb_move & king_effect(king_sq);
        }
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            #[cfg(feature = "mate1ply-full")]
            let need_attackers = king_effect(king_sq).test(to);
            #[cfg(not(feature = "mate1ply-full"))]
            let need_attackers = true;
            if need_attackers {
                let attackers = attackers_to_color(pos, to, slide, us);
                if (attackers ^ Bitboard::from_square(from)).is_empty() {
                    continue;
                }
            }
            if can_promote(us, from, to) {
                bb_attacks = bishop_step_effect(to) | king_effect(to);
            } else {
                bb_attacks = bishop_step_effect(to);
            }
            if !bb_attacks.test(king_sq) {
                continue;
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            if !can_promote(us, from, to) {
                return Some(Move::make(from, to, pos.piece_on(from)));
            }
            return Some(Move::make_promote(from, to, pos.piece_on(from)));
        }
    }

    #[cfg(feature = "mate1ply-full")]
    {
        bb = piece_bb(pos, us, PieceType::LANCE);
    }
    #[cfg(not(feature = "mate1ply-full"))]
    {
        bb = check_cand_bb(us, PT_CHECK_LANCE, king_sq) & piece_bb(pos, us, PieceType::LANCE);
    }
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        let from_bb = Bitboard::from_square(from);
        let slide = occupied ^ from_bb;
        let new_pin = pinned;
        bb_attacks = lance_effect(us, from, slide);
        #[cfg(feature = "mate1ply-full")]
        {
            let check_bb = rook_effect(king_sq, occupied ^ from_bb);
            let gold_check_bb = gold_effect(them, king_sq);
            bb_check = bb_attacks & bb_move & (check_bb | gold_check_bb);
        }
        #[cfg(not(feature = "mate1ply-full"))]
        {
            bb_check = bb_attacks & bb_move & gold_effect(them, king_sq);
        }

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            #[cfg(feature = "mate1ply-full")]
            {
                let can_promote = can_promote_to(us, to);
                let rank_edge = if us == Color::BLACK { Rank::RANK_3 } else { Rank::RANK_7 };
                let can_non_promo = !can_promote || to.rank() == rank_edge;
                let bb_lance = lance_step_effect(us, to);
                let is_lance_check = bb_lance.test(king_sq);
                let bb_gold = gold_effect(us, to);
                let is_gold_check = can_promote && bb_gold.test(king_sq);

                if is_gold_check {
                    if pos.discovered(from, to, our_king, our_pinned) {
                        continue;
                    }
                    if can_king_escape_with_from(pos, them, from, to, bb_gold, slide) {
                        continue;
                    }
                    if can_piece_capture(pos, them, to, new_pin, slide) {
                        continue;
                    }
                    return Some(Move::make_promote(from, to, pos.piece_on(from)));
                }

                if is_lance_check && can_non_promo {
                    if pos.discovered(from, to, our_king, our_pinned) {
                        continue;
                    }
                    if can_king_escape_with_from(pos, them, from, to, bb_lance, slide) {
                        continue;
                    }
                    if can_piece_capture(pos, them, to, new_pin, slide) {
                        continue;
                    }
                    return Some(Move::make(from, to, pos.piece_on(from)));
                }
            }
            if can_promote_to(us, to) {
                bb_attacks = gold_effect(us, to);
                if bb_attacks.test(king_sq) {
                    let attackers = attackers_to_color(pos, to, slide, us);
                    if !(attackers ^ Bitboard::from_square(from)).is_empty()
                        && !pos.discovered(from, to, our_king, our_pinned)
                        && !can_king_escape_with_from(pos, them, from, to, bb_attacks, slide)
                        && (dc_candidates.test(from)
                            || !can_piece_capture(pos, them, to, new_pin, slide))
                    {
                        return Some(Move::make_promote(from, to, pos.piece_on(from)));
                    }
                }
            }

            let rank_edge = if us == Color::BLACK { Rank::RANK_3 } else { Rank::RANK_7 };
            if to.rank() == rank_edge {
                bb_attacks = lance_step_effect(us, to);
                if !bb_attacks.test(king_sq) {
                    continue;
                }
                let attackers = attackers_to_color(pos, to, slide, us);
                if (attackers ^ Bitboard::from_square(from)).is_empty() {
                    continue;
                }
                if pos.discovered(from, to, our_king, our_pinned) {
                    continue;
                }
                if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                    continue;
                }
                if can_piece_capture(pos, them, to, new_pin, slide) {
                    continue;
                }
                return Some(Move::make(from, to, pos.piece_on(from)));
            }
        }
    }

    #[cfg(feature = "mate1ply-full")]
    if hand_only_pawns(them_hand) {
        let bb_king_movable = andnot(pos.bitboards().color_pieces(them), king_effect(king_sq));
        let aakns = attacks_around_king_non_slider(pos, them);
        let aaks = attacks_around_king_slider(pos, them);
        let aak = aakns | aaks;

        let mut escape_bb = bb_king_movable.and_not(aak);
        let esc_count = escape_bb.count();
        if esc_count < 4 {
            let mut bb2 = king_effect(king_sq).and_not(occupied);

            if esc_count == 2 {
                let mut tmp = escape_bb;
                let _ = tmp.pop_lsb();
                let _ = tmp.pop_lsb();
            }

            while let Some(one) = bb2.pop_lsb() {
                to = next_square(king_sq, one);
                if to.is_none() {
                    continue;
                }
                let to_piece = pos.piece_on(to);
                if to_piece != Piece::NO_PIECE && to_piece.color() == us {
                    continue;
                }
                if can_pawn_drop(pos, them, one) {
                    continue;
                }
                if pos.piece_on(to).piece_type() == PieceType::PAWN
                    && to.file() == one.file()
                    && them_hand.count(HandPiece::HAND_PAWN) >= 1
                {
                    continue;
                }

                let dr = directions_of(king_sq, one);
                let mut pt;
                let mut can_lance_attack = false;
                if (dr & DIRECTIONS_DIAG) != 0 {
                    pt = PieceType::BISHOP;
                    if our_hand.count(HandPiece::HAND_BISHOP) == 0 {
                        continue;
                    }
                } else {
                    pt = PieceType::ROOK;
                    can_lance_attack =
                        if us == Color::BLACK { dr == DIRECTIONS_D } else { dr == DIRECTIONS_U };
                    if can_lance_attack && our_hand.count(HandPiece::HAND_LANCE) >= 1 {
                        pt = PieceType::LANCE;
                    } else if our_hand.count(HandPiece::HAND_ROOK) == 0 {
                        continue;
                    }
                }

                if pos.piece_on(to) != Piece::NO_PIECE {
                    continue;
                }
                if can_piece_capture(pos, them, one, pinned, occupied) {
                    continue;
                }
                if can_piece_capture(pos, them, to, pinned, occupied) {
                    continue;
                }

                escape_bb = bb_king_movable
                    .and_not(aakns | attacks_slider(pos, us, occupied | Bitboard::from_square(to)));

                if (dr & DIRECTIONS_DIAG) != 0 {
                    if escape_bb.and_not(bishop_step_effect(to)).is_empty() {
                        return Some(Move::make_drop(pt, to, us));
                    }
                } else if escape_bb.and_not(rook_step_effect(to)).is_empty() {
                    return Some(Move::make_drop(pt, to, us));
                }

                if esc_count <= 2 {
                    let next_to = next_square(one, to);
                    if next_to.is_none() {
                        continue;
                    }
                    if pos.piece_on(next_to) != Piece::NO_PIECE {
                        continue;
                    }
                    if can_pawn_drop(pos, them, to) {
                        continue;
                    }
                    if can_piece_capture(pos, them, next_to, pinned, occupied) {
                        continue;
                    }

                    escape_bb = bb_king_movable.and_not(
                        aakns | attacks_slider(pos, us, occupied | Bitboard::from_square(next_to)),
                    );

                    if (dr & DIRECTIONS_DIAG) != 0 {
                        if escape_bb.and_not(bishop_step_effect(next_to)).is_empty() {
                            return Some(Move::make_drop(pt, next_to, us));
                        }
                    } else if escape_bb.and_not(rook_step_effect(next_to)).is_empty() {
                        return Some(Move::make_drop(pt, next_to, us));
                    }
                }

                if (dr & DIRECTIONS_DIAG) == 0 {
                    let is_rook = rook_step_effect(to).and(rook_dragon_of(pos, us)).any();
                    let is_dragon = king_effect(to).and(piece_bb(pos, us, PieceType::DRAGON)).any();
                    let is_lance = if can_lance_attack {
                        lance_step_effect(them, to).and(piece_bb(pos, us, PieceType::LANCE)).any()
                    } else {
                        false
                    };

                    if is_rook || is_dragon || is_lance {
                        let mut candidates = Bitboard::EMPTY;
                        if is_rook {
                            candidates = rook_effect(to, occupied).and(rook_dragon_of(pos, us));
                        }
                        if is_dragon {
                            candidates = candidates
                                | (king_effect(to) & piece_bb(pos, us, PieceType::DRAGON));
                        }
                        if is_lance {
                            candidates = candidates
                                | (lance_effect(them, to, occupied)
                                    & piece_bb(pos, us, PieceType::LANCE));
                        }

                        while let Some(from_sq) = candidates.pop_lsb() {
                            from = from_sq;
                            if pos.discovered(from, to, our_king, our_pinned) {
                                continue;
                            }
                            let slide = occupied ^ Bitboard::from_square(from);
                            if can_piece_capture(pos, them, to, pinned, slide) {
                                continue;
                            }
                            if can_piece_capture_with_avoid(pos, them, one, to, pinned, slide) {
                                continue;
                            }

                            let from_piece = pos.piece_on(from);
                            if from_piece.piece_type() == PieceType::LANCE {
                                bb_attacks = rook_step_effect(to);
                            } else if can_promote(us, from, to)
                                || from_piece.piece_type() == PieceType::DRAGON
                            {
                                bb_attacks = queen_step_effect(to);
                            } else {
                                bb_attacks = rook_step_effect(to);
                            }

                            let new_slide = (occupied ^ Bitboard::from_square(from))
                                | Bitboard::from_square(to);
                            let blocked = pos.bitboards().color_pieces(them)
                                | attacks_around_king_in_avoiding(pos, them, from, new_slide)
                                | bb_attacks;
                            if king_effect(king_sq).and_not(blocked).is_empty() {
                                let pt = from_piece.piece_type();
                                if pt != PieceType::LANCE
                                    && can_promote(us, from, to)
                                    && !is_promoted(pt)
                                {
                                    return Some(Move::make_promote(from, to, from_piece));
                                }
                                return Some(Move::make(from, to, from_piece));
                            }
                        }
                    }
                } else {
                    let is_bishop = bishop_step_effect(to).and(bishop_horse_of(pos, us)).any();
                    let is_horse = king_effect(to).and(piece_bb(pos, us, PieceType::HORSE)).any();
                    if is_bishop || is_horse {
                        let mut candidates = Bitboard::EMPTY;
                        if is_bishop {
                            candidates = bishop_effect(to, occupied).and(bishop_horse_of(pos, us));
                        }
                        if is_horse {
                            candidates = candidates
                                | (king_effect(to) & piece_bb(pos, us, PieceType::HORSE));
                        }

                        while let Some(from_sq) = candidates.pop_lsb() {
                            from = from_sq;
                            if pos.discovered(from, to, our_king, our_pinned) {
                                continue;
                            }
                            let slide = occupied ^ Bitboard::from_square(from);
                            if can_piece_capture_with_avoid(pos, them, one, to, pinned, slide) {
                                continue;
                            }
                            if can_piece_capture(pos, them, to, pinned, slide) {
                                continue;
                            }

                            let new_slide = (occupied ^ Bitboard::from_square(from))
                                | Bitboard::from_square(to);
                            let blocked = pos.bitboards().color_pieces(them)
                                | attacks_around_king_in_avoiding(pos, them, from, new_slide)
                                | queen_step_effect(to);
                            if king_effect(king_sq).and_not(blocked).is_empty() {
                                let pc = pos.piece_on(from);
                                if can_promote(us, from, to) && !is_promoted(pc.piece_type()) {
                                    return Some(Move::make_promote(from, to, pc));
                                }
                                return Some(Move::make(from, to, pc));
                            }
                        }
                    }
                }
            }
        }
    }

    bb = check_cand_bb(us, PT_CHECK_NON_SLIDER, king_sq)
        & (golds_of(pos, us)
            | piece_bb(pos, us, PieceType::SILVER)
            | piece_bb(pos, us, PieceType::KNIGHT)
            | piece_bb(pos, us, PieceType::PAWN));
    if bb.is_empty() {
        return None;
    }

    bb = check_cand_bb(us, PT_CHECK_GOLD, king_sq) & golds_of(pos, us);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        bb_check = gold_effect(us, from) & bb_move & gold_effect(them, king_sq);
        if bb_check.is_empty() {
            continue;
        }
        let slide = occupied ^ Bitboard::from_square(from);
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            let attackers = attackers_to_color(pos, to, slide, us);
            if (attackers ^ Bitboard::from_square(from)).is_empty() {
                continue;
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            bb_attacks = gold_effect(us, to);
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            return Some(Move::make(from, to, pos.piece_on(from)));
        }
    }

    bb = check_cand_bb(us, PT_CHECK_SILVER, king_sq) & piece_bb(pos, us, PieceType::SILVER);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        bb_check = silver_effect(us, from) & bb_move & king_effect(king_sq);
        if bb_check.is_empty() {
            continue;
        }
        let slide = occupied ^ Bitboard::from_square(from);
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            let can_promote = can_promote(us, from, to);
            bb_attacks = silver_effect(us, to);
            let attackers = attackers_to_color(pos, to, slide, us);
            let non_promote_ok = bb_attacks.test(king_sq)
                && !(attackers ^ Bitboard::from_square(from)).is_empty()
                && !pos.discovered(from, to, our_king, our_pinned)
                && !can_king_escape_with_from(pos, them, from, to, bb_attacks, slide)
                && ((dc_candidates.test(from) && !aligned(from, to, king_sq))
                    || !can_piece_capture(pos, them, to, new_pin, slide));
            if non_promote_ok {
                return Some(Move::make(from, to, pos.piece_on(from)));
            }

            if !can_promote {
                continue;
            }
            bb_attacks = gold_effect(us, to);
            if !bb_attacks.test(king_sq) {
                continue;
            }
            let attackers = attackers_to_color(pos, to, slide, us);
            if (attackers ^ Bitboard::from_square(from)).is_empty() {
                continue;
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            return Some(Move::make_promote(from, to, pos.piece_on(from)));
        }
    }

    bb = check_cand_bb(us, PT_CHECK_KNIGHT, king_sq) & piece_bb(pos, us, PieceType::KNIGHT);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        bb_check = knight_effect(us, from) & bb_move;
        if bb_check.is_empty() {
            continue;
        }
        let slide = occupied ^ Bitboard::from_square(from);
        let new_pin = pos.pinned_pieces_avoid(them, from);

        while let Some(to_sq) = bb_check.pop_lsb() {
            to = to_sq;
            bb_attacks = knight_effect(us, to);
            if bb_attacks.test(king_sq) {
                if pos.discovered(from, to, our_king, our_pinned) {
                    continue;
                }
                if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                    continue;
                }
                if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                    continue;
                }
                return Some(Move::make(from, to, pos.piece_on(from)));
            }

            if !can_promote(us, from, to) {
                continue;
            }
            bb_attacks = gold_effect(us, to);
            if !bb_attacks.test(king_sq) {
                continue;
            }
            let attackers = attackers_to_color(pos, to, slide, us);
            if (attackers ^ Bitboard::from_square(from)).is_empty() {
                continue;
            }
            if pos.discovered(from, to, our_king, our_pinned) {
                continue;
            }
            if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
                continue;
            }
            if !dc_candidates.test(from) && can_piece_capture(pos, them, to, new_pin, slide) {
                continue;
            }
            return Some(Move::make_promote(from, to, pos.piece_on(from)));
        }
    }

    let pawn_candidates =
        check_cand_bb(us, PT_CHECK_PAWN_WITH_NO_PRO, king_sq) & piece_bb(pos, us, PieceType::PAWN);
    if !pawn_candidates.is_empty() {
        to = square_offset(king_sq, 0, if us == Color::BLACK { 1 } else { -1 });
        if !to.is_none() {
            let to_piece = pos.piece_on(to);
            if to_piece == Piece::NO_PIECE || to_piece.color() == them {
                from = square_offset(to, 0, if us == Color::BLACK { 1 } else { -1 });
                if !from.is_none() && !can_promote_to(us, to) {
                    let slide = occupied ^ Bitboard::from_square(from);
                    let attackers = attackers_to_color(pos, to, slide, us);
                    if !(attackers ^ Bitboard::from_square(from)).is_empty()
                        && !pos.discovered(from, to, our_king, our_pinned)
                        && !can_king_escape_with_from(pos, them, from, to, Bitboard::EMPTY, slide)
                        && !can_piece_capture(pos, them, to, pinned, slide)
                    {
                        return Some(Move::make(from, to, pos.piece_on(from)));
                    }
                }
            }
        }
    }

    bb = check_cand_bb(us, PT_CHECK_PAWN_WITH_PRO, king_sq) & piece_bb(pos, us, PieceType::PAWN);
    while let Some(from_sq) = bb.pop_lsb() {
        from = from_sq;
        to = square_offset(from, 0, if us == Color::BLACK { -1 } else { 1 });
        if to.is_none() {
            continue;
        }
        let to_piece = pos.piece_on(to);
        if to_piece != Piece::NO_PIECE && to_piece.color() != them {
            continue;
        }
        bb_attacks = gold_effect(us, to);
        if !bb_attacks.test(king_sq) {
            continue;
        }
        let slide = occupied ^ Bitboard::from_square(from);
        let attackers = attackers_to_color(pos, to, slide, us);
        if (attackers ^ Bitboard::from_square(from)).is_empty() {
            continue;
        }
        if pos.discovered(from, to, our_king, our_pinned) {
            continue;
        }
        if can_king_escape_with_from(pos, them, from, to, bb_attacks, slide) {
            continue;
        }
        if can_piece_capture(pos, them, to, pinned, slide) {
            continue;
        }
        return Some(Move::make_promote(from, to, pos.piece_on(from)));
    }

    #[cfg(feature = "mate1ply-full")]
    if !dc_candidates.is_empty() {
        let enemy_bb = enemy_field(us);
        let mut bb_candidates = dc_candidates;

        while let Some(from_sq) = bb_candidates.pop_lsb() {
            from = from_sq;
            let mut pt = pos.piece_on(from).piece_type();

            match pt {
                PieceType::PAWN => {
                    if from.file() == king_sq.file() {
                        continue;
                    }
                    to = square_offset(from, 0, if us == Color::BLACK { -1 } else { 1 });
                    if to.is_none() {
                        continue;
                    }
                    if pos.piece_on(to) != Piece::NO_PIECE && pos.piece_on(to).color() != them {
                        continue;
                    }
                    if !can_promote_to(us, to) {
                        continue;
                    }
                    bb_attacks = gold_effect(us, to);
                    if !bb_attacks.test(king_sq) {
                        continue;
                    }
                    if pos.discovered(from, to, our_king, our_pinned) {
                        continue;
                    }
                    let slide = occupied ^ Bitboard::from_square(from);
                    if can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                        continue;
                    }
                    return Some(Move::make_promote(from, to, pos.piece_on(from)));
                }
                PieceType::LANCE => continue,
                PieceType::KNIGHT => {
                    if !check_around_bb(us, PieceType::KNIGHT, king_sq).test(from) {
                        continue;
                    }
                    let mut bb = knight_effect(us, from) & knight_effect(them, king_sq) & bb_move;
                    while let Some(to_sq) = bb.pop_lsb() {
                        to = to_sq;
                        if aligned(from, to, king_sq) {
                            continue;
                        }
                        bb_attacks = knight_effect(us, to);
                        if bb_attacks.test(king_sq) {
                            continue;
                        }
                        if pos.discovered(from, to, our_king, our_pinned) {
                            continue;
                        }
                        let slide = occupied ^ Bitboard::from_square(from);
                        if can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                            continue;
                        }
                        return Some(Move::make(from, to, pos.piece_on(from)));
                    }

                    let mut bb = knight_effect(us, from) & gold_effect(them, king_sq) & bb_move;
                    while let Some(to_sq) = bb.pop_lsb() {
                        to = to_sq;
                        if aligned(from, to, king_sq) {
                            continue;
                        }
                        if !can_promote(us, from, to) {
                            continue;
                        }
                        bb_attacks = gold_effect(us, to);
                        if bb_attacks.test(king_sq) {
                            continue;
                        }
                        if pos.discovered(from, to, our_king, our_pinned) {
                            continue;
                        }
                        let slide = occupied ^ Bitboard::from_square(from);
                        if can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                            continue;
                        }
                        return Some(Move::make_promote(from, to, pos.piece_on(from)));
                    }
                    continue;
                }
                PieceType::SILVER => {
                    if !check_around_bb(us, PieceType::SILVER, king_sq).test(from) {
                        continue;
                    }
                    let mut bb = silver_effect(us, from) & silver_effect(them, king_sq) & bb_move;
                    while let Some(to_sq) = bb.pop_lsb() {
                        to = to_sq;
                        if aligned(from, to, king_sq) {
                            continue;
                        }
                        bb_attacks = silver_effect(us, to);
                        if bb_attacks.test(king_sq) {
                            continue;
                        }
                        if pos.discovered(from, to, our_king, our_pinned) {
                            continue;
                        }
                        let slide = occupied ^ Bitboard::from_square(from);
                        if can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                            continue;
                        }
                        return Some(Move::make(from, to, pos.piece_on(from)));
                    }

                    let mut bb = silver_effect(us, from) & gold_effect(them, king_sq) & bb_move;
                    while let Some(to_sq) = bb.pop_lsb() {
                        to = to_sq;
                        if aligned(from, to, king_sq) {
                            continue;
                        }
                        if !can_promote(us, from, to) {
                            continue;
                        }
                        bb_attacks = gold_effect(us, to);
                        if bb_attacks.test(king_sq) {
                            continue;
                        }
                        if pos.discovered(from, to, our_king, our_pinned) {
                            continue;
                        }
                        let slide = occupied ^ Bitboard::from_square(from);
                        if can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                            continue;
                        }
                        return Some(Move::make_promote(from, to, pos.piece_on(from)));
                    }
                    continue;
                }
                PieceType::PRO_PAWN
                | PieceType::PRO_LANCE
                | PieceType::PRO_KNIGHT
                | PieceType::PRO_SILVER => {
                    pt = PieceType::GOLD;
                    if !check_around_bb(us, PieceType::GOLD, king_sq).test(from) {
                        continue;
                    }
                }
                PieceType::GOLD => {
                    if !check_around_bb(us, PieceType::GOLD, king_sq).test(from) {
                        continue;
                    }
                }
                _ => {}
            }

            let mut bb = match pt {
                PieceType::GOLD => gold_effect(us, from) & gold_effect(them, king_sq),
                PieceType::BISHOP => {
                    let mut bb = bishop_effect(king_sq, occupied);
                    let extra = if can_promote_to(us, from) {
                        king_effect(king_sq)
                    } else {
                        king_effect(king_sq) & enemy_bb
                    };
                    bb = bb | extra;
                    bb & bishop_effect(from, occupied)
                }
                PieceType::HORSE => horse_effect(from, occupied) & horse_effect(king_sq, occupied),
                PieceType::ROOK => {
                    let mut bb = rook_effect(king_sq, occupied);
                    let extra = if can_promote_to(us, from) {
                        king_effect(king_sq)
                    } else {
                        king_effect(king_sq) & enemy_bb
                    };
                    bb = bb | extra;
                    bb & rook_effect(from, occupied)
                }
                PieceType::DRAGON => {
                    dragon_effect(from, occupied) & dragon_effect(king_sq, occupied)
                }
                _ => continue,
            };

            bb = bb & bb_move;
            let is_enemy_from = can_promote_to(us, from);

            while let Some(to_sq) = bb.pop_lsb() {
                to = to_sq;
                let promo = is_enemy_from || can_promote_to(us, to);
                if aligned(from, to, king_sq) {
                    continue;
                }
                if pos.discovered(from, to, our_king, our_pinned) {
                    continue;
                }

                let slide = occupied ^ Bitboard::from_square(from);
                bb_attacks = match pt {
                    PieceType::GOLD => gold_effect(us, to),
                    PieceType::BISHOP => {
                        let mut bb = bishop_step_effect(to);
                        if promo {
                            bb = bb | king_effect(to);
                        }
                        bb
                    }
                    PieceType::HORSE => bishop_step_effect(to) | king_effect(to),
                    PieceType::ROOK => {
                        let mut bb = rook_step_effect(to);
                        if promo {
                            bb = bb | king_effect(to);
                        }
                        bb
                    }
                    PieceType::DRAGON => rook_step_effect(to) | king_effect(to),
                    _ => Bitboard::EMPTY,
                };

                if bb_attacks.is_empty() {
                    continue;
                }
                if !can_king_escape_cangoto(pos, them, from, to, bb_attacks, slide) {
                    let from_piece = pos.piece_on(from);
                    if promo && !is_promoted(pt) && pt != PieceType::GOLD {
                        return Some(Move::make_promote(from, to, from_piece));
                    }
                    return Some(Move::make(from, to, from_piece));
                }
            }
        }
    }

    #[cfg(feature = "mate1ply-full")]
    if !dc_candidates.is_empty() && hand_only_pawns(them_hand) {
        let mut bb_candidates = dc_candidates & around24_bb(king_sq);

        while let Some(from_sq) = bb_candidates.pop_lsb() {
            from = from_sq;

            let mut atk = attackers_to_color(pos, from, occupied, them)
                .and_not(Bitboard::from_square(king_sq));
            if atk.any() {
                if atk.count() >= 2 {
                    continue;
                }
            } else {
                atk = around24_bb(king_sq) & bb_move;
            }

            let mut pt = pos.piece_on(from).piece_type();
            let mut bb_attacks = match pt {
                PieceType::PAWN | PieceType::LANCE => continue,
                PieceType::KNIGHT => {
                    let rank_ok = if us == Color::BLACK {
                        from.rank() >= Rank::RANK_3 && from.rank() <= Rank::RANK_5
                    } else {
                        from.rank() >= Rank::RANK_5 && from.rank() <= Rank::RANK_7
                    };
                    if !rank_ok {
                        continue;
                    }
                    knight_effect(us, from) & gold_effect(them, king_sq).not()
                }
                PieceType::SILVER => silver_effect(us, from),
                PieceType::PRO_PAWN
                | PieceType::PRO_LANCE
                | PieceType::PRO_KNIGHT
                | PieceType::PRO_SILVER
                | PieceType::GOLD => {
                    pt = PieceType::GOLD;
                    gold_effect(us, from) & gold_effect(them, king_sq).not()
                }
                PieceType::BISHOP => bishop_effect(from, occupied),
                PieceType::HORSE => horse_effect(from, occupied) & king_effect(king_sq).not(),
                PieceType::ROOK => rook_effect(from, occupied),
                PieceType::DRAGON => dragon_effect(from, occupied) & king_effect(king_sq).not(),
                PieceType::KING => continue,
                _ => continue,
            };

            let mut targets = bb_attacks & atk;
            let slide = occupied ^ Bitboard::from_square(from);
            while let Some(to_sq) = targets.pop_lsb() {
                to = to_sq;
                if aligned(from, to, king_sq) {
                    continue;
                }
                if pos.discovered(from, to, our_king, our_pinned) {
                    continue;
                }
                if can_pawn_drop(pos, them, from) {
                    continue;
                }
                let cap_pawn = pos.piece_on(to).piece_type() == PieceType::PAWN;
                if cap_pawn && from.file() == to.file() {
                    continue;
                }

                let new_slide = slide | Bitboard::from_square(to);
                let new_pinned = pos.pinned_pieces_after_move(them, from, to);

                if can_piece_capture_with_avoid(pos, them, from, to, new_pinned, new_slide) {
                    continue;
                }
                if king_effect(king_sq).test(to) {
                    let attackers = attackers_to_color(pos, to, occupied, us);
                    if (attackers ^ Bitboard::from_square(from)).is_empty() {
                        continue;
                    }
                }

                let new_slide_king = new_slide ^ Bitboard::from_square(king_sq);
                let is_mate = |bb_attacks: Bitboard| -> bool {
                    if bb_attacks.test(king_sq) {
                        return false;
                    }
                    let blocked = bb_attacks
                        | attacks_around_king_in_avoiding(pos, them, from, new_slide_king)
                        | pos.bitboards().color_pieces(them);
                    if king_effect(king_sq).and_not(blocked).any() {
                        return false;
                    }

                    let mut s1 = king_sq;
                    let step = next_square(s1, from);
                    if step.is_none() {
                        return false;
                    }
                    let df = step.file().raw() - from.file().raw();
                    let dr = step.rank().raw() - from.rank().raw();
                    let mut s2 = square_offset(s1, df, dr);
                    if s2.is_none() {
                        return false;
                    }

                    loop {
                        if can_piece_capture_with_avoid(pos, them, s2, to, new_pinned, new_slide) {
                            return false;
                        }
                        if s2 != from && pos.piece_on(s2) != Piece::NO_PIECE {
                            break;
                        }
                        if can_pawn_drop(pos, them, s2) || (cap_pawn && s2.file() == to.file()) {
                            return false;
                        }
                        let s3 = next_square(s1, s2);
                        s1 = s2;
                        s2 = s3;
                        if s2.is_none() {
                            return true;
                        }
                    }
                    false
                };

                if pt == PieceType::SILVER {
                    if can_promote(us, from, to) && is_mate(gold_effect(us, to)) {
                        return Some(Move::make_promote(from, to, pos.piece_on(from)));
                    }
                    if is_mate(silver_effect(us, to)) {
                        return Some(Move::make(from, to, pos.piece_on(from)));
                    }
                    continue;
                }

                bb_attacks = match pt {
                    PieceType::KNIGHT | PieceType::GOLD => gold_effect(us, to),
                    PieceType::BISHOP => {
                        if can_promote(us, from, to) {
                            horse_effect(to, new_slide)
                        } else {
                            bishop_effect(to, new_slide)
                        }
                    }
                    PieceType::HORSE => horse_effect(to, new_slide),
                    PieceType::ROOK => {
                        if can_promote(us, from, to) {
                            dragon_effect(to, new_slide)
                        } else {
                            rook_effect(to, new_slide)
                        }
                    }
                    PieceType::DRAGON => dragon_effect(to, new_slide),
                    _ => Bitboard::EMPTY,
                };

                if is_mate(bb_attacks) {
                    let from_piece = pos.piece_on(from);
                    if can_promote(us, from, to)
                        && !is_promoted(from_piece.piece_type())
                        && pt != PieceType::GOLD
                    {
                        return Some(Move::make_promote(from, to, from_piece));
                    }
                    return Some(Move::make(from, to, from_piece));
                }
            }
        }
    }

    None
}

#[cfg(feature = "mate1ply-full")]
#[must_use]
pub fn mate_1ply_extension(pos: &Position) -> Option<Move> {
    let mut moves = MoveList::new();
    if pos.checkers().is_empty() {
        generate_moves::<NonEvasionsAll>(pos, &mut moves);
    } else {
        generate_moves::<Evasions>(pos, &mut moves);
    }

    let mut local = pos.clone();
    local.init_stack();
    let mut evasions = MoveList::new();

    for mv in moves.iter().copied() {
        if !pos.is_legal(mv) {
            continue;
        }
        if !pos.gives_check(mv) {
            continue;
        }
        local.do_move_with_gives_check(mv, true);
        if local.checkers().is_empty() {
            let _ = local.undo_move(mv);
            continue;
        }

        evasions.clear();
        generate_moves::<Evasions>(&local, &mut evasions);
        let mut has_legal = false;
        for ev in evasions.iter().copied() {
            if local.is_legal(ev) {
                has_legal = true;
                break;
            }
        }
        let _ = local.undo_move(mv);
        if !has_legal {
            return Some(mv);
        }
    }

    None
}
