//! 一手詰め判定ヘルパー。
//!
//! YaneuraOu互換の1手詰め判定を提供する。

pub mod table;
pub mod yaneuraou;

use crate::board::movegen::{generate_checks, generate_moves, Evasions};
use crate::board::{MoveList, Position};
use crate::types::{Move, RepetitionState};

/// `solve_mate_in_three` の探索手順を要約して出力する。
#[must_use]
#[allow(clippy::cognitive_complexity, clippy::too_many_lines)]
pub fn debug_solve_mate_in_three(pos: &Position) -> String {
    use std::fmt::Write;

    const MAX_M1: usize = 8;
    const MAX_M2: usize = 8;

    let mut out = String::new();

    let root_ply = usize::from(pos.game_ply());
    let mut checks = MoveList::new();
    generate_checks(pos, &mut checks);
    let _ = writeln!(out, "mate3: checks={}", checks.len());

    let mut m1_count = 0usize;
    for m1 in checks.iter() {
        if !pos.is_legal(*m1) {
            continue;
        }
        m1_count += 1;
        if m1_count > MAX_M1 {
            let _ = writeln!(out, "mate3: m1 truncated");
            break;
        }

        let mut p1 = pos.clone();
        p1.init_stack();
        p1.do_move(*m1);

        let ply_from_root = usize::from(p1.game_ply()).saturating_sub(root_ply);
        let rep = p1.get_repetition_state_with_ply(ply_from_root);
        if rep != RepetitionState::None {
            let _ = writeln!(out, "m1 {m1:?}: repetition={rep:?}");
            let _ = writeln!(
                out,
                "m1 {m1:?}: repetition treated as mate={}",
                rep == RepetitionState::Lose
            );
            continue;
        }

        let mut evasions = MoveList::new();
        generate_moves::<Evasions>(&p1, &mut evasions);
        let mut legal_evasions = Vec::new();
        for m2 in evasions.iter() {
            if p1.is_legal(*m2) {
                legal_evasions.push(*m2);
            }
        }

        let _ = writeln!(out, "m1 {m1:?} usi={} : evasions={}", m1.to_usi(), legal_evasions.len());
        if legal_evasions.is_empty() {
            let _ = writeln!(out, "m1 {m1:?}: immediate mate");
            continue;
        }

        let mut m2_count = 0usize;
        let mut all_mate1 = true;
        for m2 in legal_evasions {
            m2_count += 1;
            if m2_count > MAX_M2 {
                let _ = writeln!(out, "m1 {m1:?}: m2 truncated");
                break;
            }
            let mut p2 = p1.clone();
            p2.init_stack();
            p2.do_move(m2);
            if solve_mate_in_one(&p2).is_none() {
                all_mate1 = false;
                let sfen = p2.sfen(None);
                let table = table::solve_mate_in_one_table(&p2);
                let table_usi = table.map(Move::to_usi);
                let _ = writeln!(
                    out,
                    "  m2 {m2:?} usi={}: no mate1 table={table:?} table_usi={table_usi:?} sfen={sfen}",
                    m2.to_usi()
                );
                break;
            }
            let _ = writeln!(out, "  m2 {m2:?} usi={}: mate1 ok", m2.to_usi());
        }

        if all_mate1 {
            let _ = writeln!(out, "m1 {m1:?}: all mate1 ok");
        }
    }

    out
}

/// 現局面で先手側が一手で詰ませられる指し手を探索する。
/// 一手詰め判定。
#[must_use]
pub fn solve_mate_in_one(pos: &Position) -> Option<Move> {
    let mv = yaneuraou::mate_1ply(pos);
    #[cfg(feature = "mate1ply-full")]
    if mv.is_none() {
        return yaneuraou::mate_1ply_extension(pos);
    }
    mv
}

/// テーブル駆動版の一手詰め判定（比較用）。
#[must_use]
pub fn solve_mate_in_one_table(pos: &Position) -> Option<Move> {
    table::solve_mate_in_one_table(pos)
}

/// テーブル駆動版の3手詰め判定（比較用）。
#[must_use]
pub fn solve_mate_in_three_table(pos: &Position) -> Option<(Move, Move, Move)> {
    table::solve_mate_in_three_table(pos)
}

/// `solve_mate_in_three_table` の探索手順を要約して出力する。
#[must_use]
pub fn debug_solve_mate_in_three_table(pos: &Position) -> String {
    table::debug_solve_mate_in_three_table(pos)
}

/// Solves for a mate-in-3 from the current position.
#[must_use]
pub fn solve_mate_in_three(pos: &Position) -> Option<(Move, Move, Move)> {
    let mut local_pos = pos.clone();
    local_pos.init_stack();

    let root_ply = usize::from(pos.game_ply());
    let mut checks = MoveList::new();
    generate_checks(pos, &mut checks);

    if checks.is_empty() {
        return None;
    }

    for m1 in checks.iter() {
        if !pos.is_legal(*m1) {
            continue;
        }

        local_pos.do_move(*m1);

        let ply_from_root = usize::from(local_pos.game_ply()).saturating_sub(root_ply);
        let rep = local_pos.get_repetition_state_with_ply(ply_from_root);
        if rep != RepetitionState::None {
            let _ = local_pos.undo_move(*m1);
            if rep == RepetitionState::Lose {
                return Some((*m1, crate::types::MOVE_NONE, crate::types::MOVE_NONE));
            }
            continue;
        }

        let mut evasions = MoveList::new();
        if local_pos.checkers().is_empty() {
            let _ = local_pos.undo_move(*m1);
            continue;
        }

        generate_moves::<Evasions>(&local_pos, &mut evasions);

        let legal_evasions: Vec<_> =
            evasions.iter().copied().filter(|mv| local_pos.is_legal(*mv)).collect();

        if legal_evasions.is_empty() {
            let _ = local_pos.undo_move(*m1);
            return Some((*m1, crate::types::MOVE_NONE, crate::types::MOVE_NONE));
        }

        let mut all_evasions_mated = true;
        let mut pv_line = None;

        for m2 in &legal_evasions {
            if !local_pos.is_legal(*m2) {
                continue;
            }
            local_pos.do_move(*m2);
            if !local_pos.checkers().is_empty() {
                all_evasions_mated = false;
                let _ = local_pos.undo_move(*m2);
                break;
            }

            if let Some(m3) = solve_mate_in_one(&local_pos) {
                pv_line = Some((*m1, *m2, m3));
            } else {
                all_evasions_mated = false;
                let _ = local_pos.undo_move(*m2);
                break;
            }

            let _ = local_pos.undo_move(*m2);
        }

        let _ = local_pos.undo_move(*m1);

        if all_evasions_mated {
            return pv_line;
        }
    }

    None
}
