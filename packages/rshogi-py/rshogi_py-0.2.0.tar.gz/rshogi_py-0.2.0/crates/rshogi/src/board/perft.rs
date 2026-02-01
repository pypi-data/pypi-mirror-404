//! Reference perft dataとperft計算ロジックを提供するモジュール。
//! YaneuraOu互換の参照値を保持しつつ、自前の合法手生成を用いた
//! perft（Performance Test）計算を行う。

use super::{
    move_list::MoveList,
    movegen::{self, NonEvasionsAll},
    position::Position,
};
use crate::types::Move;
use std::convert::TryFrom;
use std::time::{Duration, Instant};
use thiserror::Error;

const STARTPOS_SFEN: &str = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
const BENCH_OPENING_SFEN: &str =
    "lnsgkgsnl/1r7/p1ppp1bpp/1p3pp2/7P1/2P6/PP1PPPP1P/1B3S1R1/LNSGKG1NL b - 9";
const BENCH_TACTICAL_SFEN: &str =
    "l6nl/5+P1gk/2np1S3/p1p4Pp/3P2Sp1/1PPb2P1P/P5GS1/R8/LN4bKL w RGgsn5p 1";

const STARTPOS_PERFT: &[(u8, u64)] =
    &[(1, 30), (2, 900), (3, 25_470), (4, 719_731), (5, 19_861_490), (6, 547_581_517)];

const BENCH_OPENING_PERFT: &[(u8, u64)] = &[(4, 1_307_221)];

const BENCH_TACTICAL_PERFT: &[(u8, u64)] = &[(3, 4_809_015)];

const REFERENCE_POSITIONS: &[(&str, &str)] = &[
    ("startpos", STARTPOS_SFEN),
    ("bench_opening", BENCH_OPENING_SFEN),
    ("bench_tactical", BENCH_TACTICAL_SFEN),
];

const PERFT_RESULTS: &[(&str, &[(u8, u64)])] = &[
    ("startpos", STARTPOS_PERFT),
    ("bench_opening", BENCH_OPENING_PERFT),
    ("bench_tactical", BENCH_TACTICAL_PERFT),
];

const CUSTOM_POSITION_NAME: &str = "custom";

/// Status for a perft evaluation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PerftStatus {
    /// Nodes were resolved using the embedded reference table. The move
    /// generator is not enabled yet, so this acts as a guard-rail.
    Stub,
    /// Nodes were computed by traversing the move tree (future work).
    Computed,
}

/// Result of a perft query.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PerftResult {
    pub name: &'static str,
    pub depth: u8,
    pub nodes: u64,
    pub status: PerftStatus,
}

impl PerftResult {
    #[must_use]
    pub const fn is_stub(&self) -> bool {
        matches!(self.status, PerftStatus::Stub)
    }
}

/// `perft_div` で得られる初手毎のノード情報
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PerftBranch {
    pub mv: Move,
    pub nodes: u64,
}

/// perft計測時の統計情報
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PerftStats {
    pub name: &'static str,
    pub depth: u8,
    pub nodes: u64,
    pub elapsed: Duration,
    pub nps: u64,
}

/// Errors that occur when resolving reference perft data.
#[derive(Debug, Error)]
pub enum PerftError {
    #[error("perft reference not found for sfen: {sfen}")]
    UnknownPosition { sfen: String },
    #[error("perft reference not found for {name} at depth {depth}")]
    UnknownDepth { name: &'static str, depth: u8 },
    #[error("perft_div depth must be at least 1 (got {depth})")]
    InvalidDivisionDepth { depth: u8 },
}

/// Returns the canonical name associated with an SFEN if it is part of the
/// reference table.
fn name_for_sfen(sfen: &str) -> Option<&'static str> {
    REFERENCE_POSITIONS
        .iter()
        .find_map(|(name, reference_sfen)| ((*reference_sfen == sfen).then_some(*name)))
}

/// Returns the expected node count for a named position at the specified depth.
fn expected_nodes_for(name: &str, depth: u8) -> Option<u64> {
    PERFT_RESULTS
        .iter()
        .find(|(key, _)| *key == name)
        .and_then(|(_, entries)| entries.iter().find(|(d, _)| *d == depth).map(|(_, n)| *n))
}

/// Returns the canonical name for the supplied [`Position`], if it is present in
/// the reference set.
#[must_use]
pub fn position_name(position: &Position) -> Option<&'static str> {
    name_for_sfen(&position.sfen(None))
}

/// Execute a perft search starting from the supplied [`Position`].
/// 参照データが存在する場合はdebug assertで一致を確認する。
pub fn perft(position: &Position, depth: u8) -> Result<PerftResult, PerftError> {
    let mut working = position.clone();
    initialize_stack(&mut working);

    let mut ctx = PerftContext::new(depth);

    let nodes = compute_perft_with_context(&mut working, depth, &mut ctx);

    let name = position_name(position).unwrap_or(CUSTOM_POSITION_NAME);

    if let Some(expected) = expected_nodes_for(name, depth) {
        debug_assert!(
            expected == nodes,
            "perft mismatch for {name} depth {depth}: expected {expected}, got {nodes}"
        );
    }

    Ok(PerftResult { name, depth, nodes, status: PerftStatus::Computed })
}

/// perft実行の所要時間とNPSを計測する
pub fn perft_bench(position: &Position, depth: u8) -> Result<PerftStats, PerftError> {
    let mut working = position.clone();
    initialize_stack(&mut working);

    let mut ctx = PerftContext::new(depth);

    let start = Instant::now();
    let nodes = compute_perft_with_context(&mut working, depth, &mut ctx);
    let elapsed = start.elapsed();

    let nps = if elapsed.as_nanos() == 0 {
        nodes
    } else {
        let scaled = (nodes as u128) * 1_000_000_000u128;
        let per_sec = scaled / elapsed.as_nanos();
        u64::try_from(per_sec).unwrap_or(u64::MAX)
    };

    let name = position_name(position).unwrap_or(CUSTOM_POSITION_NAME);

    log::info!("perft {name} depth {depth}: {nodes} nodes in {:.3?} ({nps} nps)", elapsed);

    Ok(PerftStats { name, depth, nodes, elapsed, nps })
}

/// 各初手に対するノード数を返す `perft_div`
pub fn perft_div(position: &Position, depth: u8) -> Result<Vec<PerftBranch>, PerftError> {
    if depth == 0 {
        return Err(PerftError::InvalidDivisionDepth { depth });
    }

    let mut working = position.clone();
    initialize_stack(&mut working);

    let mut moves = MoveList::new();
    movegen::generate_moves::<NonEvasionsAll>(&working, &mut moves);

    let mut branches = Vec::with_capacity(moves.len());
    let mut ctx = PerftContext::new(depth - 1);

    for &mv in moves.iter() {
        if !working.is_legal(mv) {
            continue;
        }
        working.do_move(mv);
        // PieceList整合性チェック（デバッグビルドのみ）
        #[cfg(debug_assertions)]
        working.assert_piece_list_consistency();

        let nodes = compute_perft_with_context(&mut working, depth - 1, &mut ctx);
        working.undo_move(mv).expect("undo_move must succeed during perft_div");

        // undo後のPieceList整合性チェック（デバッグビルドのみ）
        #[cfg(debug_assertions)]
        working.assert_piece_list_consistency();

        branches.push(PerftBranch { mv, nodes });
    }

    Ok(branches)
}

/// Returns all reference positions as `(name, sfen)` tuples.
#[must_use]
pub const fn reference_positions() -> &'static [(&'static str, &'static str)] {
    REFERENCE_POSITIONS
}

/// Returns the known `(depth, nodes)` table for the supplied position name.
#[must_use]
pub fn reference_depths(name: &str) -> Option<&'static [(u8, u64)]> {
    PERFT_RESULTS.iter().find(|(key, _)| *key == name).map(|(_, entries)| *entries)
}

/// 再帰的に合法手を辿りノード数を数えるperft本体。
#[must_use]
pub fn compute_perft(position: &mut Position, depth: u8) -> u64 {
    let mut ctx = PerftContext::new(depth);
    compute_perft_with_context(position, depth, &mut ctx)
}

fn initialize_stack(position: &mut Position) {
    position.init_stack();
}

struct PerftContext {
    buffers: Vec<MoveList>,
}

impl PerftContext {
    fn new(max_depth: u8) -> Self {
        let count = usize::from(max_depth);
        let mut buffers = Vec::with_capacity(count);
        for _ in 0..count {
            buffers.push(MoveList::new());
        }
        Self { buffers }
    }

    fn buffers_for(&mut self, depth: u8) -> &mut [MoveList] {
        let len = usize::from(depth);
        debug_assert!(len <= self.buffers.len());
        &mut self.buffers[..len]
    }
}

fn compute_perft_with_context(position: &mut Position, depth: u8, ctx: &mut PerftContext) -> u64 {
    let buffers = ctx.buffers_for(depth);
    compute_perft_recursive(position, depth, buffers)
}

fn compute_perft_recursive(position: &mut Position, depth: u8, buffers: &mut [MoveList]) -> u64 {
    if depth == 0 {
        return 1;
    }

    let (current, rest) =
        buffers.split_last_mut().expect("buffers length must match recursion depth");

    current.clear();
    movegen::generate_moves::<NonEvasionsAll>(position, current);

    if depth == 1 {
        return current.iter().filter(|&&mv| position.is_legal(mv)).count() as u64;
    }

    let mut nodes = 0_u64;

    for &mv in current.iter() {
        if !position.is_legal(mv) {
            continue;
        }
        position.do_move(mv);
        // PieceList整合性チェック（デバッグビルドのみ）
        #[cfg(debug_assertions)]
        position.assert_piece_list_consistency();

        nodes += compute_perft_recursive(position, depth - 1, rest);
        position.undo_move(mv).expect("undo_move must succeed during perft");

        // undo後のPieceList整合性チェック（デバッグビルドのみ）
        #[cfg(debug_assertions)]
        position.assert_piece_list_consistency();
    }

    nodes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn name_lookup_succeeds() {
        let pos = crate::board::position_from_sfen(STARTPOS_SFEN).expect("parse startpos");
        assert_eq!(position_name(&pos), Some("startpos"));
    }

    #[test]
    fn expected_nodes_are_available() {
        assert_eq!(expected_nodes_for("startpos", 3), Some(25_470));
        assert_eq!(expected_nodes_for("bench_tactical", 3), Some(4_809_015));
        assert!(expected_nodes_for("startpos", 7).is_none());
    }
}
