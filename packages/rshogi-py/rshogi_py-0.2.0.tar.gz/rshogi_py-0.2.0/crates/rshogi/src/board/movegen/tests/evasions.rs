use crate::board::{move_list::MoveList, movegen};
use crate::types::{Piece, PieceType};
use std::collections::BTreeSet;

const SFEN_ROOK_CHECK: &str =
    "l4S2l/4g1gs1/5p1p1/pr2N1pkp/4Gn3/PP3PPPP/2GPP4/1K2r4/L4+s2L b BS2N5Pb 2";
const SFEN_ROOK_ADVANCES: &str =
    "l4S2l/4g1gs1/5p1p1/p3N1pkp/4Gn3/Pr3PPPP/2GPP4/1K7/L3r+s2L b BS2N5Pbp 2";
const SFEN_BISHOP_DROP: &str =
    "l4S2l/4g1gs1/5p1p1/pr2N1pkp/4Gn3/PP3PPPP/2GPP4/1K7/L1b1r+s2L b BS2N5P 2";

#[test]
fn evasion_moves_clear_check_and_roundtrip() {
    // 王手回避の apply/undo が整合性を保つことを検証
    let mut pos = crate::board::position_from_sfen(SFEN_ROOK_CHECK).expect("parse SFEN");

    let checkers_before = pos.checkers();
    assert!(!checkers_before.is_empty(), "Initial scenario must start in check to test evasions");

    let mut list = MoveList::new();
    movegen::generate_evasions(&pos, &mut list);
    assert!(!list.is_empty(), "Evasion generator should produce at least one move");

    let zobrist_before = pos.key();
    let depth_before = pos.state_stack().depth();

    for &mv in list.iter() {
        pos.do_move(mv);
        assert!(
            pos.checkers().is_empty(),
            "After applying an evasion move, the side to move must not be in check"
        );
        assert_eq!(
            pos.state_stack().depth(),
            depth_before + 1,
            "StateStack depth should increase after do_move"
        );

        pos.undo_move(mv).expect("undo evasion move");
        assert_eq!(
            pos.state_stack().depth(),
            depth_before,
            "StateStack depth should return to baseline after undo_move"
        );
        assert_eq!(pos.key(), zobrist_before, "Zobrist key must round-trip");
        assert_eq!(pos.checkers(), checkers_before, "Undo should restore original checkers");
    }
}

#[test]
fn rook_line_check_generates_expected_evasions() {
    let pos = crate::board::position_from_sfen(SFEN_ROOK_CHECK).expect("parse SFEN");

    let mut list = MoveList::new();
    movegen::generate_evasions(&pos, &mut list);

    assert!(!list.is_empty(), "王手回避手が1手以上生成されるべき");

    let actual: BTreeSet<String> = list.iter().map(|mv| mv.to_usi()).collect();
    let expected: BTreeSet<String> = [
        "8h7i", "8h8g", "8h8i", "8h9g", "N*6h", "S*6h", "B*6h", "7g7h", "P*7h", "N*7h", "S*7h",
        "B*7h",
    ]
    .into_iter()
    .map(String::from)
    .collect();

    assert_eq!(actual, expected, "既知の王手回避手集合と一致するべき");
}

#[test]
fn rook_line_evasions_comprehensive() {
    // 飛車の王手回避：駒取り、合駒、玉移動などすべての種類の回避手を検証
    let pos = crate::board::position_from_sfen(SFEN_ROOK_ADVANCES).expect("parse SFEN");

    let mut list = MoveList::new();
    movegen::generate_evasions(&pos, &mut list);

    assert!(!list.is_empty(), "王手回避手が1手以上生成されるべき");

    // 王手駒を取る手が含まれていることを確認
    let has_capture =
        list.iter().any(|mv| !mv.is_drop() && pos.piece_on(mv.to_sq()) != Piece::NO_PIECE);
    assert!(has_capture, "王手をかけている駒を取る回避手が含まれているべき");

    // 合駒となる駒打ちが含まれていることを確認
    assert!(list.iter().any(|mv| mv.is_drop()), "合駒となる駒打ちが生成されるべき");

    // 玉の移動や駒移動による回避も含まれていることを確認
    assert!(list.iter().any(|mv| !mv.is_drop()), "玉の移動や駒移動による回避も含まれるべき");
}

#[test]
fn double_check_only_king_moves() {
    let pos = crate::board::position_from_sfen(SFEN_BISHOP_DROP).expect("parse SFEN");

    let mut list = MoveList::new();
    movegen::generate_evasions(&pos, &mut list);

    assert!(!list.is_empty(), "両王手でも最低1手は生成されるべき");

    for mv in list.iter() {
        assert!(!mv.is_drop(), "両王手下では打ち駒による回避は発生しない");
        assert_eq!(
            pos.piece_on(mv.from_sq()).piece_type(),
            PieceType::KING,
            "両王手下では玉の移動のみが許容されるべき"
        );
    }
}
