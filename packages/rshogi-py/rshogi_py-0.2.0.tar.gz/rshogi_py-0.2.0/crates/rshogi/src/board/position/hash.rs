use super::{Position, MINOR_PIECE_TYPES};
use crate::board::zobrist::{Zobrist, ZobristKey};
use crate::types::{Color, Hand, HandPiece, Move, Piece, PieceType};

#[allow(clippy::struct_field_names)]
pub(in crate::board) struct KeySet {
    pub(in crate::board) board_key: ZobristKey,
    pub(in crate::board) hand_key: ZobristKey,
    pub(in crate::board) pawn_key: ZobristKey,
    pub(in crate::board) minor_piece_key: ZobristKey,
    pub(in crate::board) non_pawn_key: [ZobristKey; Color::COLOR_NB],
    pub(in crate::board) material_key: ZobristKey,
}

impl Position {
    /// 局面全体のZobristキー
    #[must_use]
    pub const fn board_key(&self) -> ZobristKey {
        self.board_key
    }

    /// 持ち駒のZobristキー
    #[must_use]
    pub const fn hand_key(&self) -> ZobristKey {
        self.hand_key
    }

    /// 歩のみのZobristキー
    #[must_use]
    pub const fn pawn_key(&self) -> ZobristKey {
        self.pawn_key
    }

    /// 小駒のみのZobristキー
    #[must_use]
    pub const fn minor_piece_key(&self) -> ZobristKey {
        self.minor_piece_key
    }

    /// 歩以外のZobristキー
    #[must_use]
    pub const fn non_pawn_key(&self, color: Color) -> ZobristKey {
        self.non_pawn_key[color.to_index()]
    }

    /// 盤上の駒構成Zobristキー
    #[must_use]
    pub const fn material_key(&self) -> ZobristKey {
        self.material_key
    }

    /// Zobristハッシュを完全計算
    pub(in crate::board) fn compute_keys(&self) -> KeySet {
        let mut board_key = ZobristKey::default();
        let mut hand_key = ZobristKey::default();
        let mut pawn_key = Zobrist::no_pawns();
        let mut minor_piece_key = ZobristKey::default();
        let mut non_pawn_key = [ZobristKey::default(); Color::COLOR_NB];
        let mut material_key = ZobristKey::default();

        // 盤上の駒
        for (sq, packed) in self.board.iter() {
            if !packed.is_empty() {
                let piece = packed.to_piece();
                board_key ^= Zobrist::psq(sq, piece);
                if piece.piece_type() == PieceType::PAWN {
                    pawn_key ^= Zobrist::psq(sq, piece);
                } else {
                    non_pawn_key[piece.color().to_index()] ^= Zobrist::psq(sq, piece);
                }
                if MINOR_PIECE_TYPES.contains(&piece.piece_type()) {
                    minor_piece_key ^= Zobrist::psq(sq, piece);
                }
                material_key.add(Zobrist::material(piece));
            }
        }

        // 持ち駒
        for color in [Color::BLACK, Color::WHITE] {
            let hand = self.hand_of(color);
            for hp in 0..7 {
                let hp = HandPiece(hp);
                let count = Hand::hand_count(hand, hp);
                if count > 0 {
                    hand_key.add(Zobrist::hand(color, hp.into_piece_type(), count as usize));
                }
            }
        }

        // 手番
        if self.side_to_move == Color::WHITE {
            board_key ^= Zobrist::side();
        }

        KeySet { board_key, hand_key, pawn_key, minor_piece_key, non_pawn_key, material_key }
    }

    /// 指し手適用後のZobristキーを計算（YaneuraOu互換）
    #[must_use]
    pub fn key_after(&self, mv: Move) -> ZobristKey {
        let us = self.side_to_move;
        let mut board_key = self.board_key ^ Zobrist::side();
        let mut hand_key = self.hand_key;
        let to = mv.to_sq();

        if mv.is_drop() {
            let piece_type =
                mv.dropped_piece().expect("drop move must include a dropped piece type");
            let piece = Piece::make(us, piece_type);
            board_key ^= Zobrist::psq(to, piece);
            hand_key.sub(Zobrist::hand(us, piece_type, 1));
        } else {
            let from = mv.from_sq();
            let moved_piece = self.piece_on(from);
            debug_assert!(moved_piece != Piece::NO_PIECE, "move must originate from a piece");

            let moved_after = if mv.is_promote() { moved_piece.promote() } else { moved_piece };

            let captured = self.piece_on(to);
            if captured != Piece::NO_PIECE {
                board_key ^= Zobrist::psq(to, captured);
                hand_key.add(Zobrist::hand(us, captured.piece_type().demote(), 1));
            }

            board_key ^= Zobrist::psq(from, moved_piece);
            board_key ^= Zobrist::psq(to, moved_after);
        }

        board_key ^ hand_key
    }
}
