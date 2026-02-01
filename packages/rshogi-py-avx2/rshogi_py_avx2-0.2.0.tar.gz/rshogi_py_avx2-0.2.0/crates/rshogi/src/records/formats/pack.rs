use crate::records::record::Record;
use crate::{
    board::{Position, SfenError},
    types::{Color, GameResult, Square},
};
use thiserror::Error;

/// Pack 形式のシリアライゼーションエラー。
#[derive(Debug, Error)]
pub enum PackError {
    #[error("SFEN parsing failed: {0}")]
    Sfen(#[from] SfenError),

    #[error("move {0} missing eval")]
    MissingEval(usize),

    #[error("game ply {0} exceeds 65535")]
    PlyOutOfRange(u32),

    #[error("move {index} is not legal")]
    IllegalMove { index: usize },

    #[error("invalid result for pack encoding: {0:?}")]
    InvalidResult(GameResult),
}

/// `Record` を pack 形式バイト列にシリアライズします。
pub fn serialize(record: &Record) -> Result<Vec<u8>, PackError> {
    let mut pos = Position::new();
    pos.set(record.init_position_sfen())?;

    let mut data = Vec::new();

    if is_startpos(&pos) {
        data.push(1);
    } else {
        data.push(0);
        let packed = pos.sfen_pack();
        data.extend_from_slice(&packed.data);

        let ply_number = pos.game_ply() as u32;
        if ply_number > 0xFFFF {
            return Err(PackError::PlyOutOfRange(ply_number));
        }
        data.extend_from_slice(&(ply_number as u16).to_le_bytes());
    }

    for (index, mv_record) in record.moves().iter().enumerate() {
        let eval = mv_record.eval().ok_or(PackError::MissingEval(index))?;
        let mv = mv_record.mv();
        if !pos.is_legal(mv) {
            return Err(PackError::IllegalMove { index });
        }
        let mv16 = mv.to_move16();
        data.extend_from_slice(&mv16.0.to_le_bytes());
        data.extend_from_slice(&clamp_eval(eval).to_le_bytes());
        pos.do_move(mv);
    }

    let (raw_result, reason_code) = pack_result_code(record)?;
    let end_marker = raw_result | (raw_result << 7);
    data.extend_from_slice(&end_marker.to_le_bytes());
    data.push(reason_code);

    Ok(data)
}

fn clamp_eval(value: i32) -> i16 {
    if value < -32000 {
        -32000
    } else if value > 32000 {
        32000
    } else {
        value as i16
    }
}

fn is_startpos(pos: &Position) -> bool {
    let mut start = Position::new();
    start.set_hirate();

    if pos.side_to_move() != start.side_to_move() {
        return false;
    }

    for color in [Color::BLACK, Color::WHITE] {
        if pos.hand_of(color) != start.hand_of(color) {
            return false;
        }
    }

    for sq_idx in 0..Square::SQ_NB {
        let sq = Square::from_index(sq_idx);
        if pos.piece_on(sq) != start.piece_on(sq) {
            return false;
        }
    }

    true
}

fn pack_result_code(record: &Record) -> Result<(u16, u8), PackError> {
    let result = record.result().result();
    if result.is_draw() {
        let reason = if result == GameResult::DrawByMaxPlies { 2 } else { 1 };
        return Ok((0, reason));
    }

    if result.is_black_win() {
        let reason = if result == GameResult::BlackWinByDeclaration { 10 } else { 0 };
        return Ok((1, reason));
    }

    if result.is_white_win() {
        let reason = if result == GameResult::WhiteWinByDeclaration { 10 } else { 0 };
        return Ok((2, reason));
    }

    Err(PackError::InvalidResult(result))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::records::record::{MoveRecord, Record, RecordResult};
    use crate::{
        board,
        types::{GameResult, Move16},
    };

    const STARTING_SFEN: &str = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

    #[test]
    fn serialize_start_position_without_moves() {
        let record = Record::new(
            STARTING_SFEN.to_string(),
            Vec::new(),
            RecordResult::new(GameResult::DrawByMaxPlies, None, Some(0)),
        )
        .unwrap();

        let bytes = serialize(&record).unwrap();
        assert_eq!(bytes, vec![1, 0, 0, 2]);
    }

    #[test]
    fn missing_eval_is_error() {
        let pos = board::hirate_position();
        let mv16 = Move16::from_usi("7g7f").unwrap();
        let mv = pos.move_from_move16(mv16);
        let record = Record::new(
            STARTING_SFEN.to_string(),
            vec![MoveRecord::new(mv, None)],
            RecordResult::new(GameResult::BlackWin, None, Some(1)),
        )
        .unwrap();

        assert!(matches!(serialize(&record), Err(PackError::MissingEval(0))));
    }

    #[test]
    fn non_start_position_writes_ply() {
        let extra_sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPP1PPPP/1B5R1/LNSGKGSNL b - 3";

        let record = Record::new(
            extra_sfen.to_string(),
            Vec::new(),
            RecordResult::new(GameResult::DrawByRepetition, None, None),
        )
        .unwrap();

        let bytes = serialize(&record).unwrap();
        assert_eq!(bytes[0], 0);
        assert_eq!(bytes.len(), 1 + 32 + 2 + 3);
        let ply = u16::from_le_bytes([bytes[33], bytes[34]]);
        assert_eq!(ply, 3);
    }

    #[test]
    fn invalid_result_returns_error() {
        let record = Record::new(
            STARTING_SFEN.to_string(),
            Vec::new(),
            RecordResult::new(GameResult::Error, None, Some(0)),
        )
        .unwrap();

        assert!(matches!(serialize(&record), Err(PackError::InvalidResult(GameResult::Error))));
    }
}
