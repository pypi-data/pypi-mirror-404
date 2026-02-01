use crate::types::{Move, PieceType, Square};

#[test]
fn pawn_drop_mate_reference_position_detected() {
    let sfen = "l+N4knl/6g2/4+P2p1/p2s1Pp1p/1pp1l2P1/P1sK2P1P/1P3S1r1/5G3/LN7 w R2BGSN4Pgp 106";
    let pos = crate::board::position_from_sfen(sfen).expect("valid SFEN");

    let to = Square::from_usi("6e").expect("valid square");
    let drop = Move::make_drop(PieceType::PAWN, to, pos.side_to_move());
    assert!(pos.gives_check(drop), "drop should give check");
    assert!(!pos.legal_pawn_drop(pos.side_to_move(), to));
    assert!(!pos.is_legal(drop), "pawn drop mate must be rejected by is_legal");
}

#[test]
fn pawn_drop_mate_reference_position_not_detected() {
    let sfen = "l+N4knl/6g2/4+P2p1/p1s2Pp1p/1pp1l2P1/P1sK2P1P/1P3S1r1/5G3/LN7 w R2BGSN3Pg2p 1";
    let pos = crate::board::position_from_sfen(sfen).expect("valid SFEN");

    let to = Square::from_usi("6e").expect("valid square");
    let drop = Move::make_drop(PieceType::PAWN, to, pos.side_to_move());
    assert!(pos.gives_check(drop), "drop should give check");
    assert!(pos.legal_pawn_drop(pos.side_to_move(), to));
    assert!(pos.is_legal(drop), "non-mating pawn drop must be legal");
}
