//! Zobristキー関連の実装

use crate::types::{Color, Piece, PieceType, Square};
use std::sync::LazyLock;

/// YaneuraOu互換のハッシュキー（デフォルトは64bit、hash-128で128bit）
#[cfg(not(feature = "hash-128"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct ZobristKey(u64);

#[cfg(not(feature = "hash-128"))]
impl ZobristKey {
    #[must_use]
    pub const fn new(low: u64, _high: u64) -> Self {
        Self(low)
    }

    #[must_use]
    pub const fn from_u64(value: u64) -> Self {
        Self(value)
    }

    #[must_use]
    pub const fn low_u64(self) -> u64 {
        self.0
    }

    #[must_use]
    pub const fn high_u64(self) -> u64 {
        0
    }

    /// XOR operation for updating hash
    pub fn xor(&mut self, other: Self) {
        self.0 ^= other.0;
    }

    /// Add operation for material key updates (YaneuraOu互換)
    pub fn add(&mut self, other: Self) {
        self.0 = self.0.wrapping_add(other.0);
    }

    /// Sub operation for material key updates (YaneuraOu互換)
    pub fn sub(&mut self, other: Self) {
        self.0 = self.0.wrapping_sub(other.0);
    }

    #[must_use]
    pub const fn mul_u64(self, rhs: u64) -> Self {
        Self(self.0.wrapping_mul(rhs))
    }
}

#[cfg(feature = "hash-128")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct ZobristKey {
    low: u64,
    high: u64,
}

#[cfg(feature = "hash-128")]
impl ZobristKey {
    #[must_use]
    pub const fn new(low: u64, high: u64) -> Self {
        Self { low, high }
    }

    #[must_use]
    pub const fn from_u64(value: u64) -> Self {
        Self { low: value, high: 0 }
    }

    #[must_use]
    pub const fn low_u64(self) -> u64 {
        self.low
    }

    #[must_use]
    pub const fn high_u64(self) -> u64 {
        self.high
    }

    /// XOR operation for updating hash
    pub fn xor(&mut self, other: Self) {
        self.low ^= other.low;
        self.high ^= other.high;
    }

    /// Add operation for material key updates (YaneuraOu互換)
    pub fn add(&mut self, other: Self) {
        self.low = self.low.wrapping_add(other.low);
        self.high = self.high.wrapping_add(other.high);
    }

    /// Sub operation for material key updates (YaneuraOu互換)
    pub fn sub(&mut self, other: Self) {
        self.low = self.low.wrapping_sub(other.low);
        self.high = self.high.wrapping_sub(other.high);
    }

    #[must_use]
    pub const fn mul_u64(self, rhs: u64) -> Self {
        Self { low: self.low.wrapping_mul(rhs), high: self.high.wrapping_mul(rhs) }
    }
}

impl From<u64> for ZobristKey {
    fn from(value: u64) -> Self {
        Self::from_u64(value)
    }
}

impl std::ops::BitXor for ZobristKey {
    type Output = Self;

    fn bitxor(self, rhs: Self) -> Self::Output {
        #[cfg(not(feature = "hash-128"))]
        {
            Self(self.0 ^ rhs.0)
        }
        #[cfg(feature = "hash-128")]
        {
            Self { low: self.low ^ rhs.low, high: self.high ^ rhs.high }
        }
    }
}

impl std::ops::BitXorAssign for ZobristKey {
    fn bitxor_assign(&mut self, rhs: Self) {
        #[cfg(not(feature = "hash-128"))]
        {
            self.0 ^= rhs.0;
        }
        #[cfg(feature = "hash-128")]
        {
            self.low ^= rhs.low;
            self.high ^= rhs.high;
        }
    }
}

/// Zobrist hash table structure for position hashing
#[derive(Debug)]
pub struct ZobristTable {
    /// Hash values for pieces on squares indexed by piece type and square.
    pub board: [[ZobristKey; Square::SQ_NB_PLUS1]; Piece::PIECE_NB],
    /// Hash values for pieces in hand indexed by color and piece type.
    /// YaneuraOu互換でcount==1の値を基準とし、手駒数に応じて加算する。
    pub hand: [[ZobristKey; PieceType::PIECE_HAND_NB]; Color::COLOR_NB],
    /// Hash value for pawn-less positions (YaneuraOu互換).
    pub no_pawns: ZobristKey,
    /// Hash value for side to move (BLACK = 0, WHITE = this value)
    pub side: ZobristKey,
}

pub const HASH_KEY_BITS: u32 = if cfg!(feature = "hash-128") { 128 } else { 64 };

const BOARD_PIECES: usize = Piece::PIECE_NB;
const BOARD_SQUARES: usize = Square::SQ_NB;
const HAND_PIECES: usize = PieceType::PIECE_HAND_NB;
const MATERIAL_SQUARE_INDEX: usize = 8;
const ZOBRIST_SEED: u64 = 20_151_225;
const PRNG_MULTIPLIER: u64 = 2_685_821_657_736_338_717;

struct Prng {
    state: u64,
}

impl Prng {
    fn new(seed: u64) -> Self {
        debug_assert!(seed != 0, "PRNG seed must be non-zero");
        Self { state: seed }
    }

    fn next_u64(&mut self) -> u64 {
        let mut s = self.state;
        s ^= s >> 12;
        s ^= s << 25;
        s ^= s >> 27;
        self.state = s;
        s.wrapping_mul(PRNG_MULTIPLIER)
    }
}

fn generate_zobrist_table() -> ZobristTable {
    let mut rng = Prng::new(ZOBRIST_SEED);
    let mut board = [[ZobristKey::default(); Square::SQ_NB_PLUS1]; BOARD_PIECES];
    let mut hand = [[ZobristKey::default(); HAND_PIECES]; Color::COLOR_NB];

    let mut next_key = || next_key(&mut rng);

    let side = next_key();
    let no_pawns = next_key();

    for (piece_idx, piece_row) in board.iter_mut().enumerate().take(BOARD_PIECES) {
        if piece_idx == 0 {
            continue;
        }
        for square_entry in piece_row.iter_mut().take(BOARD_SQUARES) {
            *square_entry = next_key();
        }
    }

    for row in hand.iter_mut().take(Color::COLOR_NB) {
        for (piece_idx, cell) in row.iter_mut().enumerate().take(HAND_PIECES) {
            if piece_idx == 0 {
                continue;
            }
            *cell = next_key();
        }
    }

    ZobristTable { board, hand, no_pawns, side }
}

fn next_key(rng: &mut Prng) -> ZobristKey {
    let low = rng.next_u64();
    let high = if HASH_KEY_BITS >= 128 { rng.next_u64() } else { 0 };

    let remaining = if HASH_KEY_BITS >= 128 { 2 } else { 3 };
    for _ in 0..remaining {
        let _ = rng.next_u64();
    }

    ZobristKey::new(low, high)
}

/// Global Zobrist hash table instance generated deterministically from a fixed seed
pub static ZOBRIST: LazyLock<ZobristTable> = LazyLock::new(generate_zobrist_table);

/// Zobrist singleton access wrapper
pub struct Zobrist;

impl Zobrist {
    /// Get the singleton instance
    #[must_use]
    pub fn instance() -> &'static ZobristTable {
        &ZOBRIST
    }

    /// Get hash for a piece on a square
    #[must_use]
    pub fn psq(sq: Square, piece: Piece) -> ZobristKey {
        let table = Self::instance();
        let piece_idx = piece.to_index();
        let square_idx = sq.to_index();
        table.board[piece_idx][square_idx]
    }

    /// Get hash for a piece independent of square (material key)
    #[must_use]
    pub fn material(piece: Piece) -> ZobristKey {
        let table = Self::instance();
        let piece_idx = piece.to_index();
        table.board[piece_idx][MATERIAL_SQUARE_INDEX]
    }

    /// Get hash for pieces in hand (YaneuraOu互換: 基本値 * count)
    #[must_use]
    pub fn hand(color: Color, piece_type: PieceType, count: usize) -> ZobristKey {
        let table = Self::instance();
        let piece_idx = piece_type.to_index();
        if piece_idx == 0 || piece_idx >= PieceType::PIECE_HAND_NB || count == 0 {
            return ZobristKey::default();
        }
        let base = table.hand[color.to_index()][piece_idx];
        base.mul_u64(count as u64)
    }

    /// Get hash for side to move
    #[must_use]
    pub fn side() -> ZobristKey {
        Self::instance().side
    }

    /// Get hash for pawn-less positions
    #[must_use]
    pub fn no_pawns() -> ZobristKey {
        Self::instance().no_pawns
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn zobrist_table_structure() {
        assert_ne!(ZOBRIST.side, ZobristKey::default(), "Side hash should not be zero");
        assert_ne!(ZOBRIST.no_pawns, ZobristKey::default(), "No-pawns hash should not be zero");

        let mut non_zero_count = 0;
        for piece in 0..Piece::PIECE_NB {
            for square in 0..Square::SQ_NB {
                if ZOBRIST.board[piece][square] != ZobristKey::default() {
                    non_zero_count += 1;
                }
            }
        }
        assert!(non_zero_count > 0, "Board hashes should not all be zero");

        non_zero_count = 0;
        for color in 0..Color::COLOR_NB {
            for piece in 1..PieceType::PIECE_HAND_NB {
                if ZOBRIST.hand[color][piece] != ZobristKey::default() {
                    non_zero_count += 1;
                }
            }
        }
        assert!(non_zero_count > 0, "Hand hashes should not all be zero");
    }

    #[test]
    fn zobrist_table_uniqueness() {
        let mut hashes = HashSet::new();

        hashes.insert(ZOBRIST.side);
        hashes.insert(ZOBRIST.no_pawns);

        for piece in 0..Piece::PIECE_NB {
            for square in 0..Square::SQ_NB {
                let hash = ZOBRIST.board[piece][square];
                if hash != ZobristKey::default() {
                    assert!(
                        hashes.insert(hash),
                        "Duplicate hash found in board table: low={:#016x} high={:#016x}",
                        hash.low_u64(),
                        hash.high_u64()
                    );
                }
            }
        }

        for color in 0..Color::COLOR_NB {
            for piece in 1..PieceType::PIECE_HAND_NB {
                let hash = ZOBRIST.hand[color][piece];
                if hash != ZobristKey::default() {
                    assert!(
                        hashes.insert(hash),
                        "Duplicate hash found in hand table: low={:#016x} high={:#016x}",
                        hash.low_u64(),
                        hash.high_u64()
                    );
                }
            }
        }

        let unique_count = hashes.len();
        assert!(unique_count > 100, "Too few unique hashes: {unique_count}");
    }

    #[test]
    fn zobrist_table_size_verification() {
        assert_eq!(ZOBRIST.board.len(), Piece::PIECE_NB);
        assert_eq!(ZOBRIST.board[0].len(), Square::SQ_NB_PLUS1);

        assert_eq!(ZOBRIST.hand.len(), Color::COLOR_NB);
        assert_eq!(ZOBRIST.hand[0].len(), PieceType::PIECE_HAND_NB);

        assert_ne!(ZOBRIST.side, ZobristKey::default());
    }

    #[test]
    fn zobrist_no_piece_is_zero() {
        for square in 0..Square::SQ_NB_PLUS1 {
            assert_eq!(
                ZOBRIST.board[0][square],
                ZobristKey::default(),
                "NO_PIECE hash at square {square} should be 0"
            );
        }
    }

    #[test]
    fn zobrist_zero_count_is_zero() {
        for color in 0..Color::COLOR_NB {
            assert_eq!(
                ZOBRIST.hand[color][0],
                ZobristKey::default(),
                "Hash for NO_PIECE_TYPE in hand should be 0 for color {color}"
            );
        }
    }

    #[test]
    fn zobrist_reproducibility() {
        assert_eq!(ZOBRIST.board[1][0], ZOBRIST.board[1][0]);
        assert_ne!(ZOBRIST.side, ZobristKey::default());
    }

    #[test]
    fn zobrist_distribution() {
        let mut bit_count = [0u32; 64];

        for piece in 1..Piece::PIECE_NB {
            for square in 0..Square::SQ_NB {
                let hash = ZOBRIST.board[piece][square].low_u64();
                for (bit, count) in bit_count.iter_mut().enumerate() {
                    if (hash >> bit) & 1 == 1 {
                        *count += 1;
                    }
                }
            }
        }

        let piece_nb = u32::try_from(Piece::PIECE_NB).expect("piece count fits in u32");
        let square_nb = u32::try_from(Square::SQ_NB).expect("square count fits in u32");
        let total: u32 = (piece_nb - 1) * square_nb;
        for (bit, count) in bit_count.iter().enumerate() {
            let ratio = f64::from(*count) / f64::from(total);
            assert!((0.3..0.7).contains(&ratio), "Bit {bit} has unusual distribution: {ratio:.2}");
        }
    }
}
