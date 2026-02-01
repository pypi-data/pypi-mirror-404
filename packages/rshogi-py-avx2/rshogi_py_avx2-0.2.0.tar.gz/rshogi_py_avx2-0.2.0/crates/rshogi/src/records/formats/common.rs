use crate::board::{Position, SfenError};
use std::collections::HashMap;

pub(crate) type BoardMap = HashMap<(u8, u8), (char, String)>;
pub(crate) type HandCounts = HashMap<char, HashMap<String, u8>>;

const HAND_ORDER: [&str; 7] = ["FU", "KY", "KE", "GI", "KI", "KA", "HI"];

fn csa_piece_to_sfen(piece_code: &str, color: char) -> Option<String> {
    let token = match piece_code {
        "FU" => "P",
        "KY" => "L",
        "KE" => "N",
        "GI" => "S",
        "KI" => "G",
        "KA" => "B",
        "HI" => "R",
        "OU" => "K",
        "TO" => "+P",
        "NY" => "+L",
        "NK" => "+N",
        "NG" => "+S",
        "UM" => "+B",
        "RY" => "+R",
        _ => return None,
    };

    if token.starts_with('+') {
        let piece = token.chars().nth(1)?;
        let normalized =
            if color == '-' { piece.to_ascii_lowercase().to_string() } else { piece.to_string() };
        return Some(format!("+{normalized}"));
    }

    let normalized = if color == '-' { token.to_ascii_lowercase() } else { token.to_string() };
    Some(normalized)
}

pub(crate) fn board_map_to_sfen(board_map: &BoardMap) -> Result<String, String> {
    let mut rows = Vec::with_capacity(9);
    for rank in 1..=9 {
        let mut empties = 0;
        let mut row = String::new();
        for file in (1..=9).rev() {
            if let Some((color, piece_code)) = board_map.get(&(file, rank)) {
                if empties > 0 {
                    row.push_str(&empties.to_string());
                    empties = 0;
                }
                let token = csa_piece_to_sfen(piece_code, *color)
                    .ok_or_else(|| format!("unknown piece code: {piece_code}"))?;
                row.push_str(&token);
            } else {
                empties += 1;
            }
        }
        if empties > 0 {
            row.push_str(&empties.to_string());
        }
        if row.is_empty() {
            row.push('9');
        }
        rows.push(row);
    }
    Ok(rows.join("/"))
}

pub(crate) fn hand_counts_to_sfen(hand_counts: &HandCounts) -> Result<String, String> {
    let mut parts: Vec<String> = Vec::new();
    for (color, lower) in [('+', false), ('-', true)] {
        let counts =
            hand_counts.get(&color).ok_or_else(|| "hand counts missing side".to_string())?;
        for piece_code in HAND_ORDER {
            let count = counts.get(piece_code).copied().unwrap_or(0);
            if count == 0 {
                continue;
            }
            let letter = csa_piece_to_sfen(piece_code, '+')
                .ok_or_else(|| format!("unknown hand piece code: {piece_code}"))?;
            let normalized = if lower { letter.to_ascii_lowercase() } else { letter };
            let token = if count > 1 { format!("{count}{normalized}") } else { normalized };
            parts.push(token);
        }
    }
    if parts.is_empty() {
        Ok("-".to_string())
    } else {
        Ok(parts.join(""))
    }
}

pub(crate) fn ensure_hand_sides(hand_counts: &mut HandCounts) {
    hand_counts.entry('+').or_default();
    hand_counts.entry('-').or_default();
}

pub(crate) fn refresh_position_if_needed(
    pos: &mut Position,
    since_refresh: &mut usize,
) -> Result<(), SfenError> {
    const REFRESH_INTERVAL: usize = 200;
    *since_refresh += 1;
    if *since_refresh >= REFRESH_INTERVAL {
        let sfen = pos.sfen(None);
        pos.set(&sfen)?;
        *since_refresh = 0;
    }
    Ok(())
}
