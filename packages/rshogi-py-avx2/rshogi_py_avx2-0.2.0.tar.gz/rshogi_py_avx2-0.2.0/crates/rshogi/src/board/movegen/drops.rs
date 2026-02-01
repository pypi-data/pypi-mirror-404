use crate::board::{Bitboard, Position};
use crate::types::{Color, Move, PieceType, Rank};

use super::types::MoveGenType;
use super::{ColorMarker, MoveSink};

fn pawn_drop_mask(us: Color, pawns: Bitboard) -> Bitboard {
    let left = Bitboard::rank_mask(Rank::RANK_9).packed_bits();
    let board_mask = (1u128 << 81) - 1;
    let mut t = left.wrapping_sub(pawns.packed_bits());
    if us == Color::BLACK {
        t = (t & left) >> 7;
        Bitboard::from_packed_bits(left ^ left.wrapping_sub(t))
    } else {
        t = (t & left) >> 8;
        let not_left = (!left) & board_mask;
        Bitboard::from_packed_bits(not_left & left.wrapping_sub(t))
    }
}

fn emit_drops_unrolled(
    targets: Bitboard,
    drops: [PieceType; 6],
    start_idx: usize,
    count: usize,
    us: Color,
    list: &mut impl MoveSink,
) {
    if count == 0 {
        return;
    }
    let mut squares = targets;
    while let Some(to) = squares.pop_lsb() {
        match count {
            1 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
            }
            2 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 1], to, us));
            }
            3 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 1], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 2], to, us));
            }
            4 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 1], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 2], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 3], to, us));
            }
            5 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 1], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 2], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 3], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 4], to, us));
            }
            6 => {
                list.push_move(Move::make_drop(drops[start_idx], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 1], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 2], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 3], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 4], to, us));
                list.push_move(Move::make_drop(drops[start_idx + 5], to, us));
            }
            _ => {}
        }
    }
}

#[allow(clippy::extra_unused_type_parameters, clippy::too_many_lines)]
#[inline]
pub(super) fn generate_drops_color<T: MoveGenType, C: ColorMarker>(
    pos: &Position,
    list: &mut impl MoveSink,
) {
    let empty = !pos.bitboards().occupied();
    generate_drops_for_target_color::<T, C>(pos, list, empty);
}

#[allow(clippy::extra_unused_type_parameters, clippy::too_many_lines)]
pub(super) fn generate_drops_for_target_color<T: MoveGenType, C: ColorMarker>(
    pos: &Position,
    list: &mut impl MoveSink,
    target: Bitboard,
) {
    use crate::board::attack_tables::PAWN_ATTACKS;
    use crate::types::HandPiece;

    let us = C::COLOR;
    let them = C::THEM;
    let bb = pos.bitboards();
    let hand = pos.hand_of(us);

    // 空きマスを取得
    let empty = !bb.occupied();
    let empty_target = empty.and(target);
    if empty_target.is_empty() {
        return;
    }

    // --- 歩の打ち駒（YaneuraOu互換: 先に生成）
    let Some(pawn_hand) = HandPiece::from_piece_type(PieceType::PAWN) else {
        return;
    };
    if hand.count(pawn_hand) > 0 {
        let pawns = bb.pieces_of(PieceType::PAWN, us);
        let mut target2 = empty_target & pawn_drop_mask(us, pawns);
        let pawn_drop_check = bb
            .pieces_of(PieceType::KING, them)
            .lsb()
            .map_or(Bitboard::EMPTY, |king_sq| PAWN_ATTACKS[king_sq.to_index()][them.to_index()]);
        if !pawn_drop_check.is_empty() {
            let to = pawn_drop_check.lsb().expect("pawn drop check square exists");
            if target2.test(to) && !pos.legal_drop(to) {
                target2 = target2.and_not(pawn_drop_check);
            }
        }

        let mut drop_targets = target2;
        while let Some(to) = drop_targets.pop_lsb() {
            list.push_move(Move::make_drop(PieceType::PAWN, to, us));
        }
    }

    // --- 歩以外の打ち駒（YaneuraOu互換: マス優先、駒種は KNIGHT → LANCE → SILVER → GOLD → BISHOP → ROOK）
    let mut drops: [PieceType; 6] = [
        PieceType::KNIGHT,
        PieceType::LANCE,
        PieceType::SILVER,
        PieceType::GOLD,
        PieceType::BISHOP,
        PieceType::ROOK,
    ];
    let mut drops_len = 0;

    if let Some(hand_piece) = HandPiece::from_piece_type(PieceType::KNIGHT) {
        if hand.count(hand_piece) > 0 {
            drops[drops_len] = PieceType::KNIGHT;
            drops_len += 1;
        }
    }
    let next_to_knight = drops_len;

    if let Some(hand_piece) = HandPiece::from_piece_type(PieceType::LANCE) {
        if hand.count(hand_piece) > 0 {
            drops[drops_len] = PieceType::LANCE;
            drops_len += 1;
        }
    }
    let next_to_lance = drops_len;

    for piece_type in [PieceType::SILVER, PieceType::GOLD, PieceType::BISHOP, PieceType::ROOK] {
        let Some(hand_piece) = HandPiece::from_piece_type(piece_type) else {
            continue;
        };
        if hand.count(hand_piece) == 0 {
            continue;
        }
        drops[drops_len] = piece_type;
        drops_len += 1;
    }

    if drops_len == 0 {
        return;
    }

    if next_to_lance == 0 {
        emit_drops_unrolled(empty_target, drops, 0, drops_len, us, list);
        return;
    }

    let rank1 = if us == Color::BLACK { Rank::RANK_1 } else { Rank::RANK_9 };
    let rank2 = if us == Color::BLACK { Rank::RANK_2 } else { Rank::RANK_8 };
    let rank3_to_9 = if us == Color::BLACK {
        Bitboard::rank_mask(Rank::RANK_3)
            | Bitboard::rank_mask(Rank::RANK_4)
            | Bitboard::rank_mask(Rank::RANK_5)
            | Bitboard::rank_mask(Rank::RANK_6)
            | Bitboard::rank_mask(Rank::RANK_7)
            | Bitboard::rank_mask(Rank::RANK_8)
            | Bitboard::rank_mask(Rank::RANK_9)
    } else {
        Bitboard::rank_mask(Rank::RANK_1)
            | Bitboard::rank_mask(Rank::RANK_2)
            | Bitboard::rank_mask(Rank::RANK_3)
            | Bitboard::rank_mask(Rank::RANK_4)
            | Bitboard::rank_mask(Rank::RANK_5)
            | Bitboard::rank_mask(Rank::RANK_6)
            | Bitboard::rank_mask(Rank::RANK_7)
    };

    let target1 = empty_target & Bitboard::rank_mask(rank1);
    let target2 = empty_target & Bitboard::rank_mask(rank2);
    let target3 = empty_target & rank3_to_9;

    // 1段目: 香・桂を除外
    emit_drops_unrolled(target1, drops, next_to_lance, drops_len - next_to_lance, us, list);
    // 2段目: 桂を除外
    emit_drops_unrolled(target2, drops, next_to_knight, drops_len - next_to_knight, us, list);
    // 3～9段目: 全駒
    emit_drops_unrolled(target3, drops, 0, drops_len, us, list);
}
