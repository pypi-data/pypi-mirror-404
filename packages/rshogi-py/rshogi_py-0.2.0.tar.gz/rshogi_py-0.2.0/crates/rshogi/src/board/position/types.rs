use crate::types::{Color, File, HandPiece, Piece, PieceType, Square, SQUARE_NB};
use std::convert::TryFrom;

/// USIプロトコルで使用される手数型
pub type Ply = u16;

/// 盤面の1マスを1バイトで表現する型
///
/// エンコーディング:
/// - bit 0-3: 駒種（PieceType: 0=なし, 1=歩, 2=香, 3=桂, 4=銀, 5=角, 6=飛, 7=金, 8=玉, 9-14=成駒）
/// - bit 4: 先後（0=先手, 1=後手）
/// - bit 5: 成りフラグ
/// - bit 6-7: 予約（0固定）
#[repr(transparent)]
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct PackedPiece(pub u8);

const PIECE_TYPE_FROM_INDEX: [PieceType; PieceType::PIECE_TYPE_NB] = [
    PieceType::NO_PIECE_TYPE,
    PieceType::PAWN,
    PieceType::LANCE,
    PieceType::KNIGHT,
    PieceType::SILVER,
    PieceType::BISHOP,
    PieceType::ROOK,
    PieceType::GOLD,
    PieceType::KING,
    PieceType::PRO_PAWN,
    PieceType::PRO_LANCE,
    PieceType::PRO_KNIGHT,
    PieceType::PRO_SILVER,
    PieceType::HORSE,
    PieceType::DRAGON,
    // GOLDSは盤上に置かれないが、配列サイズ互換のため保持する。
    PieceType::GOLDS,
];

pub(in crate::board) const MINOR_PIECE_TYPES: [PieceType; 8] = [
    PieceType::LANCE,
    PieceType::KNIGHT,
    PieceType::SILVER,
    PieceType::GOLD,
    PieceType::PRO_LANCE,
    PieceType::PRO_KNIGHT,
    PieceType::PRO_SILVER,
    PieceType::PRO_PAWN,
];

impl PackedPiece {
    /// 空のマス
    pub const EMPTY: Self = Self(0);

    /// `PackedPiece` を作成
    #[inline]
    #[must_use]
    pub fn new(piece_type: PieceType, color: Color, promoted: bool) -> Self {
        if piece_type == PieceType::NO_PIECE_TYPE {
            return Self::EMPTY;
        }

        let mut value = u8::try_from(piece_type.to_index()).expect("piece type index fits in u8");
        if color == Color::WHITE {
            value |= 0x10; // bit 4に先後
        }
        if promoted {
            value |= 0x20; // bit 5に成りフラグ
        }
        Self(value)
    }

    /// Pieceから変換
    #[inline]
    #[must_use]
    pub fn from_piece(piece: Piece) -> Self {
        if piece == Piece::NO_PIECE {
            return Self::EMPTY;
        }

        let piece_type = piece.piece_type();
        let color = piece.color();

        // Check if promoted based on piece type value
        let promoted = matches!(
            piece_type,
            PieceType::PRO_PAWN
                | PieceType::PRO_LANCE
                | PieceType::PRO_KNIGHT
                | PieceType::PRO_SILVER
                | PieceType::HORSE
                | PieceType::DRAGON
        );

        // Get base piece type for promoted pieces
        let base_piece_type = if promoted {
            match piece_type {
                PieceType::PRO_PAWN => PieceType::PAWN,
                PieceType::PRO_LANCE => PieceType::LANCE,
                PieceType::PRO_KNIGHT => PieceType::KNIGHT,
                PieceType::PRO_SILVER => PieceType::SILVER,
                PieceType::HORSE => PieceType::BISHOP,
                PieceType::DRAGON => PieceType::ROOK,
                _ => piece_type,
            }
        } else {
            piece_type
        };
        Self::new(base_piece_type, color, promoted)
    }

    /// Pieceへ変換
    #[inline]
    #[must_use]
    pub fn to_piece(self) -> Piece {
        if self == Self::EMPTY {
            return Piece::NO_PIECE;
        }

        let piece_type = self.piece_type();
        let color = self.color();

        if self.is_promoted() {
            // 成り駒の場合
            let promoted_type = match piece_type {
                PieceType::PAWN => PieceType::PRO_PAWN,
                PieceType::LANCE => PieceType::PRO_LANCE,
                PieceType::KNIGHT => PieceType::PRO_KNIGHT,
                PieceType::SILVER => PieceType::PRO_SILVER,
                PieceType::BISHOP => PieceType::HORSE,
                PieceType::ROOK => PieceType::DRAGON,
                _ => piece_type, // 金・玉は成らない
            };
            Piece::make(color, promoted_type)
        } else {
            Piece::make(color, piece_type)
        }
    }

    /// 駒種を取得
    #[inline]
    #[must_use]
    pub fn piece_type(self) -> PieceType {
        let idx = usize::from(self.0 & 0x0F);
        PIECE_TYPE_FROM_INDEX.get(idx).copied().unwrap_or(PieceType::NO_PIECE_TYPE)
    }

    /// 先後を取得
    #[inline]
    #[must_use]
    pub const fn color(self) -> Color {
        if (self.0 & 0x10) != 0 {
            // bit 4をチェック
            Color::WHITE
        } else {
            Color::BLACK
        }
    }

    /// 成り判定
    #[inline]
    #[must_use]
    pub const fn is_promoted(self) -> bool {
        (self.0 & 0x20) != 0
    }

    /// 空マス判定
    #[inline]
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.0 == 0
    }
}

/// 盤面の81マスを保持する配列
#[derive(Clone, Copy, Debug)]
pub struct BoardArray([PackedPiece; SQUARE_NB]);

impl BoardArray {
    /// 指定した駒で埋めた盤面を作成
    #[must_use]
    pub const fn filled(piece: PackedPiece) -> Self {
        Self([piece; SQUARE_NB])
    }

    /// 空の盤面を作成
    #[must_use]
    pub const fn empty() -> Self {
        Self::filled(PackedPiece::EMPTY)
    }

    /// 指定マスに駒を設定
    #[inline]
    pub fn set(&mut self, sq: Square, piece: PackedPiece) {
        debug_assert!(sq.is_ok() && !sq.is_none(), "Invalid square: {sq:?}");
        self.0[sq.to_board_index()] = piece;
    }

    /// 指定マスの駒を取得
    #[inline]
    #[must_use]
    pub fn get(&self, sq: Square) -> PackedPiece {
        debug_assert!(sq.is_ok() && !sq.is_none(), "Invalid square: {sq:?}");
        self.0[sq.to_board_index()]
    }

    /// イテレータを返す
    pub fn iter(&self) -> impl Iterator<Item = (Square, PackedPiece)> + '_ {
        self.0.iter().enumerate().map(|(idx, &piece)| (Square::from_index(idx), piece))
    }
}

impl Default for BoardArray {
    fn default() -> Self {
        Self::empty()
    }
}

/// エラー型定義
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MoveError {
    NoStateInfo,
    StackUnderflow,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidationError {
    NoKing(Color),
    TwoKings(Color),
    DoublePawn(File, Color),
    InvalidHandCount { piece: HandPiece, count: u32 },
    InvalidPlacement(Square, PieceType),
}
