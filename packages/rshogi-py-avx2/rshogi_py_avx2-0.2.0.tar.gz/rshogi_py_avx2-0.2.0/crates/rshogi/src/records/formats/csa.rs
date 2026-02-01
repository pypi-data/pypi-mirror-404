use crate::board::{Position, SfenError};
use crate::records::formats::common::{
    board_map_to_sfen, ensure_hand_sides, hand_counts_to_sfen, refresh_position_if_needed,
    BoardMap, HandCounts,
};
use crate::records::record::{MoveRecord, Record, RecordResult};
use crate::types::{Color, GameResult, Piece, PieceType, Square};
use std::collections::HashMap;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CsaError {
    #[error("SFEN parsing failed: {0}")]
    Sfen(#[from] SfenError),
    #[error("invalid CSA line: {0}")]
    InvalidLine(String),
    #[error("invalid CSA board line: {0}")]
    InvalidBoard(String),
    #[error("invalid CSA move line: {0}")]
    InvalidMove(String),
    #[error("illegal move at index {index}")]
    IllegalMove { index: usize },
    #[error("missing CSA end marker")]
    MissingEndMarker,
}

const INITIAL_COUNTS: [(char, [(&str, u8); 8]); 2] = [
    ('+', [("FU", 9), ("KY", 2), ("KE", 2), ("GI", 2), ("KI", 2), ("KA", 1), ("HI", 1), ("OU", 1)]),
    ('-', [("FU", 9), ("KY", 2), ("KE", 2), ("GI", 2), ("KI", 2), ("KA", 1), ("HI", 1), ("OU", 1)]),
];

fn base_piece(piece_code: &str) -> &str {
    match piece_code {
        "TO" => "FU",
        "NY" => "KY",
        "NK" => "KE",
        "NG" => "GI",
        "UM" => "KA",
        "RY" => "HI",
        _ => piece_code,
    }
}

fn parse_row_lines(lines: &[String]) -> Result<BoardMap, CsaError> {
    let mut board_map: BoardMap = HashMap::new();
    let mut rows: HashMap<u8, String> = HashMap::new();
    for line in lines {
        let rank = line
            .chars()
            .nth(1)
            .and_then(|ch| ch.to_digit(10))
            .ok_or_else(|| CsaError::InvalidBoard(line.clone()))? as u8;
        rows.insert(rank, line[2..].to_string());
    }
    for rank in 1..=9 {
        let row_spec = rows.get(&rank).cloned().unwrap_or_default();
        let compact: String = row_spec.chars().filter(|ch| *ch != ' ').collect();
        let mut file = 9u8;
        let mut idx = 0usize;
        let chars: Vec<char> = compact.chars().collect();
        while file >= 1 && idx < chars.len() {
            let token = chars[idx];
            if token == '+' || token == '-' {
                if idx + 2 >= chars.len() {
                    return Err(CsaError::InvalidBoard(row_spec));
                }
                let piece_code = format!("{}{}", chars[idx + 1], chars[idx + 2]);
                board_map.insert((file, rank), (token, piece_code));
                idx += 3;
            } else if token == '*' {
                idx += 1;
            } else {
                return Err(CsaError::InvalidBoard(row_spec));
            }
            if file == 1 {
                break;
            }
            file -= 1;
        }
    }
    Ok(board_map)
}

fn parse_piece_line(line: &str) -> Result<Vec<(char, String, String)>, CsaError> {
    let mut chars = line.chars();
    if chars.next() != Some('P') {
        return Err(CsaError::InvalidLine(line.to_string()));
    }
    let color = chars
        .next()
        .filter(|ch| *ch == '+' || *ch == '-')
        .ok_or_else(|| CsaError::InvalidLine(line.to_string()))?;
    let mut data: String = chars.collect();
    data.retain(|ch| ch != ' ');
    if data.is_empty() {
        return Ok(Vec::new());
    }
    if data.len() % 4 != 0 {
        return Err(CsaError::InvalidLine(line.to_string()));
    }
    let mut out = Vec::new();
    let bytes = data.as_bytes();
    for idx in (0..bytes.len()).step_by(4) {
        let square = String::from_utf8(bytes[idx..idx + 2].to_vec())
            .map_err(|_| CsaError::InvalidLine(line.to_string()))?;
        let piece_code = String::from_utf8(bytes[idx + 2..idx + 4].to_vec())
            .map_err(|_| CsaError::InvalidLine(line.to_string()))?;
        out.push((color, square, piece_code));
    }
    Ok(out)
}

fn decode_start_board() -> BoardMap {
    let mut board = HashMap::new();
    let mut pos = Position::new();
    pos.set_hirate();
    for rank in 1..=9 {
        for file in 1..=9 {
            let file_char = char::from(b'0' + file);
            let rank_char = char::from(b'a' + (rank - 1));
            let sq = Square::from_usi(&format!("{file_char}{rank_char}")).expect("valid square");
            let piece = pos.piece_on(sq);
            if piece == Piece::NO_PIECE {
                continue;
            }
            let color = if piece.color() == Color::BLACK { '+' } else { '-' };
            let piece_code = match piece.piece_type() {
                PieceType::PAWN => "FU",
                PieceType::LANCE => "KY",
                PieceType::KNIGHT => "KE",
                PieceType::SILVER => "GI",
                PieceType::GOLD => "KI",
                PieceType::BISHOP => "KA",
                PieceType::ROOK => "HI",
                PieceType::KING => "OU",
                PieceType::PRO_PAWN => "TO",
                PieceType::PRO_LANCE => "NY",
                PieceType::PRO_KNIGHT => "NK",
                PieceType::PRO_SILVER => "NG",
                PieceType::HORSE => "UM",
                PieceType::DRAGON => "RY",
                _ => "OU",
            };
            board.insert((file, rank), (color, piece_code.to_string()));
        }
    }
    board
}

fn game_result_from_marker(marker: &str, side_to_move: Color) -> GameResult {
    let is_black_turn = side_to_move == Color::BLACK;
    match marker {
        "%TORYO" => {
            if is_black_turn {
                GameResult::WhiteWin
            } else {
                GameResult::BlackWin
            }
        }
        "%SENNICHITE" => GameResult::DrawByRepetition,
        "%MAX_MOVES" => GameResult::DrawByMaxPlies,
        "%KACHI" => {
            if is_black_turn {
                GameResult::BlackWinByDeclaration
            } else {
                GameResult::WhiteWinByDeclaration
            }
        }
        "%CHUDAN" => GameResult::Paused,
        "%ILLEGAL_MOVE" => {
            if is_black_turn {
                GameResult::BlackWinByIllegalMove
            } else {
                GameResult::WhiteWinByIllegalMove
            }
        }
        "%TIME_UP" => {
            if is_black_turn {
                GameResult::BlackWinByTimeout
            } else {
                GameResult::WhiteWinByTimeout
            }
        }
        "%ERROR" => GameResult::Error,
        _ => GameResult::Paused,
    }
}

fn game_result_to_marker(result: GameResult) -> &'static str {
    match result {
        GameResult::BlackWin | GameResult::WhiteWin => "%TORYO",
        GameResult::DrawByRepetition => "%SENNICHITE",
        GameResult::DrawByMaxPlies => "%MAX_MOVES",
        GameResult::BlackWinByDeclaration
        | GameResult::WhiteWinByDeclaration
        | GameResult::BlackWinByForfeit
        | GameResult::WhiteWinByForfeit => "%KACHI",
        GameResult::BlackWinByIllegalMove | GameResult::WhiteWinByIllegalMove => "%ILLEGAL_MOVE",
        GameResult::BlackWinByTimeout | GameResult::WhiteWinByTimeout => "%TIME_UP",
        GameResult::Error => "%ERROR",
        GameResult::Invalid | GameResult::Paused => "%CHUDAN",
    }
}

pub fn parse_csa_str(text: &str) -> Result<Record, CsaError> {
    let mut lines: Vec<String> =
        text.lines().map(|line| line.trim_end_matches('\r').to_string()).collect();
    if let Some(first) = lines.first_mut() {
        *first = first.trim_start_matches('\u{feff}').to_string();
    }

    let mut pos = Position::new();
    let mut position_lines: Vec<String> = Vec::new();
    let mut side_to_move_token: Option<char> = None;
    let mut header_end = lines.len();

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            header_end = idx + 1;
            break;
        }
        if trimmed.starts_with('+') || trimmed.starts_with('-') || trimmed.starts_with('%') {
            if trimmed.len() >= 7 {
                header_end = idx;
                break;
            }
            side_to_move_token = trimmed.chars().next();
            continue;
        }
        if trimmed.starts_with('P') {
            position_lines.push(trimmed.to_string());
            continue;
        }
    }

    let row_lines: Vec<String> = position_lines
        .iter()
        .filter(|line| {
            line.len() >= 2
                && line.starts_with('P')
                && line.chars().nth(1).unwrap().is_ascii_digit()
        })
        .cloned()
        .collect();
    let pi_line = position_lines.iter().find(|line| line.starts_with("PI")).cloned();
    let piece_lines: Vec<String> = position_lines
        .iter()
        .filter(|line| line.starts_with("P+") || line.starts_with("P-"))
        .cloned()
        .collect();

    let mut board_map: BoardMap = if position_lines.is_empty() {
        decode_start_board()
    } else if !row_lines.is_empty() {
        parse_row_lines(&row_lines)?
    } else if let Some(pi_line) = pi_line {
        let mut start = decode_start_board();
        let suffix = pi_line[2..].trim();
        if !suffix.is_empty() {
            if suffix.len() % 4 != 0 {
                return Err(CsaError::InvalidBoard(pi_line));
            }
            let bytes = suffix.as_bytes();
            for idx in (0..bytes.len()).step_by(4) {
                let square = String::from_utf8(bytes[idx..idx + 2].to_vec())
                    .map_err(|_| CsaError::InvalidBoard(pi_line.clone()))?;
                let file = square.chars().next().and_then(|ch| ch.to_digit(10)).unwrap_or(0);
                let rank = square.chars().nth(1).and_then(|ch| ch.to_digit(10)).unwrap_or(0);
                if file >= 1 && rank >= 1 {
                    start.remove(&(file as u8, rank as u8));
                }
            }
        }
        start
    } else {
        HashMap::new()
    };

    let mut hand_counts: HandCounts = HashMap::new();
    ensure_hand_sides(&mut hand_counts);
    let mut fill_remaining: HashMap<char, bool> = HashMap::new();
    fill_remaining.insert('+', false);
    fill_remaining.insert('-', false);

    for entry_line in piece_lines {
        for (color, square, piece_code) in parse_piece_line(&entry_line)? {
            if square == "00" {
                if piece_code == "AL" {
                    fill_remaining.insert(color, true);
                    continue;
                }
                let entry = hand_counts.entry(color).or_default().entry(piece_code).or_insert(0);
                *entry += 1;
            } else {
                let file = square.chars().next().and_then(|ch| ch.to_digit(10)).unwrap_or(0);
                let rank = square.chars().nth(1).and_then(|ch| ch.to_digit(10)).unwrap_or(0);
                if file >= 1 && rank >= 1 {
                    board_map.insert((file as u8, rank as u8), (color, piece_code));
                }
            }
        }
    }

    let mut placed_counts: HashMap<char, HashMap<String, u8>> = HashMap::new();
    for (color, initial) in INITIAL_COUNTS {
        let mut map = HashMap::new();
        for (piece_code, _) in initial {
            map.insert(piece_code.to_string(), 0);
        }
        placed_counts.insert(color, map);
    }

    for (color, piece_code) in board_map.values().map(|(c, p)| (*c, p.clone())) {
        let base = base_piece(&piece_code).to_string();
        if let Some(counts) = placed_counts.get_mut(&color) {
            if let Some(entry) = counts.get_mut(&base) {
                *entry += 1;
            }
        }
    }

    for (color, counts) in hand_counts.clone() {
        for (piece_code, count) in counts {
            let base = base_piece(&piece_code).to_string();
            if let Some(entries) = placed_counts.get_mut(&color) {
                if let Some(entry) = entries.get_mut(&base) {
                    *entry += count;
                }
            }
        }
    }

    for (color, initial) in INITIAL_COUNTS {
        if !*fill_remaining.get(&color).unwrap_or(&false) {
            continue;
        }
        for (piece_code, initial_count) in initial {
            let base = piece_code.to_string();
            let placed = placed_counts
                .get(&color)
                .and_then(|counts| counts.get(&base))
                .copied()
                .unwrap_or(0);
            if placed < initial_count {
                let remaining = initial_count - placed;
                let entry = hand_counts.entry(color).or_default().entry(base.clone()).or_insert(0);
                *entry += remaining;
            }
        }
    }

    let board_sfen = board_map_to_sfen(&board_map).map_err(CsaError::InvalidBoard)?;
    let hands_sfen = hand_counts_to_sfen(&hand_counts).map_err(CsaError::InvalidBoard)?;
    let turn = if side_to_move_token == Some('-') { "w" } else { "b" };
    let init_position_sfen = format!("{board_sfen} {turn} {hands_sfen} 1");

    pos.set(&init_position_sfen)?;

    let mut moves: Vec<MoveRecord> = Vec::new();
    let mut result: Option<GameResult> = None;
    let mut idx = header_end;
    let mut refresh_counter = 0usize;

    while idx < lines.len() {
        let line = lines[idx].trim();
        idx += 1;
        if line.is_empty() {
            continue;
        }
        if line.starts_with('\'') || line.starts_with('T') {
            continue;
        }
        if line.starts_with('%') {
            result = Some(game_result_from_marker(line, pos.side_to_move()));
            break;
        }
        if line.starts_with('+') || line.starts_with('-') {
            let move_token = line.split(',').next().unwrap_or(line);
            if move_token.len() < 7 {
                return Err(CsaError::InvalidMove(line.to_string()));
            }
            let mv = pos.move_from_csa(&move_token[1..7]);
            if !pos.is_legal(mv) {
                return Err(CsaError::IllegalMove { index: moves.len() });
            }
            pos.do_move(mv);
            moves.push(MoveRecord::new(mv, None));
            refresh_position_if_needed(&mut pos, &mut refresh_counter)?;
            continue;
        }
        return Err(CsaError::InvalidLine(line.to_string()));
    }

    let result = result.ok_or(CsaError::MissingEndMarker)?;
    let record_result = RecordResult::new(result, None, Some(moves.len()));
    Record::new(init_position_sfen, moves, record_result)
        .map_err(|e| CsaError::InvalidLine(e.to_string()))
}

fn append_csa_position_lines(lines: &mut Vec<String>, pos: &Position) {
    for rank in 1..=9u8 {
        let mut row = format!("P{rank}");
        for file in (1..=9u8).rev() {
            let file_char = char::from(b'0' + file);
            let rank_char = char::from(b'a' + (rank - 1));
            let sq = Square::from_usi(&format!("{file_char}{rank_char}")).expect("valid square");
            let piece = pos.piece_on(sq);
            if piece == Piece::NO_PIECE {
                row.push_str("*  ");
                continue;
            }
            let color = if piece.color() == Color::BLACK { '+' } else { '-' };
            let piece_code = match piece.piece_type() {
                PieceType::PAWN => "FU",
                PieceType::LANCE => "KY",
                PieceType::KNIGHT => "KE",
                PieceType::SILVER => "GI",
                PieceType::GOLD => "KI",
                PieceType::BISHOP => "KA",
                PieceType::ROOK => "HI",
                PieceType::KING => "OU",
                PieceType::PRO_PAWN => "TO",
                PieceType::PRO_LANCE => "NY",
                PieceType::PRO_KNIGHT => "NK",
                PieceType::PRO_SILVER => "NG",
                PieceType::HORSE => "UM",
                PieceType::DRAGON => "RY",
                _ => "OU",
            };
            row.push(color);
            row.push_str(piece_code);
        }
        lines.push(row);
    }

    for (color, label) in [(Color::BLACK, "P+"), (Color::WHITE, "P-")] {
        let hand = pos.hand_of(color);
        let mut line = label.to_string();
        for piece_code in ["FU", "KY", "KE", "GI", "KI", "KA", "HI"] {
            let piece_type = match piece_code {
                "FU" => PieceType::PAWN,
                "KY" => PieceType::LANCE,
                "KE" => PieceType::KNIGHT,
                "GI" => PieceType::SILVER,
                "KI" => PieceType::GOLD,
                "KA" => PieceType::BISHOP,
                "HI" => PieceType::ROOK,
                _ => PieceType::PAWN,
            };
            let hand_piece =
                crate::types::HandPiece::from_piece_type(piece_type).expect("valid hand piece");
            let count = hand.count(hand_piece);
            for _ in 0..count {
                line.push_str("00");
                line.push_str(piece_code);
            }
        }
        lines.push(line);
    }

    let stm = if pos.side_to_move() == Color::BLACK { "+" } else { "-" };
    lines.push(stm.to_string());
}

pub fn export_csa(record: &Record) -> Result<String, CsaError> {
    let mut pos = Position::new();
    pos.set(record.init_position_sfen())?;

    let mut lines: Vec<String> = vec!["V2.2".to_string()];
    append_csa_position_lines(&mut lines, &pos);
    let mut refresh_counter = 0usize;

    for (index, mv_record) in record.moves().iter().enumerate() {
        let mv = mv_record.mv();
        if !pos.is_legal(mv) {
            return Err(CsaError::IllegalMove { index });
        }
        let prefix = if pos.side_to_move() == Color::BLACK { '+' } else { '-' };
        let csa = mv
            .to_csa()
            .ok_or_else(|| CsaError::InvalidMove(format!("invalid move at index {index}")))?;
        lines.push(format!("{prefix}{csa}"));
        if let Some(eval) = mv_record.eval() {
            lines.push(format!("'**評価値={eval}"));
        }
        pos.do_move(mv);
        refresh_position_if_needed(&mut pos, &mut refresh_counter)?;
    }

    lines.push(game_result_to_marker(record.result().result()).to_string());
    Ok(lines.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::hirate_position;
    use crate::types::Move16;

    #[test]
    fn csa_roundtrip_basic() {
        let pos = hirate_position();
        let mv = pos.move_from_move16(Move16::from_usi("7g7f").unwrap());
        let record = Record::new(
            pos.sfen(None),
            vec![MoveRecord::new(mv, None)],
            RecordResult::new(GameResult::BlackWin, None, Some(1)),
        )
        .unwrap();

        let csa = export_csa(&record).unwrap();
        let parsed = parse_csa_str(&csa).unwrap();
        assert_eq!(parsed.moves().len(), 1);
        assert_eq!(parsed.result().result(), GameResult::BlackWin);
    }
}
