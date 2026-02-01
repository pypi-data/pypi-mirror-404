use super::{generate_moves, NonEvasionsAll};
use crate::board::MoveList;
use crate::types::{Color, PieceType};

#[test]
fn lance_moves_forward_span() {
    let sfen = "9/9/9/9/4L4/9/9/9/9 b - 1";
    let pos = crate::board::position_from_sfen(sfen).unwrap();
    let mut moves = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut moves);

    let count = moves
        .iter()
        .filter(|&m| !m.is_drop() && pos.piece_on(m.from_sq()).piece_type() == PieceType::LANCE)
        .count();

    assert_eq!(count, 6, "香車の移動手は6手");
}

#[test]
fn lance_moves_blocked_by_ally() {
    let sfen = "9/9/9/4P4/4L4/9/9/9/9 b - 1";
    let pos = crate::board::position_from_sfen(sfen).unwrap();
    let mut moves = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut moves);

    let count = moves
        .iter()
        .filter(|&m| !m.is_drop() && pos.piece_on(m.from_sq()).piece_type() == PieceType::LANCE)
        .count();

    assert_eq!(count, 0, "味方の駒で遮られている場合は移動できない");
}

#[test]
fn bishop_moves_cover_diagonals() {
    let sfen = "9/9/9/9/4B4/9/9/9/9 b - 1";
    let pos = crate::board::position_from_sfen(sfen).unwrap();
    let mut moves = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut moves);

    let count = moves
        .iter()
        .filter(|&m| !m.is_drop() && pos.piece_on(m.from_sq()).piece_type() == PieceType::BISHOP)
        .count();

    assert_eq!(count, 22, "角の移動手は22手");
}

#[test]
fn rook_moves_cover_ranks_files() {
    let sfen = "9/9/9/9/4R4/9/9/9/9 b - 1";
    let pos = crate::board::position_from_sfen(sfen).unwrap();
    let mut moves = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut moves);

    let count = moves
        .iter()
        .filter(|&m| !m.is_drop() && pos.piece_on(m.from_sq()).piece_type() == PieceType::ROOK)
        .count();

    assert_eq!(count, 19, "飛車の移動手は19手");
}

#[test]
fn slider_moves_startpos_counts() {
    let pos = crate::board::hirate_position();
    let mut moves = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut moves);

    let lance_moves = moves
        .iter()
        .filter(|&m| {
            !m.is_drop()
                && pos.piece_on(m.from_sq()).piece_type() == PieceType::LANCE
                && pos.piece_on(m.from_sq()).color() == Color::BLACK
        })
        .count();

    let bishop_moves = moves
        .iter()
        .filter(|&m| {
            !m.is_drop()
                && pos.piece_on(m.from_sq()).piece_type() == PieceType::BISHOP
                && pos.piece_on(m.from_sq()).color() == Color::BLACK
        })
        .count();

    let rook_moves = moves
        .iter()
        .filter(|&m| {
            !m.is_drop()
                && pos.piece_on(m.from_sq()).piece_type() == PieceType::ROOK
                && pos.piece_on(m.from_sq()).color() == Color::BLACK
        })
        .count();

    assert_eq!(lance_moves, 2, "先手の香車はそれぞれ1手ずつ");
    assert_eq!(bishop_moves, 0, "角は初期配置では歩で遮られる");
    assert_eq!(rook_moves, 6, "先手の飛車は横方向に6手");
}
