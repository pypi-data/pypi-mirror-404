use crate::board::{Position, SfenError};
use crate::records::formats::common::{
    board_map_to_sfen, ensure_hand_sides, hand_counts_to_sfen, refresh_position_if_needed,
    BoardMap, HandCounts,
};
use crate::records::record::{MoveRecord, Record, RecordResult};
use crate::types::{Color, GameResult, Move, Move16, Piece, PieceType, Square};
use std::collections::HashMap;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum KifError {
    #[error("SFEN parsing failed: {0}")]
    Sfen(#[from] SfenError),
    #[error("invalid KIF line: {0}")]
    InvalidLine(String),
    #[error("invalid KIF move: {0}")]
    InvalidMove(String),
    #[error("illegal move at index {index}")]
    IllegalMove { index: usize },
    #[error("missing KIF result")]
    MissingResult,
}

const KANJI_RANKS: [char; 9] = ['一', '二', '三', '四', '五', '六', '七', '八', '九'];
const WIDE_DIGITS: [char; 9] = ['１', '２', '３', '４', '５', '６', '７', '８', '９'];

fn normalize_kif_line(line: &str) -> String {
    let mut normalized = line.replace('王', "玉").replace('竜', "龍");
    normalized = normalized.replace("成銀", "全");
    normalized = normalized.replace("成桂", "圭");
    normalized = normalized.replace("成香", "杏");
    normalized = normalized.replace("成歩", "と");
    normalized
}

fn kanji_to_int(text: &str) -> u8 {
    if text.is_empty() {
        return 1;
    }
    let mut total = 0u8;
    let mut current = 0u8;
    for ch in text.chars() {
        match ch {
            '十' => {
                current = current.max(1);
                total = total.saturating_add(current.saturating_mul(10));
                current = 0;
            }
            '〇' | '零' => current = current.saturating_mul(10),
            '一' => current = current.saturating_mul(10).saturating_add(1),
            '二' => current = current.saturating_mul(10).saturating_add(2),
            '三' => current = current.saturating_mul(10).saturating_add(3),
            '四' => current = current.saturating_mul(10).saturating_add(4),
            '五' => current = current.saturating_mul(10).saturating_add(5),
            '六' => current = current.saturating_mul(10).saturating_add(6),
            '七' => current = current.saturating_mul(10).saturating_add(7),
            '八' => current = current.saturating_mul(10).saturating_add(8),
            '九' => current = current.saturating_mul(10).saturating_add(9),
            _ => {}
        }
    }
    let total = total.saturating_add(current);
    if total == 0 {
        1
    } else {
        total
    }
}

fn parse_hand_pieces(text: &str) -> HashMap<String, u8> {
    let cleaned = text.replace('　', " ").replace(' ', "");
    if cleaned.is_empty() || cleaned == "なし" {
        return HashMap::new();
    }
    let mut counts: HashMap<String, u8> = HashMap::new();
    let mut iter = cleaned.chars().peekable();
    while let Some(ch) = iter.next() {
        let piece_code = match ch {
            '歩' => "FU",
            '香' => "KY",
            '桂' => "KE",
            '銀' => "GI",
            '金' => "KI",
            '角' => "KA",
            '飛' => "HI",
            '玉' | '王' => "OU",
            _ => continue,
        };
        let mut number = String::new();
        while let Some(next) = iter.peek() {
            if "一二三四五六七八九十〇零".contains(*next) {
                number.push(*next);
                iter.next();
            } else {
                break;
            }
        }
        let count = kanji_to_int(&number);
        *counts.entry(piece_code.to_string()).or_insert(0) += count;
    }
    counts
}

fn is_board_header_line(line: &str) -> bool {
    line.contains('９') && line.contains('１') && line.trim_start().starts_with('９')
}

fn parse_board_block(lines: &[String], start_index: usize) -> Result<(usize, BoardMap), KifError> {
    let mut idx = start_index + 1;
    if idx < lines.len() && lines[idx].starts_with('+') {
        idx += 1;
    }
    let mut board_map: BoardMap = HashMap::new();
    for row in 0..9 {
        if idx >= lines.len() {
            break;
        }
        let row_line = &lines[idx];
        idx += 1;
        let segments: Vec<&str> = row_line.split('|').collect();
        let mut file_index = 0u8;
        for seg in segments.iter().skip(1).take(9) {
            file_index += 1;
            let token = seg.trim();
            if token.is_empty() || token == "・" || token == "　" {
                continue;
            }
            let mut chars = token.chars();
            let mut color = '+';
            let mut piece_text = token.to_string();
            if let Some(prefix) = chars.next() {
                if prefix == 'v' || prefix == '^' {
                    color = '-';
                    piece_text = chars.collect();
                }
            }
            let piece_code = match piece_text.as_str() {
                "歩" => "FU",
                "香" => "KY",
                "桂" => "KE",
                "銀" => "GI",
                "金" => "KI",
                "角" => "KA",
                "飛" => "HI",
                "玉" | "王" => "OU",
                "と" => "TO",
                "杏" => "NY",
                "圭" => "NK",
                "全" => "NG",
                "馬" => "UM",
                "龍" | "竜" => "RY",
                _ => continue,
            };
            let file = 10 - file_index;
            let rank = (row + 1) as u8;
            board_map.insert((file, rank), (color, piece_code.to_string()));
        }
    }
    if idx < lines.len() && lines[idx].starts_with('+') {
        idx += 1;
    }
    Ok((idx, board_map))
}

fn parse_kif_destination(text: &str, last_to: Option<Square>) -> Result<(Square, usize), KifError> {
    let mut chars = text.chars();
    let first = chars.next().ok_or_else(|| KifError::InvalidMove(text.to_string()))?;
    if first == '同' {
        let sq = last_to.ok_or_else(|| KifError::InvalidMove(text.to_string()))?;
        return Ok((sq, first.len_utf8()));
    }
    let file_digit = if let Some(idx) = WIDE_DIGITS.iter().position(|ch| *ch == first) {
        (idx + 1) as u8
    } else if first.is_ascii_digit() {
        first.to_digit(10).ok_or_else(|| KifError::InvalidMove(text.to_string()))? as u8
    } else {
        return Err(KifError::InvalidMove(text.to_string()));
    };
    let second = chars.next().ok_or_else(|| KifError::InvalidMove(text.to_string()))?;
    let rank_idx = KANJI_RANKS
        .iter()
        .position(|ch| *ch == second)
        .ok_or_else(|| KifError::InvalidMove(text.to_string()))?;
    let rank_digit = (rank_idx + 1) as u8;
    let file_char = char::from(b'0' + file_digit);
    let rank_char = char::from(b'a' + (rank_digit - 1));
    let sq = Square::from_usi(&format!("{file_char}{rank_char}"))
        .ok_or_else(|| KifError::InvalidMove(text.to_string()))?;
    Ok((sq, first.len_utf8() + second.len_utf8()))
}

fn parse_kif_move(
    _pos: &Position,
    line: &str,
    last_to: Option<Square>,
) -> Result<(Move16, Square), KifError> {
    let normalized = normalize_kif_line(line);
    let mut idx = 0usize;
    while let Some(ch) = normalized[idx..].chars().next() {
        if ch.is_whitespace() {
            idx += ch.len_utf8();
        } else {
            break;
        }
    }
    while let Some(ch) = normalized[idx..].chars().next() {
        if ch.is_ascii_digit() {
            idx += ch.len_utf8();
        } else {
            break;
        }
    }
    while let Some(ch) = normalized[idx..].chars().next() {
        if ch.is_whitespace() {
            idx += ch.len_utf8();
        } else {
            break;
        }
    }
    let dest_part = &normalized[idx..];
    let (to_sq, consumed) = parse_kif_destination(dest_part, last_to)?;
    idx += consumed;
    while let Some(ch) = normalized[idx..].chars().next() {
        if ch.is_whitespace() {
            idx += ch.len_utf8();
        } else {
            break;
        }
    }

    let mut iter = normalized[idx..].chars();
    let piece_char = iter.next().ok_or_else(|| KifError::InvalidMove(line.to_string()))?;
    let piece_code = match piece_char {
        '歩' => "P",
        '香' => "L",
        '桂' => "N",
        '銀' => "S",
        '金' => "G",
        '角' => "B",
        '飛' => "R",
        '玉' | '王' => "K",
        'と' => "+P",
        '杏' => "+L",
        '圭' => "+N",
        '全' => "+S",
        '馬' => "+B",
        '龍' | '竜' => "+R",
        _ => return Err(KifError::InvalidMove(line.to_string())),
    };
    idx += piece_char.len_utf8();
    let mut promote = false;
    if let Some(ch) = normalized[idx..].chars().next() {
        if ch == '成' {
            promote = true;
            idx += ch.len_utf8();
        }
    }
    while let Some(ch) = normalized[idx..].chars().next() {
        if ch.is_whitespace() {
            idx += ch.len_utf8();
        } else {
            break;
        }
    }

    if normalized[idx..].starts_with("打") {
        let usi = format!("{piece_code}*{to_sq}");
        let mv16 = Move16::from_usi(&usi).ok_or_else(|| KifError::InvalidMove(line.to_string()))?;
        return Ok((mv16, to_sq));
    }

    if let Some(open_idx) = normalized[idx..].find('(') {
        let start = idx + open_idx + 1;
        let end = normalized[start..].find(')').map(|v| start + v);
        let end = end.ok_or_else(|| KifError::InvalidMove(line.to_string()))?;
        let from_text = &normalized[start..end];
        if from_text.len() == 2 && from_text.chars().all(|ch| ch.is_ascii_digit()) {
            let file_digit = from_text
                .chars()
                .next()
                .and_then(|ch| ch.to_digit(10))
                .ok_or_else(|| KifError::InvalidMove(line.to_string()))?
                as u8;
            let rank_digit = from_text
                .chars()
                .nth(1)
                .and_then(|ch| ch.to_digit(10))
                .ok_or_else(|| KifError::InvalidMove(line.to_string()))?
                as u8;
            let file_char = char::from(b'0' + file_digit);
            let rank_char = char::from(b'a' + (rank_digit - 1));
            let from_sq = Square::from_usi(&format!("{file_char}{rank_char}"))
                .ok_or_else(|| KifError::InvalidMove(line.to_string()))?;
            let mut usi = format!("{from_sq}{to_sq}");
            if promote {
                usi.push('+');
            }
            let mv16 =
                Move16::from_usi(&usi).ok_or_else(|| KifError::InvalidMove(line.to_string()))?;
            return Ok((mv16, to_sq));
        }
    }

    Err(KifError::InvalidMove(line.to_string()))
}

fn result_from_kif_name(name: &str, side_to_move: Color) -> GameResult {
    let is_black_turn = side_to_move == Color::BLACK;
    match name {
        "投了" | "詰み" | "詰" => {
            if is_black_turn {
                GameResult::WhiteWin
            } else {
                GameResult::BlackWin
            }
        }
        "切れ負け" => {
            if is_black_turn {
                GameResult::WhiteWinByTimeout
            } else {
                GameResult::BlackWinByTimeout
            }
        }
        "反則勝ち" => {
            if is_black_turn {
                GameResult::BlackWinByIllegalMove
            } else {
                GameResult::WhiteWinByIllegalMove
            }
        }
        "反則負け" => {
            if is_black_turn {
                GameResult::WhiteWinByIllegalMove
            } else {
                GameResult::BlackWinByIllegalMove
            }
        }
        "入玉宣言" | "入玉勝ち" => {
            if is_black_turn {
                GameResult::BlackWinByDeclaration
            } else {
                GameResult::WhiteWinByDeclaration
            }
        }
        "不戦勝" => {
            if is_black_turn {
                GameResult::BlackWinByForfeit
            } else {
                GameResult::WhiteWinByForfeit
            }
        }
        "不戦敗" => {
            if is_black_turn {
                GameResult::WhiteWinByForfeit
            } else {
                GameResult::BlackWinByForfeit
            }
        }
        "千日手" => GameResult::DrawByRepetition,
        "持将棋" => GameResult::DrawByMaxPlies,
        "中断" => GameResult::Paused,
        _ => GameResult::Paused,
    }
}

fn parse_kif_summary_result(line: &str) -> Option<GameResult> {
    let trimmed = line.trim();
    if !trimmed.starts_with("まで") {
        return None;
    }
    if trimmed.contains("千日手") {
        return Some(GameResult::DrawByRepetition);
    }
    if trimmed.contains("持将棋") {
        return Some(GameResult::DrawByMaxPlies);
    }
    if trimmed.contains("中断") {
        return Some(GameResult::Paused);
    }
    if trimmed.contains("入玉宣言") || trimmed.contains("入玉勝ち") {
        if trimmed.contains("先手") {
            return Some(GameResult::BlackWinByDeclaration);
        }
        if trimmed.contains("後手") {
            return Some(GameResult::WhiteWinByDeclaration);
        }
        return None;
    }
    if trimmed.contains("反則勝ち") {
        if trimmed.contains("先手") {
            return Some(GameResult::BlackWinByIllegalMove);
        }
        if trimmed.contains("後手") {
            return Some(GameResult::WhiteWinByIllegalMove);
        }
    }
    if trimmed.contains("反則負け") {
        if trimmed.contains("先手") {
            return Some(GameResult::WhiteWinByIllegalMove);
        }
        if trimmed.contains("後手") {
            return Some(GameResult::BlackWinByIllegalMove);
        }
    }
    if trimmed.contains("勝ち") {
        if trimmed.contains("先手") {
            return Some(GameResult::BlackWin);
        }
        if trimmed.contains("後手") {
            return Some(GameResult::WhiteWin);
        }
    }
    None
}

fn format_fullwidth_digit(value: u8) -> char {
    WIDE_DIGITS[(value - 1) as usize]
}

fn format_kanji_rank(value: u8) -> char {
    KANJI_RANKS[(value - 1) as usize]
}

fn piece_type_to_kif(piece_type: PieceType) -> &'static str {
    match piece_type {
        PieceType::PAWN => "歩",
        PieceType::LANCE => "香",
        PieceType::KNIGHT => "桂",
        PieceType::SILVER => "銀",
        PieceType::GOLD => "金",
        PieceType::BISHOP => "角",
        PieceType::ROOK => "飛",
        PieceType::KING => "玉",
        PieceType::PRO_PAWN => "と",
        PieceType::PRO_LANCE => "杏",
        PieceType::PRO_KNIGHT => "圭",
        PieceType::PRO_SILVER => "全",
        PieceType::HORSE => "馬",
        PieceType::DRAGON => "龍",
        _ => "玉",
    }
}

fn move_to_kif_line(
    pos: &Position,
    mv: Move,
    move_no: usize,
    last_to: Option<Square>,
) -> Result<(String, Square), KifError> {
    let to_sq = mv.to_sq();
    let mut dest = if Some(to_sq) == last_to {
        "同".to_string()
    } else {
        let file = to_sq.file().raw() + 1;
        let rank = to_sq.rank().raw() + 1;
        format!("{}{}", format_fullwidth_digit(file as u8), format_kanji_rank(rank as u8))
    };
    let mut suffix = String::new();
    if mv.is_drop() {
        let piece_type = mv
            .dropped_piece()
            .ok_or_else(|| KifError::InvalidMove("drop move missing piece".to_string()))?;
        dest.push_str(piece_type_to_kif(piece_type));
        suffix.push('打');
    } else {
        let mover = pos.moved_piece_after(mv).piece_type();
        if mv.is_promote() {
            let base = mover.demote();
            dest.push_str(piece_type_to_kif(base));
            suffix.push('成');
        } else {
            dest.push_str(piece_type_to_kif(mover));
        }
        let from = mv.from_sq();
        let file = from.file().raw() + 1;
        let rank = from.rank().raw() + 1;
        suffix.push_str(&format!("({}{})", file, rank));
    }
    let line = format!("{:>4} {}{}", move_no, dest, suffix);
    Ok((line, to_sq))
}

fn format_kif_result(result: GameResult, side_to_move: Color, ply: usize) -> (String, String) {
    let is_black_turn = side_to_move == Color::BLACK;
    let (move_text, reason) = match result {
        GameResult::BlackWin | GameResult::WhiteWin => ("投了", "勝ち"),
        GameResult::DrawByRepetition => ("千日手", "千日手"),
        GameResult::DrawByMaxPlies => ("持将棋", "持将棋"),
        GameResult::BlackWinByDeclaration | GameResult::WhiteWinByDeclaration => {
            ("入玉宣言", "入玉宣言")
        }
        GameResult::BlackWinByForfeit | GameResult::WhiteWinByForfeit => ("不戦勝", "不戦勝"),
        GameResult::BlackWinByIllegalMove | GameResult::WhiteWinByIllegalMove => {
            ("反則勝ち", "反則勝ち")
        }
        GameResult::BlackWinByTimeout | GameResult::WhiteWinByTimeout => ("切れ負け", "勝ち"),
        GameResult::Error | GameResult::Invalid | GameResult::Paused => ("中断", "中断"),
    };

    let winner = if let Some(color) = result.winner_color() {
        if color == Color::BLACK {
            "先手"
        } else {
            "後手"
        }
    } else if is_black_turn {
        "後手"
    } else {
        "先手"
    };

    let last_line = format!("{:>4} {}", ply + 1, move_text);
    let reason_line =
        if reason == "千日手" || reason == "持将棋" || reason == "中断" || reason == "入玉宣言"
        {
            format!("まで{}手で{}", ply, reason)
        } else {
            format!("まで{}手で{}の{}", ply, winner, reason)
        };
    (last_line, reason_line)
}

pub fn parse_kif_str(text: &str) -> Result<Record, KifError> {
    let mut lines: Vec<String> = text
        .replace("\r\n", "\n")
        .replace('\r', "\n")
        .split('\n')
        .map(|line| line.to_string())
        .collect();
    if let Some(first) = lines.first_mut() {
        *first = first.trim_start_matches('\u{feff}').to_string();
    }

    let mut board_map: BoardMap = HashMap::new();
    let mut hand_counts: HandCounts = HashMap::new();
    ensure_hand_sides(&mut hand_counts);
    let mut initial_turn: Option<char> = None;

    let mut idx = 0usize;
    while idx < lines.len() {
        let line = lines[idx].clone();
        let stripped = line.trim();
        if stripped.is_empty() {
            idx += 1;
            continue;
        }
        if stripped.starts_with("変化：") {
            break;
        }
        if stripped.starts_with("手数") || stripped.starts_with("まで") {
            break;
        }
        if stripped.starts_with('*') {
            idx += 1;
            continue;
        }
        if is_board_header_line(&line) {
            let (next, parsed) = parse_board_block(&lines, idx)?;
            board_map = parsed;
            idx = next;
            continue;
        }
        if stripped == "先手番" {
            initial_turn = Some('+');
            idx += 1;
            continue;
        }
        if stripped == "後手番" {
            initial_turn = Some('-');
            idx += 1;
            continue;
        }
        if stripped.starts_with("先手の持駒") || stripped.starts_with("下手の持駒") {
            let parts: Vec<&str> = stripped.split(['：', ':']).collect();
            if let Some(value) = parts.get(1) {
                hand_counts.insert('+', parse_hand_pieces(value));
            }
            idx += 1;
            continue;
        }
        if stripped.starts_with("後手の持駒") || stripped.starts_with("上手の持駒") {
            let parts: Vec<&str> = stripped.split(['：', ':']).collect();
            if let Some(value) = parts.get(1) {
                hand_counts.insert('-', parse_hand_pieces(value));
            }
            idx += 1;
            continue;
        }
        if stripped.starts_with("手数") || stripped.starts_with("手数＝") {
            break;
        }
        if stripped.starts_with("手合割") || stripped.contains("：") || stripped.contains(':') {
            idx += 1;
            continue;
        }
        if stripped.starts_with(|ch: char| ch.is_ascii_digit()) {
            break;
        }
        idx += 1;
    }

    let init_position_sfen = if !board_map.is_empty() {
        let board_sfen = board_map_to_sfen(&board_map).map_err(KifError::InvalidLine)?;
        let hands_sfen = hand_counts_to_sfen(&hand_counts).map_err(KifError::InvalidLine)?;
        let turn = if initial_turn == Some('-') { "w" } else { "b" };
        format!("{board_sfen} {turn} {hands_sfen} 1")
    } else {
        let mut pos = Position::new();
        pos.set_hirate();
        pos.sfen(None)
    };

    let mut pos = Position::new();
    pos.set(&init_position_sfen)?;

    let mut moves: Vec<MoveRecord> = Vec::new();
    let mut last_to: Option<Square> = None;
    let mut result: Option<GameResult> = None;
    let mut refresh_counter = 0usize;

    while idx < lines.len() {
        let line = lines[idx].trim();
        idx += 1;
        if line.is_empty() {
            continue;
        }
        if line.starts_with("変化：") {
            break;
        }
        if line.starts_with("まで") {
            if result.is_none() {
                result = parse_kif_summary_result(line);
            }
            break;
        }
        if line.starts_with('*') {
            continue;
        }
        if line.starts_with("**評価値=") {
            if let Some(last) = moves.last_mut() {
                if let Ok(value) = line.trim_start_matches("**評価値=").parse::<i32>() {
                    *last = MoveRecord::new(last.mv(), Some(value));
                }
            }
            continue;
        }
        if line.starts_with("手数") && line.contains("指手") {
            continue;
        }
        if line.chars().next().map_or(false, |ch| ch.is_ascii_digit()) || line.contains("手数") {
            match parse_kif_move(&pos, line, last_to) {
                Ok((mv16, to_sq)) => {
                    let mv = pos.move_from_move16(mv16);
                    if !pos.is_legal(mv) {
                        return Err(KifError::IllegalMove { index: moves.len() });
                    }
                    pos.do_move(mv);
                    moves.push(MoveRecord::new(mv, None));
                    last_to = Some(to_sq);
                    refresh_position_if_needed(&mut pos, &mut refresh_counter)?;
                    continue;
                }
                Err(_) => {
                    let normalized = normalize_kif_line(line);
                    let parts: Vec<&str> = normalized.split_whitespace().collect();
                    let name = parts.last().copied().unwrap_or("");
                    if !name.is_empty() {
                        result = Some(result_from_kif_name(name, pos.side_to_move()));
                        break;
                    }
                    return Err(KifError::InvalidMove(line.to_string()));
                }
            }
        }
        let normalized = normalize_kif_line(line);
        let name = normalized.split_whitespace().next().unwrap_or("");
        if !name.is_empty() {
            result = Some(result_from_kif_name(name, pos.side_to_move()));
            break;
        }
        return Err(KifError::InvalidLine(line.to_string()));
    }

    let result = result.ok_or(KifError::MissingResult)?;
    let record_result = RecordResult::new(result, None, Some(moves.len()));
    Record::new(init_position_sfen, moves, record_result)
        .map_err(|e| KifError::InvalidLine(e.to_string()))
}

pub fn export_kif(record: &Record) -> Result<String, KifError> {
    let mut pos = Position::new();
    pos.set(record.init_position_sfen())?;

    let mut lines: Vec<String> = Vec::new();
    lines.push("手合割：平手".to_string());

    let startpos = {
        let mut start = Position::new();
        start.set_hirate();
        start.sfen(None)
    };
    if record.init_position_sfen() != startpos {
        lines.extend(render_bod(&pos));
    }

    lines.push("手数----指手---------消費時間--".to_string());

    let mut last_to: Option<Square> = None;
    let mut refresh_counter = 0usize;
    for (index, mv_record) in record.moves().iter().enumerate() {
        let mv = mv_record.mv();
        if !pos.is_legal(mv) {
            return Err(KifError::IllegalMove { index });
        }
        let (line, to_sq) = move_to_kif_line(&pos, mv, index + 1, last_to)?;
        lines.push(line);
        if let Some(eval) = mv_record.eval() {
            lines.push(format!("**評価値={eval}"));
        }
        pos.do_move(mv);
        last_to = Some(to_sq);
        refresh_position_if_needed(&mut pos, &mut refresh_counter)?;
    }

    let (last_line, reason_line) =
        format_kif_result(record.result().result(), pos.side_to_move(), record.moves().len());
    lines.push(last_line);
    lines.push(reason_line);

    Ok(lines.join("\n"))
}

fn render_bod(pos: &Position) -> Vec<String> {
    let mut lines = Vec::new();
    lines.push("  ９ ８ ７ ６ ５ ４ ３ ２ １".to_string());
    lines.push("+---------------------------+".to_string());
    for rank in 1..=9u8 {
        let mut row = String::from("|");
        for file in (1..=9u8).rev() {
            let file_char = char::from(b'0' + file);
            let rank_char = char::from(b'a' + (rank - 1));
            let sq = Square::from_usi(&format!("{file_char}{rank_char}")).expect("valid square");
            let piece = pos.piece_on(sq);
            if piece == Piece::NO_PIECE {
                row.push(' ');
                row.push('・');
                continue;
            }
            if piece.color() == Color::WHITE {
                row.push('v');
                row.push_str(piece_type_to_kif(piece.piece_type()));
            } else {
                row.push(' ');
                row.push_str(piece_type_to_kif(piece.piece_type()));
            }
        }
        row.push('|');
        lines.push(row);
    }
    lines.push("+---------------------------+".to_string());

    let mut black = String::from("先手の持駒：");
    let mut white = String::from("後手の持駒：");
    black.push_str(&format_hand_text(pos.hand_of(Color::BLACK)));
    white.push_str(&format_hand_text(pos.hand_of(Color::WHITE)));
    lines.push(black);
    lines.push(white);
    lines
}

fn format_hand_text(hand: crate::types::Hand) -> String {
    let mut parts = Vec::new();
    for (piece_type, name) in [
        (PieceType::PAWN, "歩"),
        (PieceType::LANCE, "香"),
        (PieceType::KNIGHT, "桂"),
        (PieceType::SILVER, "銀"),
        (PieceType::GOLD, "金"),
        (PieceType::BISHOP, "角"),
        (PieceType::ROOK, "飛"),
    ] {
        let count = crate::types::HandPiece::from_piece_type(piece_type)
            .map(|hp| hand.count(hp))
            .unwrap_or(0);
        if count == 0 {
            continue;
        }
        if count == 1 {
            parts.push(name.to_string());
        } else {
            parts.push(format!("{name}{}", kanji_number(count as u8)));
        }
    }
    if parts.is_empty() {
        "なし".to_string()
    } else {
        parts.join("")
    }
}

fn kanji_number(value: u8) -> String {
    match value {
        1 => "一".to_string(),
        2 => "二".to_string(),
        3 => "三".to_string(),
        4 => "四".to_string(),
        5 => "五".to_string(),
        6 => "六".to_string(),
        7 => "七".to_string(),
        8 => "八".to_string(),
        9 => "九".to_string(),
        10 => "十".to_string(),
        _ => value.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::hirate_position;

    #[test]
    fn parse_kif_basic() {
        let kif = "\
手合割：平手
手数----指手---------消費時間--
 1 ７六歩(77)
 2 投了
まで1手で先手の勝ち";

        let record = parse_kif_str(kif).unwrap();
        assert_eq!(record.moves().len(), 1);
        assert_eq!(record.result().result(), GameResult::BlackWin);
    }

    #[test]
    fn export_kif_basic() {
        let pos = hirate_position();
        let mv16 = Move16::from_usi("7g7f").unwrap();
        let mv = pos.move_from_move16(mv16);
        let record = Record::new(
            pos.sfen(None),
            vec![MoveRecord::new(mv, Some(120))],
            RecordResult::new(GameResult::BlackWin, None, Some(1)),
        )
        .unwrap();

        let kif = export_kif(&record).unwrap();
        assert!(kif.contains("７六歩"));
        assert!(kif.contains("**評価値=120"));
    }
}
