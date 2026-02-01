use super::helpers::move_from_usi;
use super::*;
use crate::types::square::SQ_99;

#[test]
fn piece_list_updates_on_normal_move() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    assert_eq!(pos.piece_list().piece_count(Color::BLACK, PieceType::PAWN), 9);
    let pawns = pos.piece_list().pieces(Color::BLACK, PieceType::PAWN);
    assert_eq!(pawns.len(), 9);

    let from_sq = Square::from_file_rank(File::FILE_2, Rank::RANK_7);
    let to_sq = Square::from_file_rank(File::FILE_2, Rank::RANK_6);
    let from_piece = pos.piece_on(from_sq);
    let mv = Move::make(from_sq, to_sq, from_piece);
    pos.do_move(mv);

    let pawns_after = pos.piece_list().pieces(Color::BLACK, PieceType::PAWN);
    assert_eq!(pawns_after.len(), 9, "pawn count should remain");
    assert!(pawns_after.contains(&to_sq), "pawn should move to destination");
    assert!(!pawns_after.contains(&from_sq), "pawn should leave origin");

    pos.undo_move(mv).expect("undo move");
    let pawns_restored = pos.piece_list().pieces(Color::BLACK, PieceType::PAWN);
    assert_eq!(pawns_restored.len(), 9);
    assert!(pawns_restored.contains(&from_sq), "pawn should return to origin");
    assert!(!pawns_restored.contains(&to_sq), "pawn should be removed from destination");
}

#[test]
fn piece_list_updates_on_drop_move() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b G 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    assert_eq!(pos.piece_list().piece_count(Color::BLACK, PieceType::GOLD), 2);

    let to_sq = Square::from_file_rank(File::FILE_5, Rank::RANK_5);
    let mv = Move::make_drop(PieceType::GOLD, to_sq, Color::BLACK);
    pos.do_move(mv);

    let golds_after = pos.piece_list().pieces(Color::BLACK, PieceType::GOLD);
    assert_eq!(golds_after.len(), 3, "gold count should increase");
    assert!(golds_after.contains(&to_sq), "gold should appear on destination");

    pos.undo_move(mv).expect("undo move");
    let golds_restored = pos.piece_list().pieces(Color::BLACK, PieceType::GOLD);
    assert_eq!(golds_restored.len(), 2, "gold count should restore");
    assert!(!golds_restored.contains(&to_sq), "gold should be removed from destination");
}

#[test]
fn piece_list_updates_on_capture_move() {
    let sfen = "lnsgk1snl/1r4gb1/p1pppp2p/6pp1/1p7/2P6/PP1PPPP1P/1BG4R1/LNS1KGSNL b p 11";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    let mv = move_from_usi(&pos, "2h2d");
    let from_sq = mv.from_sq();
    let to_sq = mv.to_sq();
    let moved_piece = pos.piece_on(from_sq);
    let captured_piece = pos.piece_on(to_sq);
    assert_ne!(captured_piece, Piece::NO_PIECE);
    let moved_count_before =
        pos.piece_list().piece_count(moved_piece.color(), moved_piece.piece_type());
    let captured_count_before =
        pos.piece_list().piece_count(captured_piece.color(), captured_piece.piece_type());
    assert!(captured_count_before > 0, "captured piece must exist in piece_list");
    assert!(pos.is_legal(mv));
    pos.do_move(mv);

    let moved_after = pos.piece_list().pieces(moved_piece.color(), moved_piece.piece_type());
    assert!(moved_after.contains(&to_sq), "moved piece should be on destination");
    assert_eq!(
        moved_count_before,
        pos.piece_list().piece_count(moved_piece.color(), moved_piece.piece_type()),
        "moved piece count should remain"
    );

    assert_eq!(
        pos.piece_list().piece_count(captured_piece.color(), captured_piece.piece_type()),
        captured_count_before - 1,
        "captured piece count should be updated"
    );
    let captured_list =
        pos.piece_list().pieces(captured_piece.color(), captured_piece.piece_type());
    assert!(!captured_list.contains(&to_sq), "captured piece should be removed");

    pos.undo_move(mv).expect("undo move");
    let moved_restored = pos.piece_list().pieces(moved_piece.color(), moved_piece.piece_type());
    assert!(moved_restored.contains(&from_sq), "moved piece should return to origin");

    assert_eq!(
        pos.piece_list().piece_count(captured_piece.color(), captured_piece.piece_type()),
        captured_count_before,
        "captured piece count should restore"
    );
}

#[test]
fn piece_list_updates_on_promotion_move() {
    let sfen = "lnsgk1snl/1p4g2/pR1ppp2p/2p6/9/9/P1SPPPP1P/2G6/LN2KGSNL b B3Prb2p 25";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    let mv = move_from_usi(&pos, "8c8f+");
    let from_sq = mv.from_sq();
    let to_sq = mv.to_sq();
    let from_piece = pos.piece_on(from_sq);
    let initial_count = pos.piece_list().piece_count(from_piece.color(), from_piece.piece_type());
    let promoted_piece = from_piece.promote();
    assert_eq!(
        pos.piece_list().piece_count(promoted_piece.color(), promoted_piece.piece_type()),
        0
    );
    assert!(pos.is_legal(mv));
    pos.do_move(mv);

    assert_eq!(
        pos.piece_list().piece_count(from_piece.color(), from_piece.piece_type()),
        initial_count - 1,
        "original piece count should decrease"
    );
    assert_eq!(
        pos.piece_list().piece_count(promoted_piece.color(), promoted_piece.piece_type()),
        1,
        "promoted piece count should increase"
    );
    let promoted_list =
        pos.piece_list().pieces(promoted_piece.color(), promoted_piece.piece_type());
    assert!(promoted_list.contains(&to_sq), "promoted piece should be on destination");

    pos.undo_move(mv).expect("undo move");
    assert_eq!(
        pos.piece_list().piece_count(from_piece.color(), from_piece.piece_type()),
        initial_count,
        "original piece count should restore"
    );
    assert_eq!(
        pos.piece_list().piece_count(promoted_piece.color(), promoted_piece.piece_type()),
        0,
        "promoted piece count should reset"
    );
}

#[test]
fn piece_list_matches_board_state() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    for color in [Color::BLACK, Color::WHITE] {
        for pt in 0..PieceType::PIECE_TYPE_NB {
            #[allow(clippy::cast_possible_truncation)]
            let piece_type = PieceType::new(pt as i8);
            if piece_type == PieceType::NO_PIECE_TYPE {
                continue;
            }

            let pieces = pos.piece_list().pieces(color, piece_type);
            for &sq in pieces {
                let piece_on_board = pos.piece_on(sq);
                assert_eq!(piece_on_board.color(), color, "piece_list color should match board");
                assert_eq!(
                    piece_on_board.piece_type(),
                    piece_type,
                    "piece_list piece type should match board"
                );
            }
        }
    }
}

#[test]
fn piece_list_matches_board_after_multiple_moves() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    let mut pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    let moves = [
        (
            Square::from_file_rank(File::FILE_2, Rank::RANK_7),
            Square::from_file_rank(File::FILE_2, Rank::RANK_6),
        ),
        (
            Square::from_file_rank(File::FILE_3, Rank::RANK_3),
            Square::from_file_rank(File::FILE_3, Rank::RANK_4),
        ),
        (
            Square::from_file_rank(File::FILE_2, Rank::RANK_6),
            Square::from_file_rank(File::FILE_2, Rank::RANK_5),
        ),
    ];

    for (from_sq, to_sq) in &moves {
        let from_piece = pos.piece_on(*from_sq);
        let mv = Move::make(*from_sq, *to_sq, from_piece);
        pos.do_move(mv);

        for color in [Color::BLACK, Color::WHITE] {
            for pt in 0..PieceType::PIECE_TYPE_NB {
                #[allow(clippy::cast_possible_truncation)]
                let piece_type = PieceType::new(pt as i8);
                if piece_type == PieceType::NO_PIECE_TYPE {
                    continue;
                }

                let pieces = pos.piece_list().pieces(color, piece_type);
                for &sq in pieces {
                    let piece_on_board = pos.piece_on(sq);
                    assert_eq!(
                        piece_on_board.color(),
                        color,
                        "piece_list color should match board after move"
                    );
                    assert_eq!(
                        piece_on_board.piece_type(),
                        piece_type,
                        "piece_list type should match board after move"
                    );
                }
            }
        }
    }
}

#[test]
fn piece_list_tracks_promoted_pieces_from_sfen() {
    // data/bench/mate3_ci.sfenから成り駒を含むSFENを使用
    // l5l1l/4lsS2/p2p1p3/7pk/1pP2Np2/5NPGg/PP1P1P2R/2G2S3/+bNSK1G3 b RPbn5p 111
    // このSFENには1つの後手成り駒(+b = 馬 at 9i)が含まれている
    let sfen = "l5l1l/4lsS2/p2p1p3/7pk/1pP2Np2/5NPGg/PP1P1P2R/2G2S3/+bNSK1G3 b RPbn5p 111";
    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

    let piece_list = pos.piece_list();

    let horse_squares = piece_list.pieces(Color::WHITE, PieceType::HORSE);
    assert_eq!(horse_squares.len(), 1, "HORSE count should be 1");
    assert_eq!(horse_squares[0], SQ_99, "HORSE should be at 9i (row 8, col 0)");

    let bishop_squares = piece_list.pieces(Color::WHITE, PieceType::BISHOP);
    assert_eq!(bishop_squares.len(), 0, "BISHOP count should be 0 (成駒として登録されているため)");
}
