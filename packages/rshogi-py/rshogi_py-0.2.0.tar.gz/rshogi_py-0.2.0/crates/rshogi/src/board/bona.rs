//! BonaPiece関連の定義（YaneuraOu互換）

use crate::types::{Color, Piece, PieceType, Square};

/// KPP/KPPT評価で使うBonaPiece番号
pub type BonaPiece = i32;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ExtBonaPiece {
    pub fb: BonaPiece,
    pub fw: BonaPiece,
}

const BONA_PIECE_ZERO: BonaPiece = 0;

const F_HAND_PAWN: BonaPiece = BONA_PIECE_ZERO + 1;
const E_HAND_PAWN: BonaPiece = 20;
const F_HAND_LANCE: BonaPiece = 39;
const E_HAND_LANCE: BonaPiece = 44;
const F_HAND_KNIGHT: BonaPiece = 49;
const E_HAND_KNIGHT: BonaPiece = 54;
const F_HAND_SILVER: BonaPiece = 59;
const E_HAND_SILVER: BonaPiece = 64;
const F_HAND_GOLD: BonaPiece = 69;
const E_HAND_GOLD: BonaPiece = 74;
const F_HAND_BISHOP: BonaPiece = 79;
const E_HAND_BISHOP: BonaPiece = 82;
const F_HAND_ROOK: BonaPiece = 85;
const E_HAND_ROOK: BonaPiece = 88;
pub const FE_HAND_END: BonaPiece = 90;

const SQUARE_COUNT: BonaPiece = 81;

const F_PAWN: BonaPiece = FE_HAND_END;
const E_PAWN: BonaPiece = F_PAWN + SQUARE_COUNT;
const F_LANCE: BonaPiece = E_PAWN + SQUARE_COUNT;
const E_LANCE: BonaPiece = F_LANCE + SQUARE_COUNT;
const F_KNIGHT: BonaPiece = E_LANCE + SQUARE_COUNT;
const E_KNIGHT: BonaPiece = F_KNIGHT + SQUARE_COUNT;
const F_SILVER: BonaPiece = E_KNIGHT + SQUARE_COUNT;
const E_SILVER: BonaPiece = F_SILVER + SQUARE_COUNT;
const F_GOLD: BonaPiece = E_SILVER + SQUARE_COUNT;
const E_GOLD: BonaPiece = F_GOLD + SQUARE_COUNT;
const F_BISHOP: BonaPiece = E_GOLD + SQUARE_COUNT;
const E_BISHOP: BonaPiece = F_BISHOP + SQUARE_COUNT;
const F_HORSE: BonaPiece = E_BISHOP + SQUARE_COUNT;
const E_HORSE: BonaPiece = F_HORSE + SQUARE_COUNT;
const F_ROOK: BonaPiece = E_HORSE + SQUARE_COUNT;
const E_ROOK: BonaPiece = F_ROOK + SQUARE_COUNT;
const F_DRAGON: BonaPiece = E_ROOK + SQUARE_COUNT;
const E_DRAGON: BonaPiece = F_DRAGON + SQUARE_COUNT;
pub const F_KING: BonaPiece = E_DRAGON + SQUARE_COUNT;
const E_KING: BonaPiece = F_KING + SQUARE_COUNT;
pub const FE_END: usize = 1548;
const _: [(); FE_END] = [(); F_KING as usize];

const fn ext(fb: BonaPiece, fw: BonaPiece) -> ExtBonaPiece {
    ExtBonaPiece { fb, fw }
}

pub const KPP_BOARD_INDEX: [ExtBonaPiece; Piece::PIECE_NB] = [
    ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // NO_PIECE
    ext(F_PAWN, E_PAWN),                   // B_PAWN
    ext(F_LANCE, E_LANCE),                 // B_LANCE
    ext(F_KNIGHT, E_KNIGHT),               // B_KNIGHT
    ext(F_SILVER, E_SILVER),               // B_SILVER
    ext(F_BISHOP, E_BISHOP),               // B_BISHOP
    ext(F_ROOK, E_ROOK),                   // B_ROOK
    ext(F_GOLD, E_GOLD),                   // B_GOLD
    ext(F_KING, E_KING),                   // B_KING
    ext(F_GOLD, E_GOLD),                   // B_PRO_PAWN
    ext(F_GOLD, E_GOLD),                   // B_PRO_LANCE
    ext(F_GOLD, E_GOLD),                   // B_PRO_KNIGHT
    ext(F_GOLD, E_GOLD),                   // B_PRO_SILVER
    ext(F_HORSE, E_HORSE),                 // B_HORSE
    ext(F_DRAGON, E_DRAGON),               // B_DRAGON
    ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // B_GOLDS (unused)
    ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // sentinel for index 16
    ext(E_PAWN, F_PAWN),                   // W_PAWN
    ext(E_LANCE, F_LANCE),                 // W_LANCE
    ext(E_KNIGHT, F_KNIGHT),               // W_KNIGHT
    ext(E_SILVER, F_SILVER),               // W_SILVER
    ext(E_BISHOP, F_BISHOP),               // W_BISHOP
    ext(E_ROOK, F_ROOK),                   // W_ROOK
    ext(E_GOLD, F_GOLD),                   // W_GOLD
    ext(E_KING, F_KING),                   // W_KING
    ext(E_GOLD, F_GOLD),                   // W_PRO_PAWN
    ext(E_GOLD, F_GOLD),                   // W_PRO_LANCE
    ext(E_GOLD, F_GOLD),                   // W_PRO_KNIGHT
    ext(E_GOLD, F_GOLD),                   // W_PRO_SILVER
    ext(E_HORSE, F_HORSE),                 // W_HORSE
    ext(E_DRAGON, F_DRAGON),               // W_DRAGON
    ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // W_GOLDS (unused)
];

const fn hand_ext(fb: BonaPiece, fw: BonaPiece) -> ExtBonaPiece {
    ExtBonaPiece { fb, fw }
}

pub const KPP_HAND_INDEX: [[ExtBonaPiece; PieceType::PIECE_TYPE_NB]; Color::COLOR_NB] = [
    [
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // NO_PIECE_TYPE
        hand_ext(F_HAND_PAWN, E_HAND_PAWN),
        hand_ext(F_HAND_LANCE, E_HAND_LANCE),
        hand_ext(F_HAND_KNIGHT, E_HAND_KNIGHT),
        hand_ext(F_HAND_SILVER, E_HAND_SILVER),
        hand_ext(F_HAND_BISHOP, E_HAND_BISHOP),
        hand_ext(F_HAND_ROOK, E_HAND_ROOK),
        hand_ext(F_HAND_GOLD, E_HAND_GOLD),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO), // KING
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
    ],
    [
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(E_HAND_PAWN, F_HAND_PAWN),
        hand_ext(E_HAND_LANCE, F_HAND_LANCE),
        hand_ext(E_HAND_KNIGHT, F_HAND_KNIGHT),
        hand_ext(E_HAND_SILVER, F_HAND_SILVER),
        hand_ext(E_HAND_BISHOP, F_HAND_BISHOP),
        hand_ext(E_HAND_ROOK, F_HAND_ROOK),
        hand_ext(E_HAND_GOLD, F_HAND_GOLD),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
        hand_ext(BONA_PIECE_ZERO, BONA_PIECE_ZERO),
    ],
];

#[must_use]
pub fn board_bona_piece(piece: Piece, sq: Square, perspective: Color) -> Option<BonaPiece> {
    let ext = KPP_BOARD_INDEX[piece.to_index()];
    let base = match perspective {
        Color::BLACK => ext.fb,
        Color::WHITE => ext.fw,
        _ => return None,
    };
    if base == BONA_PIECE_ZERO {
        return None;
    }
    let offset = match perspective {
        Color::BLACK => sq.to_board_index(),
        Color::WHITE => sq.inv().to_board_index(),
        _ => return None,
    };
    let offset_i32 = i32::try_from(offset).ok()?;
    Some(base + offset_i32)
}

#[must_use]
pub fn hand_bona_piece(
    owner: Color,
    piece_type: PieceType,
    index: u32,
    perspective: Color,
) -> Option<BonaPiece> {
    let ext = KPP_HAND_INDEX[owner.to_index()][piece_type.to_index()];
    let base = match perspective {
        Color::BLACK => ext.fb,
        Color::WHITE => ext.fw,
        _ => return None,
    };
    if base == BONA_PIECE_ZERO {
        return None;
    }
    let offset = i32::try_from(index).ok()?;
    Some(base + offset)
}
