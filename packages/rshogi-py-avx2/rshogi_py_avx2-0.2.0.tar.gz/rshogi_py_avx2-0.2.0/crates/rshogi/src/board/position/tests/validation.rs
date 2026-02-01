use super::*;
use crate::types::{Color, File};

#[test]
// 初期局面がis_validで正常判定されることを確認
fn valid_initial_position() {
    let pos = crate::board::hirate_position();

    match pos.is_valid() {
        Ok(()) => {}
        Err(e) => panic!("Initial position should be valid, but got error: {e:?}"),
    }
}

#[test]
// 玉が二枚ある局面を弾くことを確認（先手側）
fn two_kings_is_invalid() {
    let sfen = "k8/9/9/9/9/9/9/9/K7K b - 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
        if let Err(e) = result {
            assert_eq!(e, ValidationError::TwoKings(Color::BLACK));
        }
    }
}

#[test]
// 玉が欠けた局面を許容することを検証
fn no_king_is_allowed() {
    let sfen = "lnsg1gsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSG1GSNL b - 1";

    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    assert!(pos.is_valid().is_ok());
}

#[test]
// 玉が1枚だけの局面は許容されることを確認
fn single_king_position_is_allowed() {
    let sfen = "K8/9/9/9/9/9/9/9/9 b - 1";

    let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");
    assert!(pos.is_valid().is_ok());
}

#[test]
// 同一筋の二歩を検出できることを確認
fn double_pawn_is_invalid() {
    let sfen = "lnsgkgsnP/1r5b1/ppppppppp/9/9/9/PPPPPPPP1/1B5RP/LNSGKGSNL b - 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
        if let Err(e) = result {
            match e {
                ValidationError::DoublePawn(file, color) => {
                    assert_eq!(file, File::FILE_1);
                    assert_eq!(color, Color::BLACK);
                }
                _ => panic!("Expected DoublePawn error"),
            }
        }
    }
}

#[test]
// 持ち駒の枚数超過を検出することを確認
fn invalid_hand_count_is_rejected() {
    let sfen = "lnsgkgsnl/1r5b1/9/9/9/9/9/1B5R1/LNSGKGSNL b 19P 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
    }
}

#[test]
// 最奥段の歩・香を不正として扱うことを確認
fn pawn_and_lance_on_last_rank_are_invalid() {
    let sfen = "P8/9/9/9/9/9/9/9/K8 b - 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
    }
}

#[test]
// 桂馬が最奥2段以内にある場合を不正と判定できるか検証
fn knight_on_last_two_ranks_is_invalid() {
    let sfen = "k8/N8/9/9/9/9/9/9/K8 b - 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
    }
}

#[test]
// 駒総数超過の異常局面を検出することを確認
fn excessive_total_piece_count_is_invalid() {
    let sfen = "ppppppppp/ppppppppp/9/9/9/9/9/9/K8 b 2P 1";

    if let Ok(pos) = crate::board::position_from_sfen(sfen) {
        let result = pos.is_valid();
        assert!(result.is_err());
    }
}
