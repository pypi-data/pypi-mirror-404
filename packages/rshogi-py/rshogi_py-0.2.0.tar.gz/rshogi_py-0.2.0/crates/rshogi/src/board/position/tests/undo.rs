use super::helpers::{apply_usi_move, move_from_usi};
use super::*;

const fn is_promoted_piece(piece: Piece) -> bool {
    matches!(
        piece.piece_type(),
        PieceType::PRO_PAWN
            | PieceType::PRO_LANCE
            | PieceType::PRO_KNIGHT
            | PieceType::PRO_SILVER
            | PieceType::HORSE
            | PieceType::DRAGON
    )
}
use crate::types::{Color, Move, PieceType, Square};

#[test]
// 通常手のapply/undoで局面が完全に往復するか検証
fn undo_normal_move() {
    let mut pos = crate::board::hirate_position();

    let initial_sfen = pos.sfen(None);
    let initial_zobrist = pos.key();
    let initial_ply = pos.game_ply();
    let initial_side = pos.side_to_move();

    let from = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_7);
    let to = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_6);
    let piece = pos.piece_on(from);
    let mv = Move::make(from, to, piece);
    pos.do_move(mv);

    assert_ne!(pos.sfen(None), initial_sfen);
    assert_ne!(pos.key(), initial_zobrist);
    assert_eq!(pos.game_ply(), initial_ply + 1);
    assert_eq!(pos.side_to_move(), initial_side.flip());

    pos.undo_move(mv).unwrap();

    assert_eq!(pos.sfen(None), initial_sfen);
    assert_eq!(pos.key(), initial_zobrist);
    assert_eq!(pos.game_ply(), initial_ply);
    assert_eq!(pos.side_to_move(), initial_side);
}

#[test]
// 駒取りを含む手のundoで持ち駒や盤面が復元されるか確認
fn undo_capture_move() {
    let mut pos = crate::board::hirate_position();

    apply_usi_move(&mut pos, "7g7f");
    apply_usi_move(&mut pos, "3c3d");
    apply_usi_move(&mut pos, "3g3f");
    apply_usi_move(&mut pos, "3d3e");

    let initial_sfen = pos.sfen(None);
    let initial_zobrist = pos.key();
    let initial_black_hand = pos.hand_of(Color::BLACK);

    let capture_from = Square::from_usi("3f").unwrap();
    let capture_to = Square::from_usi("3e").unwrap();
    let mv = Move::make(capture_from, capture_to, pos.piece_on(capture_from));
    pos.do_move(mv);

    assert_ne!(pos.hand_of(Color::BLACK), initial_black_hand);

    pos.undo_move(mv).unwrap();

    assert_eq!(pos.sfen(None), initial_sfen);
    assert_eq!(pos.key(), initial_zobrist);
    assert_eq!(pos.hand_of(Color::BLACK), initial_black_hand);
}

#[test]
// 駒打ちのundoで持ち駒と盤面が元通りになるか検証
fn undo_drop_move() {
    let sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPP1PPPP/1B5R1/LNSGKGSNL b P 1";
    let mut pos = crate::board::position_from_sfen(sfen).unwrap();

    let initial_sfen = pos.sfen(None);
    let initial_zobrist = pos.key();
    let initial_black_hand = pos.hand_of(Color::BLACK);

    let to = Square::from_file_rank(crate::types::File::FILE_5, crate::types::Rank::RANK_5);
    let mv = Move::make_drop(PieceType::PAWN, to, Color::BLACK);
    pos.do_move(mv);

    assert_ne!(pos.hand_of(Color::BLACK), initial_black_hand);
    assert_eq!(pos.piece_on(to).piece_type(), PieceType::PAWN);

    pos.undo_move(mv).unwrap();

    assert_eq!(pos.sfen(None), initial_sfen);
    assert_eq!(pos.key(), initial_zobrist);
    assert_eq!(pos.hand_of(Color::BLACK), initial_black_hand);
    assert_eq!(pos.piece_on(to), Piece::NO_PIECE);
}

#[test]
// 成りを含む手のundoで成・非成が適切に戻るか確認
fn undo_promote_move() {
    let sfen = "4k4/9/4P4/9/9/9/9/9/4K4 b - 1";
    let mut pos = crate::board::position_from_sfen(sfen).unwrap();

    let initial_sfen = pos.sfen(None);
    let initial_zobrist = pos.key();

    let from = Square::from_usi("5c").unwrap();
    let to = Square::from_usi("5b").unwrap();
    let piece = pos.piece_on(from);
    let mv = Move::make_promote(from, to, piece);
    assert!(pos.is_legal(mv));
    pos.do_move(mv);

    assert!(is_promoted_piece(pos.piece_on(to)));

    pos.undo_move(mv).unwrap();

    assert_eq!(pos.sfen(None), initial_sfen);
    assert_eq!(pos.key(), initial_zobrist);
    assert_eq!(pos.piece_on(from).piece_type(), PieceType::PAWN);
    assert!(!is_promoted_piece(pos.piece_on(from)));
}

#[test]
// 複数手を進めたあと逆順にundoして初期局面に戻れるか検証
fn undo_multiple_moves_in_reverse_order() {
    let mut pos = crate::board::hirate_position();

    let initial_sfen = pos.sfen(None);
    let initial_zobrist = pos.key();

    let from1 = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_7);
    let to1 = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_6);
    let piece1 = pos.piece_on(from1);
    let mv1 = Move::make(from1, to1, piece1);
    pos.do_move(mv1);

    let from2 = Square::from_file_rank(crate::types::File::FILE_3, crate::types::Rank::RANK_3);
    let to2 = Square::from_file_rank(crate::types::File::FILE_3, crate::types::Rank::RANK_4);
    let piece2 = pos.piece_on(from2);
    let mv2 = Move::make(from2, to2, piece2);
    pos.do_move(mv2);

    let from3 = Square::from_file_rank(crate::types::File::FILE_2, crate::types::Rank::RANK_7);
    let to3 = Square::from_file_rank(crate::types::File::FILE_2, crate::types::Rank::RANK_6);
    let piece3 = pos.piece_on(from3);
    let mv3 = Move::make(from3, to3, piece3);
    pos.do_move(mv3);

    for mv in [mv1, mv2, mv3].iter().rev() {
        pos.undo_move(*mv).unwrap();
    }

    assert_eq!(pos.sfen(None), initial_sfen);
    assert_eq!(pos.key(), initial_zobrist);
}

#[test]
// スタック不足時にStackUnderflowが返るか確認
fn undo_stack_underflow_returns_error() {
    let mut pos = crate::board::hirate_position();

    let from = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_7);
    let to = Square::from_file_rank(crate::types::File::FILE_7, crate::types::Rank::RANK_6);
    let piece = pos.piece_on(from);
    let mv = Move::make(from, to, piece);
    let result = pos.undo_move(mv);

    assert!(result.is_err());
    assert_eq!(result.unwrap_err(), MoveError::StackUnderflow);
}

#[test]
// undoでplies_from_nullなどの状態が復元されるか検証
fn undo_restores_repetition_state() {
    let mut pos = crate::board::hirate_position();

    let mv1 = move_from_usi(&pos, "7g7f");
    pos.do_move(mv1);
    let plies_after_first = pos.state_stack().current().plies_from_null;

    let mv2 = move_from_usi(&pos, "8c8d");
    pos.do_move(mv2);

    pos.undo_move(mv2).unwrap();

    assert_eq!(pos.state_stack().current().plies_from_null, plies_after_first);
}
