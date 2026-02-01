use super::helpers::{apply_usi_move, move_from_usi};
use super::*;
use crate::board::zobrist::Zobrist;
use crate::types::{Piece, Square};

#[test]
// 通常手適用後のZobrist更新内容が理論値と一致するか検証
fn zobrist_after_normal_move_matches_expected() {
    let mut pos = crate::board::hirate_position();

    let initial_zobrist = pos.key();
    let mut board_key = pos.board_key();
    let hand_key = pos.hand_key();

    apply_usi_move(&mut pos, "7g7f");

    assert_ne!(pos.key(), initial_zobrist);

    let from = Square::from_usi("7g").unwrap();
    let to = Square::from_usi("7f").unwrap();
    board_key ^= Zobrist::psq(from, Piece::B_PAWN);
    board_key ^= Zobrist::psq(to, Piece::B_PAWN);
    board_key ^= Zobrist::side();
    let expected = board_key ^ hand_key;

    assert_eq!(pos.key(), expected);
}

#[test]
// 捕獲を含む手でZobrist更新が期待値通りか確認
fn zobrist_after_capture_matches_expected() {
    let sfen = "lnsgk1snl/1r4gb1/p1pppp2p/6pp1/1p7/2P6/PP1PPPP1P/1BG4R1/LNS1KGSNL b p 11";
    let mut pos = crate::board::position_from_sfen(sfen).unwrap();

    let initial_zobrist = pos.key();
    let mut board_key = pos.board_key();
    let mut hand_key = pos.hand_key();

    let mv = move_from_usi(&pos, "2h2d");
    let from = mv.from_sq();
    let to = mv.to_sq();
    let moved_piece = pos.piece_on(from);
    let captured_piece = pos.piece_on(to);
    let us = pos.side_to_move();
    assert!(pos.is_legal(mv));
    pos.do_move(mv);

    assert_ne!(pos.key(), initial_zobrist);

    let moved_after = if mv.is_promote() { moved_piece.promote() } else { moved_piece };
    board_key ^= Zobrist::psq(from, moved_piece);
    if captured_piece != Piece::NO_PIECE {
        board_key ^= Zobrist::psq(to, captured_piece);
    }
    board_key ^= Zobrist::psq(to, moved_after);
    board_key ^= Zobrist::side();
    if captured_piece != Piece::NO_PIECE {
        hand_key.add(Zobrist::hand(us, captured_piece.piece_type().demote(), 1));
    }
    let expected = board_key ^ hand_key;

    assert_eq!(pos.key(), expected);
}

#[test]
// 駒打ち時のZobrist更新が正しく行われるか検証
fn zobrist_after_drop_matches_expected() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPP1PPPP/1B5R1/LNSGKGSNL b P 1";
    let mut pos = crate::board::position_from_sfen(sfen).unwrap();

    let initial_zobrist = pos.key();
    let mut board_key = pos.board_key();
    let mut hand_key = pos.hand_key();

    apply_usi_move(&mut pos, "P*5e");

    assert_ne!(pos.key(), initial_zobrist);

    let to = Square::from_usi("5e").unwrap();
    board_key ^= Zobrist::psq(to, Piece::B_PAWN);
    board_key ^= Zobrist::side();
    hand_key.sub(Zobrist::hand(Color::BLACK, PieceType::PAWN, 1));
    let expected = board_key ^ hand_key;

    assert_eq!(pos.key(), expected);
}

#[test]
// 成りを含む手のZobrist更新が期待通りか確認
fn zobrist_after_promote_matches_expected() {
    let sfen = "lnsgk1snl/1p4g2/pR1ppp2p/2p6/9/9/P1SPPPP1P/2G6/LN2KGSNL b B3Prb2p 25";
    let mut pos = crate::board::position_from_sfen(sfen).unwrap();

    let mut board_key = pos.board_key();
    let hand_key = pos.hand_key();

    let mv = move_from_usi(&pos, "8c8f+");
    let from = mv.from_sq();
    let to = mv.to_sq();
    let moved_piece = pos.piece_on(from);
    assert!(pos.is_legal(mv));
    pos.do_move(mv);

    assert_ne!(pos.key(), board_key ^ hand_key);

    board_key ^= Zobrist::psq(from, moved_piece);
    board_key ^= Zobrist::psq(to, moved_piece.promote());
    board_key ^= Zobrist::side();
    let expected = board_key ^ hand_key;

    assert_eq!(pos.key(), expected);
}

#[test]
// 異なる手順で同一局面に到達した際Zobristが一致するか確認
fn zobrist_is_consistent_for_equivalent_sequences() {
    let mut pos1 = crate::board::hirate_position();

    let from1 = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_7);
    let to1 = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_6);
    let piece1 = pos1.piece_on(from1);
    let mv1 = Move::make(from1, to1, piece1);
    pos1.do_move(mv1);

    let from2 = Square::from_file_rank(crate::types::File::FILE_3, crate::types::Rank::RANK_3);
    let to2 = Square::from_file_rank(crate::types::File::FILE_3, crate::types::Rank::RANK_4);
    let piece2 = pos1.piece_on(from2);
    let mv2 = Move::make(from2, to2, piece2);
    pos1.do_move(mv2);

    let sfen = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL b - 3";
    let pos2 = crate::board::position_from_sfen(sfen).unwrap();

    assert_eq!(pos1.key(), pos2.key());
}

#[test]
// 初期局面のZobristがゼロ値にならないことを確認（YaneuraOu互換チェック）
fn zobrist_initial_position_is_non_zero() {
    let pos = crate::board::hirate_position();

    assert_ne!(pos.key().low_u64(), 0);
}

#[test]
// 既知の手順でZobristが変化することを確認（YaneuraOu互換チェック）
fn zobrist_changes_after_known_sequence() {
    let mut pos = crate::board::hirate_position();
    let initial = pos.key();

    for usi in ["7g7f", "3c3d", "2g2f"] {
        apply_usi_move(&mut pos, usi);
    }

    assert_ne!(pos.key(), initial);
}

#[test]
// Zobristテーブルの特定エントリがゼロでないことを確認
fn zobrist_table_sample_entry_is_non_zero() {
    let sq = Square::from_file_rank(crate::types::File::FILE_5, crate::types::Rank::RANK_5);
    let piece = Piece::make(Color::BLACK, PieceType::PAWN);
    let hash = Zobrist::psq(sq, piece);

    assert_ne!(hash.low_u64(), 0);
}
