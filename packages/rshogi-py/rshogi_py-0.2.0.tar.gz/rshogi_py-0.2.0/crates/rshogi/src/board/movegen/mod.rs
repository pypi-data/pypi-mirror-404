//! `MoveGen` - 合法手生成

mod checks;
mod drops;
mod evasions;
mod generate;
mod pieces;
mod promotions;
mod recaptures;
mod types;

#[cfg(test)]
mod tests;

use std::marker::PhantomData;
#[cfg(feature = "generate-all-legal-moves")]
use std::sync::atomic::{AtomicBool, Ordering};

use crate::board::move_list::{ExtMove, ExtMoveList, MoveList};
use crate::board::Position;
use crate::types::{Color, Move, Square};

pub use checks::{generate_checks, generate_checks_drops_part, generate_quiet_checks};
pub use evasions::generate_evasions;
pub use generate::{generate_moves, generate_moves_to};
pub use recaptures::{generate_recaptures, generate_recaptures_all};
pub use types::{
    CapturePlusPro, CapturePlusProAll, Captures, CapturesAll, Checks, ChecksAll, Evasions,
    EvasionsAll, Legal, LegalAll, MoveGenType, NonEvasions, NonEvasionsAll, QuietChecks,
    QuietChecksAll, Quiets, QuietsAll, QuietsProMinus, QuietsProMinusAll, Recaptures,
    RecapturesAll,
};

pub(crate) trait ColorMarker {
    const COLOR: Color;
    const THEM: Color;
}

pub(crate) struct Black;
pub(crate) struct White;

impl ColorMarker for Black {
    const COLOR: Color = Color::BLACK;
    const THEM: Color = Color::WHITE;
}

impl ColorMarker for White {
    const COLOR: Color = Color::WHITE;
    const THEM: Color = Color::BLACK;
}

pub trait MoveSink {
    fn push_move(&mut self, mv: Move);
    fn retain_unordered<F>(&mut self, f: F)
    where
        F: FnMut(Move) -> bool;
}

impl MoveSink for MoveList {
    #[inline]
    fn push_move(&mut self, mv: Move) {
        self.push(mv);
    }

    #[inline]
    fn retain_unordered<F>(&mut self, f: F)
    where
        F: FnMut(Move) -> bool,
    {
        self.retain_unordered(f);
    }
}

impl MoveSink for ExtMoveList {
    #[inline]
    fn push_move(&mut self, mv: Move) {
        self.push(ExtMove::from(mv));
    }

    #[inline]
    fn retain_unordered<F>(&mut self, f: F)
    where
        F: FnMut(Move) -> bool,
    {
        self.retain_unordered(f);
    }
}

#[cfg(feature = "generate-all-legal-moves")]
static GENERATE_ALL_LEGAL_MOVES: AtomicBool = AtomicBool::new(false);

#[cfg(feature = "generate-all-legal-moves")]
pub fn set_generate_all_legal_moves(enabled: bool) {
    GENERATE_ALL_LEGAL_MOVES.store(enabled, Ordering::Relaxed);
}

#[cfg(feature = "generate-all-legal-moves")]
#[must_use]
pub fn generate_all_legal_moves_enabled() -> bool {
    GENERATE_ALL_LEGAL_MOVES.load(Ordering::Relaxed)
}

#[cfg(not(feature = "generate-all-legal-moves"))]
pub const fn set_generate_all_legal_moves(_enabled: bool) {}

#[cfg(not(feature = "generate-all-legal-moves"))]
#[must_use]
pub const fn generate_all_legal_moves_enabled() -> bool {
    false
}

/// YaneuraOuのMoveList<GenType>相当のラッパー。
pub struct MoveListGen<T: MoveGenType> {
    moves: MoveList,
    _marker: PhantomData<T>,
}

impl<T: MoveGenType + 'static> MoveListGen<T> {
    #[must_use]
    pub fn new(pos: &Position) -> Self {
        let mut moves = MoveList::new();
        debug_assert!(!T::IS_RECAPTURES, "MoveListGen::new is not for Recaptures");
        generate_moves::<T>(pos, &mut moves);
        Self { moves, _marker: PhantomData }
    }

    #[must_use]
    pub fn new_with_target(pos: &Position, target_sq: Square) -> Self {
        let mut moves = MoveList::new();
        if T::IS_RECAPTURES {
            generate_moves_to::<T>(pos, target_sq, &mut moves);
        } else {
            generate_moves::<T>(pos, &mut moves);
        }
        Self { moves, _marker: PhantomData }
    }

    pub fn iter(&self) -> impl Iterator<Item = &Move> {
        self.moves.iter()
    }

    #[must_use]
    pub const fn len(&self) -> usize {
        self.moves.len()
    }

    #[must_use]
    pub const fn size(&self) -> usize {
        self.moves.len()
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.moves.is_empty()
    }

    #[must_use]
    pub fn contains(&self, mv: Move) -> bool {
        self.moves.iter().any(|&m| m == mv)
    }

    #[must_use]
    pub fn at(&self, idx: usize) -> Move {
        debug_assert!(idx < self.moves.len(), "index out of bounds");
        self.moves.as_slice()[idx]
    }
}

impl<'a, T: MoveGenType> IntoIterator for &'a MoveListGen<T> {
    type Item = &'a Move;
    type IntoIter = std::slice::Iter<'a, Move>;

    fn into_iter(self) -> Self::IntoIter {
        self.moves.as_slice().iter()
    }
}

/// YaneuraOu互換のExtMove生成ヘルパー。
pub fn generate_moves_ext<T: MoveGenType + 'static>(pos: &Position, list: &mut ExtMoveList) {
    debug_assert!(!T::IS_RECAPTURES, "generate_moves_ext is not for Recaptures");
    generate_moves::<T>(pos, list);
}

/// YaneuraOu互換のExtMove生成ヘルパー（指定マスへの移動手）。
pub fn generate_moves_ext_to<T: MoveGenType + 'static>(
    pos: &Position,
    target_sq: Square,
    list: &mut ExtMoveList,
) {
    if T::IS_RECAPTURES {
        generate_moves_to::<T>(pos, target_sq, list);
    } else {
        generate_moves::<T>(pos, list);
    }
}
