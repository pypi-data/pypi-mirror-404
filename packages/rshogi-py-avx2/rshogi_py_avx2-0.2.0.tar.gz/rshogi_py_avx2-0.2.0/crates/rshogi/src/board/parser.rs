//! SFEN/USIのパースとシリアライズ

use super::position::{BoardArray, PackedPiece, Ply, Position};
use crate::types::{Color, File, Hand, HandPiece, Piece, PieceType, Rank, Square};
use std::convert::TryFrom;
use std::fmt;

/// SFEN解析エラー
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SfenError {
    MissingField(MissingFieldKind),
    InvalidPiece(char),
    InvalidSquare,
    InvalidHandCount { piece: PieceType, count: u8 },
    InvalidTurn(char),
    InvalidPly(std::num::ParseIntError),
    TrailingToken(String),
    InvalidMove(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MissingFieldKind {
    Placement,
    Turn,
    Hand,
    Ply,
}

impl fmt::Display for SfenError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingField(kind) => write!(f, "Missing field: {kind:?}"),
            Self::InvalidPiece(piece) => write!(f, "Invalid piece: '{piece}'"),
            Self::InvalidSquare => write!(f, "Invalid square"),
            Self::InvalidHandCount { piece, count } => {
                write!(f, "Invalid hand count for {piece:?}: {count}")
            }
            Self::InvalidTurn(turn) => write!(f, "Invalid turn: '{turn}'"),
            Self::InvalidPly(err) => write!(f, "Invalid ply: {err}"),
            Self::TrailingToken(token) => write!(f, "Trailing token: '{token}'"),
            Self::InvalidMove(mv) => write!(f, "Invalid move in sequence: '{mv}'"),
        }
    }
}

impl std::error::Error for SfenError {}

pub struct SfenData {
    pub board: BoardArray,
    pub hands: [Hand; Color::COLOR_NB],
    pub side_to_move: Color,
    pub ply: Ply,
}

/// SFEN文字列を解析
pub fn parse_sfen(sfen: &str) -> Result<SfenData, SfenError> {
    let tokens: Vec<&str> = sfen.split_whitespace().collect();
    if tokens.is_empty() {
        return Err(SfenError::MissingField(MissingFieldKind::Placement));
    }

    if tokens.len() < 3 {
        return Err(SfenError::MissingField(match tokens.len() {
            0 => MissingFieldKind::Placement,
            1 => MissingFieldKind::Turn,
            _ => MissingFieldKind::Hand,
        }));
    }

    let board = parse_board(tokens[0])?;
    let side_to_move = parse_turn(tokens[1])?;
    let hands = parse_hands(tokens[2])?;
    let ply = if tokens.len() >= 4 { parse_ply(tokens[3])? } else { 0 };

    Ok(SfenData { board, hands, side_to_move, ply })
}

/// SFEN文字列を生成
#[must_use]
pub fn generate_sfen(pos: &Position) -> String {
    generate_sfen_with_ply(pos, Some(i32::from(pos.game_ply())))
}

/// SFEN文字列を生成（手数の出力を制御）
#[must_use]
pub fn generate_sfen_with_ply(pos: &Position, ply: Option<i32>) -> String {
    let mut result = String::new();

    // 1. 盤面
    for rank_idx in 0..9 {
        let rank = Rank::new(i8::try_from(rank_idx).expect("rank index within range"));
        let mut empty_count = 0;
        for file_idx in (0..9).rev() {
            let file = File::new(i8::try_from(file_idx).expect("file index within range"));
            let sq = Square::from_file_rank(file, rank);
            let piece = pos.piece_on(sq);

            if piece == Piece::NO_PIECE {
                empty_count += 1;
            } else {
                if empty_count > 0 {
                    result.push_str(&empty_count.to_string());
                    empty_count = 0;
                }
                // 成り駒の場合は+を追加
                let piece_type = piece.piece_type();
                if piece_type.raw() >= 9 && piece_type.raw() <= 14 {
                    result.push('+');
                }
                result.push(piece_to_sfen_char(piece));
            }
        }

        if empty_count > 0 {
            result.push_str(&empty_count.to_string());
        }

        if rank_idx < 8 {
            result.push('/');
        }
    }

    // 2. 手番
    result.push(' ');
    result.push(if pos.side_to_move() == Color::BLACK { 'b' } else { 'w' });

    // 3. 持ち駒
    result.push(' ');
    let hands_str = generate_hands(pos);
    if hands_str.is_empty() {
        result.push('-');
    } else {
        result.push_str(&hands_str);
    }

    // 4. 手数
    if let Some(ply) = ply {
        result.push(' ');
        result.push_str(&ply.to_string());
    }

    result
}

// --- Helper functions ---

fn parse_board(s: &str) -> Result<BoardArray, SfenError> {
    let mut board = BoardArray::empty();
    let mut rank: i8 = 0;
    let mut file: i8 = 8;
    let mut chars = s.chars();

    while let Some(ch) = chars.next() {
        match ch {
            '/' => {
                if file != -1 {
                    return Err(SfenError::InvalidSquare);
                }
                rank += 1;
                file = 8;
            }
            '1'..='9' => {
                let skip = i8::try_from(ch.to_digit(10).expect("digit")).expect("skip fits in i8");
                file -= skip;
                if file < -1 {
                    return Err(SfenError::InvalidSquare);
                }
            }
            '+' => {
                // 成り駒: 次の文字を読む
                if file < 0 || rank >= 9 {
                    return Err(SfenError::InvalidSquare);
                }

                let next_ch = chars.next().ok_or(SfenError::InvalidPiece('+'))?;
                let piece = sfen_char_to_promoted_piece(next_ch)?;
                let sq = Square::from_file_rank(File::new(file), Rank::new(rank));
                board.set(sq, PackedPiece::from_piece(piece));
                file -= 1;
            }
            _ => {
                if file < 0 || rank >= 9 {
                    return Err(SfenError::InvalidSquare);
                }
                let piece = sfen_char_to_piece(ch)?;
                let sq = Square::from_file_rank(File::new(file), Rank::new(rank));
                board.set(sq, PackedPiece::from_piece(piece));
                file -= 1;
            }
        }
    }

    if rank != 8 || file != -1 {
        return Err(SfenError::InvalidSquare);
    }

    Ok(board)
}

fn parse_turn(s: &str) -> Result<Color, SfenError> {
    match s {
        "b" => Ok(Color::BLACK),
        "w" => Ok(Color::WHITE),
        _ => Err(SfenError::InvalidTurn(s.chars().next().unwrap_or(' '))),
    }
}

fn parse_hands(s: &str) -> Result<[Hand; Color::COLOR_NB], SfenError> {
    let mut hands = [Hand::HAND_ZERO; Color::COLOR_NB];

    if s == "-" {
        return Ok(hands);
    }

    let mut count = 1;
    let mut chars = s.chars().peekable();

    while let Some(ch) = chars.next() {
        if ch.is_ascii_digit() {
            count = 0;
            count = count * 10 + ch.to_digit(10).expect("digit");

            // 複数桁の数字を読む
            while let Some(&next_ch) = chars.peek() {
                if next_ch.is_ascii_digit() {
                    chars.next();
                    count = count * 10 + next_ch.to_digit(10).expect("digit");
                } else {
                    break;
                }
            }
        } else {
            let color = if ch.is_ascii_uppercase() { Color::BLACK } else { Color::WHITE };
            let piece = sfen_char_to_hand_piece(ch)?;

            for _ in 0..count {
                let idx = color.to_index();
                hands[idx] = Hand::add_hand(hands[idx], piece);
            }

            count = 1;
        }
    }

    Ok(hands)
}

fn parse_ply(s: &str) -> Result<Ply, SfenError> {
    s.parse::<Ply>().map_err(SfenError::InvalidPly)
}

const fn sfen_char_to_piece(ch: char) -> Result<Piece, SfenError> {
    let piece = match ch.to_ascii_lowercase() {
        'p' => Piece::make(Color::BLACK, PieceType::PAWN),
        'l' => Piece::make(Color::BLACK, PieceType::LANCE),
        'n' => Piece::make(Color::BLACK, PieceType::KNIGHT),
        's' => Piece::make(Color::BLACK, PieceType::SILVER),
        'g' => Piece::make(Color::BLACK, PieceType::GOLD),
        'b' => Piece::make(Color::BLACK, PieceType::BISHOP),
        'r' => Piece::make(Color::BLACK, PieceType::ROOK),
        'k' => Piece::make(Color::BLACK, PieceType::KING),
        '+' => {
            // 成り駒は次の文字を見る必要がある
            return Err(SfenError::InvalidPiece(ch));
        }
        _ => return Err(SfenError::InvalidPiece(ch)),
    };

    // 小文字なら後手
    let piece =
        if ch.is_ascii_lowercase() { Piece::make(Color::WHITE, piece.piece_type()) } else { piece };

    Ok(piece)
}

/// SFEN文字から成り駒への変換（'+'の次の文字を受け取る）
const fn sfen_char_to_promoted_piece(ch: char) -> Result<Piece, SfenError> {
    let piece_type = match ch.to_ascii_lowercase() {
        'p' => PieceType::PRO_PAWN,
        'l' => PieceType::PRO_LANCE,
        'n' => PieceType::PRO_KNIGHT,
        's' => PieceType::PRO_SILVER,
        'b' => PieceType::HORSE,
        'r' => PieceType::DRAGON,
        _ => return Err(SfenError::InvalidPiece(ch)),
    };

    // 大文字なら先手、小文字なら後手
    let color = if ch.is_ascii_uppercase() { Color::BLACK } else { Color::WHITE };

    Ok(Piece::make(color, piece_type))
}

fn sfen_char_to_hand_piece(ch: char) -> Result<HandPiece, SfenError> {
    match ch.to_ascii_lowercase() {
        'p' => Ok(HandPiece::from_piece_type(PieceType::PAWN).unwrap()),
        'l' => Ok(HandPiece::from_piece_type(PieceType::LANCE).unwrap()),
        'n' => Ok(HandPiece::from_piece_type(PieceType::KNIGHT).unwrap()),
        's' => Ok(HandPiece::from_piece_type(PieceType::SILVER).unwrap()),
        'g' => Ok(HandPiece::from_piece_type(PieceType::GOLD).unwrap()),
        'b' => Ok(HandPiece::from_piece_type(PieceType::BISHOP).unwrap()),
        'r' => Ok(HandPiece::from_piece_type(PieceType::ROOK).unwrap()),
        _ => Err(SfenError::InvalidPiece(ch)),
    }
}

fn piece_to_sfen_char(piece: Piece) -> char {
    if piece == Piece::NO_PIECE {
        return '.';
    }

    let piece_type = piece.piece_type();

    // 成り駒の場合は+付きで返す必要があるため、特別処理
    let ch = match piece_type {
        pt if pt == PieceType::PAWN => 'P',
        pt if pt == PieceType::LANCE => 'L',
        pt if pt == PieceType::KNIGHT => 'N',
        pt if pt == PieceType::SILVER => 'S',
        pt if pt == PieceType::GOLD => 'G',
        pt if pt == PieceType::BISHOP => 'B',
        pt if pt == PieceType::ROOK => 'R',
        pt if pt == PieceType::KING => 'K',
        pt if pt == PieceType::PRO_PAWN => 'P', // 成り駒は元の駒種を返す
        pt if pt == PieceType::PRO_LANCE => 'L',
        pt if pt == PieceType::PRO_KNIGHT => 'N',
        pt if pt == PieceType::PRO_SILVER => 'S',
        pt if pt == PieceType::HORSE => 'B',
        pt if pt == PieceType::DRAGON => 'R',
        _ => '?',
    };

    if piece.color() == Color::WHITE {
        ch.to_ascii_lowercase()
    } else {
        ch
    }
}

fn generate_hands(pos: &Position) -> String {
    let mut result = String::new();

    for color in [Color::BLACK, Color::WHITE] {
        let hand = pos.hand_of(color);

        // 飛、角、金、銀、桂、香、歩の順（YaneuraOu互換）
        let order = [
            HandPiece::from_piece_type(PieceType::ROOK).unwrap(),
            HandPiece::from_piece_type(PieceType::BISHOP).unwrap(),
            HandPiece::from_piece_type(PieceType::GOLD).unwrap(),
            HandPiece::from_piece_type(PieceType::SILVER).unwrap(),
            HandPiece::from_piece_type(PieceType::KNIGHT).unwrap(),
            HandPiece::from_piece_type(PieceType::LANCE).unwrap(),
            HandPiece::from_piece_type(PieceType::PAWN).unwrap(),
        ];

        for hp in order {
            let count = Hand::hand_count(hand, hp);
            if count > 0 {
                if count > 1 {
                    result.push_str(&count.to_string());
                }

                let ch = match hp.into_piece_type() {
                    PieceType::PAWN => 'P',
                    PieceType::LANCE => 'L',
                    PieceType::KNIGHT => 'N',
                    PieceType::SILVER => 'S',
                    PieceType::GOLD => 'G',
                    PieceType::BISHOP => 'B',
                    PieceType::ROOK => 'R',
                    _ => '?',
                };

                result.push(if color == Color::BLACK { ch } else { ch.to_ascii_lowercase() });
            }
        }
    }

    result
}
