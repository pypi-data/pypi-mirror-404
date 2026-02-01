//! 駒割り（先手視点）の計算ユーティリティ。

use crate::board::position::Position;
use crate::types::{Color, HandPiece, Piece, PieceType};

const PIECE_VALUES: [i32; PieceType::PIECE_TYPE_NB] = [
    0,      // NO_PIECE_TYPE
    90,     // PAWN
    315,    // LANCE
    405,    // KNIGHT
    495,    // SILVER
    855,    // BISHOP
    990,    // ROOK
    540,    // GOLD
    15_000, // KING
    540,    // PRO_PAWN
    540,    // PRO_LANCE
    540,    // PRO_KNIGHT
    540,    // PRO_SILVER
    945,    // HORSE
    1_395,  // DRAGON
    0,      // GOLDS (unused)
];

/// 駒種の価値を返す（先後に関係なく正の値）。
#[must_use]
pub const fn piece_value(piece_type: PieceType) -> i32 {
    PIECE_VALUES[piece_type.to_index()]
}

#[inline]
fn color_sign(color: Color) -> i32 {
    if color == Color::BLACK {
        1
    } else {
        -1
    }
}

/// 盤上の駒価値（先手視点）を返す。
#[must_use]
pub fn piece_value_signed(piece: Piece) -> i32 {
    if piece == Piece::NO_PIECE {
        return 0;
    }
    color_sign(piece.color()) * piece_value(piece.piece_type())
}

/// 局面の駒割りを計算する（先手視点、手駒込み）。
#[must_use]
pub fn material_value(pos: &Position) -> i32 {
    let mut value = 0;

    for (_sq, packed) in pos.board.iter() {
        let piece = packed.to_piece();
        value += piece_value_signed(piece);
    }

    for color in [Color::BLACK, Color::WHITE] {
        let hand = pos.hands[color.to_index()];
        for hp_raw in 0..HandPiece::HAND_NB {
            let hp = HandPiece(i8::try_from(hp_raw).expect("hand piece index fits in i8"));
            let count = hand.count(hp);
            if count == 0 {
                continue;
            }
            let pt = hp.into_piece_type();
            let delta = piece_value(pt) * i32::try_from(count).expect("hand count fits in i32");
            value += color_sign(color) * delta;
        }
    }

    value
}

/// 捕獲による駒割り差分を返す（先手視点）。
#[must_use]
pub fn capture_material_delta(capturer: Color, captured_piece: Piece) -> i32 {
    if captured_piece == Piece::NO_PIECE {
        return 0;
    }
    let sign = color_sign(capturer);
    let captured_value = piece_value(captured_piece.piece_type());
    let hand_value = piece_value(captured_piece.piece_type().demote());
    sign * (captured_value + hand_value)
}

/// 成りによる駒割り差分を返す（先手視点）。
#[must_use]
pub fn promotion_material_delta(color: Color, before: PieceType, after: PieceType) -> i32 {
    let sign = color_sign(color);
    sign * (piece_value(after) - piece_value(before))
}
