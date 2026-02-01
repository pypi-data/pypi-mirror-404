use std::convert::TryFrom;
use std::fmt;
use std::ops::BitOr;
use std::str::FromStr;

use super::file::File;
use super::rank::can_promote as can_promote_rank;
use super::rank::Rank;
use super::Color;

// ビルド時に生成されたテーブルを読み込み
include!(concat!(env!("OUT_DIR"), "/square_tables.rs"));

/// マス表現（0..81 + `SQ_NONE`）
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
#[repr(transparent)]
pub struct Square(pub i8);

// 定数定義（YaneuraOu互換）
pub const SQ_LD: i8 = 10;
pub const SQ_LU: i8 = 8;
pub const SQ_RD: i8 = -8;
pub const SQ_RU: i8 = -10;
pub const SQ_L: i8 = 9;
pub const SQ_R: i8 = -9;
pub const SQ_U: i8 = -1;
pub const SQ_D: i8 = 1;
pub const SQ_ZERO: Square = Square::SQ_ZERO;
pub const SQ_NONE: Square = Square::SQ_NONE;
pub const SQ_NB_PLUS1: usize = Square::SQ_NB_PLUS1;
pub const SQ_NB: usize = Square::SQ_NB;
pub const SQUARE_NB: usize = Square::SQ_NB; // Alias for compatibility
pub const SQ_NB_I8: i8 = 81;
/// 盤面を180度回転させた升目を返す（YaneuraOu互換）。
#[inline]
#[must_use]
pub const fn inv(sq: Square) -> Square {
    Square((SQ_NB_I8 - 1) - sq.0)
}

/// 盤面を左右反転させた升目を返す（YaneuraOu互換）。
#[inline]
#[must_use]
pub const fn mir(sq: Square) -> Square {
    let file = sq.0 / 9;
    let rank = sq.0 % 9;
    Square((8 - file) * 9 + rank)
}

/// 盤面を180度回転させた升目を返す（YaneuraOu互換）。
#[inline]
#[must_use]
pub const fn flip(sq: Square) -> Square {
    Square((SQ_NB_I8 - 1) - sq.0)
}

/// 移動元/移動先が成りゾーンかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub fn can_promote(color: Color, from_or_to: Square) -> bool {
    if !from_or_to.is_ok() || from_or_to.is_none() {
        return false;
    }
    can_promote_rank(color, from_or_to.rank())
}

/// 移動元と移動先のどちらかが成りゾーンかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub fn can_promote_from_to(color: Color, from: Square, to: Square) -> bool {
    can_promote(color, from) || can_promote(color, to)
}
pub const SQ_99: Square = Square(80);
pub const SQ_98: Square = Square(79);
pub const SQ_97: Square = Square(78);
pub const SQ_96: Square = Square(77);
pub const SQ_95: Square = Square(76);
pub const SQ_94: Square = Square(75);
pub const SQ_93: Square = Square(74);
pub const SQ_92: Square = Square(73);
pub const SQ_91: Square = Square(72);
pub const SQ_89: Square = Square(71);
pub const SQ_88: Square = Square(70);
pub const SQ_87: Square = Square(69);
pub const SQ_86: Square = Square(68);
pub const SQ_85: Square = Square(67);
pub const SQ_84: Square = Square(66);
pub const SQ_83: Square = Square(65);
pub const SQ_82: Square = Square(64);
pub const SQ_81: Square = Square(63);
pub const SQ_79: Square = Square(62);
pub const SQ_78: Square = Square(61);
pub const SQ_77: Square = Square(60);
pub const SQ_76: Square = Square(59);
pub const SQ_75: Square = Square(58);
pub const SQ_74: Square = Square(57);
pub const SQ_73: Square = Square(56);
pub const SQ_72: Square = Square(55);
pub const SQ_71: Square = Square(54);
pub const SQ_69: Square = Square(53);
pub const SQ_68: Square = Square(52);
pub const SQ_67: Square = Square(51);
pub const SQ_66: Square = Square(50);
pub const SQ_65: Square = Square(49);
pub const SQ_64: Square = Square(48);
pub const SQ_63: Square = Square(47);
pub const SQ_62: Square = Square(46);
pub const SQ_61: Square = Square(45);
pub const SQ_59: Square = Square(44);
pub const SQ_58: Square = Square(43);
pub const SQ_57: Square = Square(42);
pub const SQ_56: Square = Square(41);
pub const SQ_55: Square = Square(40);
pub const SQ_54: Square = Square(39);
pub const SQ_53: Square = Square(38);
pub const SQ_52: Square = Square(37);
pub const SQ_51: Square = Square(36);
pub const SQ_49: Square = Square(35);
pub const SQ_48: Square = Square(34);
pub const SQ_47: Square = Square(33);
pub const SQ_46: Square = Square(32);
pub const SQ_45: Square = Square(31);
pub const SQ_44: Square = Square(30);
pub const SQ_43: Square = Square(29);
pub const SQ_42: Square = Square(28);
pub const SQ_41: Square = Square(27);
pub const SQ_39: Square = Square(26);
pub const SQ_38: Square = Square(25);
pub const SQ_37: Square = Square(24);
pub const SQ_36: Square = Square(23);
pub const SQ_35: Square = Square(22);
pub const SQ_34: Square = Square(21);
pub const SQ_33: Square = Square(20);
pub const SQ_32: Square = Square(19);
pub const SQ_31: Square = Square(18);
pub const SQ_29: Square = Square(17);
pub const SQ_28: Square = Square(16);
pub const SQ_27: Square = Square(15);
pub const SQ_26: Square = Square(14);
pub const SQ_25: Square = Square(13);
pub const SQ_24: Square = Square(12);
pub const SQ_23: Square = Square(11);
pub const SQ_22: Square = Square(10);
pub const SQ_21: Square = Square(9);
pub const SQ_19: Square = Square(8);
pub const SQ_18: Square = Square(7);
pub const SQ_17: Square = Square(6);
pub const SQ_16: Square = Square(5);
pub const SQ_15: Square = Square(4);
pub const SQ_14: Square = Square(3);
pub const SQ_13: Square = Square(2);
pub const SQ_12: Square = Square(1);
pub const SQ_11: Square = Square(0);
impl Square {
    // 関連定数（YaneuraOu互換）
    /// 無効なマス
    pub const SQ_NONE: Self = Self(81);
    /// ゼロ値
    pub const SQ_ZERO: Self = Self(0);
    /// マスの総数
    pub const SQ_NB: usize = 81;
    /// マスの総数+1（`SQ_NONE` 含む）
    pub const SQ_NB_PLUS1: usize = 82;

    // 方角定数（将棋の座標系）
    // file * 9 + rank なので:
    // 上(U): rank-1 = -1
    // 下(D): rank+1 = +1
    // 右(R): file-1 = -9
    // 左(L): file+1 = +9
    // 注: file+1は9筋側（先手視点で左）に進む。

    /// 新しい`Square`
    #[inline]
    #[must_use]
    pub const fn new(value: i8) -> Self {
        Self(value)
    }

    /// 有効なマスかどうかを判定
    #[must_use]
    pub const fn is_ok(self) -> bool {
        0 <= self.0 && self.0 <= 81 // 0..81 + SQ_NONE(81)
    }

    /// `SQ_NONE` かどうか
    #[inline]
    #[must_use]
    pub const fn is_none(self) -> bool {
        self.0 == Self::SQ_NONE.0
    }

    /// マスから筋を取得
    #[must_use]
    pub fn file(self) -> File {
        if self.0 >= 0 && self.0 < 82 {
            SQUARE_TO_FILE[self.to_index()]
        } else {
            File::new(-1) // 無効な値
        }
    }

    /// マスから段を取得
    #[must_use]
    pub fn rank(self) -> Rank {
        if self.0 >= 0 && self.0 < 82 {
            SQUARE_TO_RANK[self.to_index()]
        } else {
            Rank::new(-1) // 無効な値
        }
    }

    /// 筋と段からマスを生成
    #[must_use]
    pub const fn from_file_rank(file: File, rank: Rank) -> Self {
        if file.is_ok() && rank.is_ok() {
            Self(file.raw() * 9 + rank.raw())
        } else {
            Self::SQ_NONE
        }
    }

    /// 内部値を取得する（主にテスト用）
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }

    /// `USI`形式から`Square`を生成
    #[must_use]
    pub fn from_usi(s: &str) -> Option<Self> {
        s.parse().ok()
    }

    /// インデックス値を取得
    #[must_use]
    pub fn to_index(self) -> usize {
        usize::try_from(self.0).expect("square index should be non-negative")
    }

    /// 盤面を180度回転させた升目を返す（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn inv(self) -> Self {
        inv(self)
    }

    /// 盤面を左右反転させた升目を返す（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn mir(self) -> Self {
        mir(self)
    }

    /// 盤面を180度回転させた升目を返す（YaneuraOu互換）。
    #[inline]
    #[must_use]
    pub const fn flip(self) -> Self {
        flip(self)
    }

    /// 盤面インデックス（0-80）を取得
    #[inline]
    #[must_use]
    pub fn to_board_index(self) -> usize {
        debug_assert!(self.is_ok() && !self.is_none(), "Square out of board: {self:?}");
        self.to_index()
    }

    /// インデックスから`Square`を生成
    #[inline]
    #[must_use]
    pub fn from_index(index: usize) -> Self {
        debug_assert!(index < Self::SQ_NB, "Square index out of range: {index}");
        let value = i8::try_from(index).expect("square index fits in i8");
        Self(value)
    }
}

/// File | Rank でSquareを生成できるようにする
impl BitOr<Rank> for File {
    type Output = Square;

    fn bitor(self, rank: Rank) -> Square {
        Square::from_file_rank(self, rank)
    }
}

impl fmt::Display for Square {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if *self == Self::SQ_NONE {
            write!(f, "NONE")
        } else if self.is_ok() {
            // USI形式: 筋(1-9) + 段(a-i)
            let file_char = self.file().to_usi();
            let rank_char = self.rank().to_usi();
            write!(f, "{file_char}{rank_char}")
        } else {
            write!(f, "INVALID")
        }
    }
}

impl FromStr for Square {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s == "NONE" {
            return Ok(Self::SQ_NONE);
        }

        if s.len() != 2 {
            return Err(format!("Invalid square string: {s}"));
        }

        let mut chars = s.chars();
        let file_char = chars.next().unwrap();
        let rank_char = chars.next().unwrap();

        let file = File::from_usi(file_char)
            .ok_or_else(|| format!("Invalid file character: {file_char}"))?;
        let rank = Rank::from_usi(rank_char)
            .ok_or_else(|| format!("Invalid rank character: {rank_char}"))?;

        Ok(file | rank)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_square_constants() {
        // 定数値検証
        assert_eq!(SQ_11.0, 0);
        assert_eq!(SQ_99.0, 80);
        assert_eq!(SQ_ZERO.0, 0);
        assert_eq!(SQ_NONE.0, 81);
        assert_eq!(SQ_NB, 81);
        assert_eq!(SQ_NB_PLUS1, 82);

        // 方角定数検証
        assert_eq!(SQ_U, -1);
        assert_eq!(SQ_D, 1);
        assert_eq!(SQ_R, -9);
        assert_eq!(SQ_L, 9);
        assert_eq!(SQ_RU, -10);
        assert_eq!(SQ_RD, -8);
        assert_eq!(SQ_LU, 8);
        assert_eq!(SQ_LD, 10);
    }

    #[test]
    fn test_square_is_ok() {
        // 境界値テスト
        assert!(!Square(-1).is_ok());
        assert!(Square(0).is_ok()); // SQ_11
        assert!(Square(40).is_ok()); // SQ_55
        assert!(Square(80).is_ok()); // SQ_99
        assert!(Square(81).is_ok()); // SQ_NONE
        assert!(!Square(82).is_ok());
    }

    #[test]
    fn test_square_specific_positions() {
        // 特定のマスの値を確認
        assert_eq!(SQ_55.0, 40); // 中央
        assert_eq!(SQ_51.0, 36); // 5一
        assert_eq!(SQ_59.0, 44); // 5九
        assert_eq!(SQ_15.0, 4); // 1五
        assert_eq!(SQ_95.0, 76); // 9五
    }

    #[test]
    fn test_square_coordinate_conversion() {
        // file()とrank()のテスト
        let sq = SQ_55; // 中央（file=4, rank=4）
        assert_eq!(sq.file(), File::FILE_5);
        assert_eq!(sq.rank(), Rank::RANK_5);

        let sq = SQ_11; // file=1, rank=1
        assert_eq!(sq.file(), File::FILE_1);
        assert_eq!(sq.rank(), Rank::RANK_1);

        let sq = SQ_99; // file=9, rank=9
        assert_eq!(sq.file(), File::FILE_9);
        assert_eq!(sq.rank(), Rank::RANK_9);

        let sq = SQ_NONE;
        assert_eq!(sq.file(), File::new(-1));
        assert_eq!(sq.rank(), Rank::new(-1));
    }

    #[test]
    fn test_square_from_file_rank() {
        // from_file_rank()のテスト
        assert_eq!(Square::from_file_rank(File::FILE_5, Rank::RANK_5), SQ_55);
        assert_eq!(Square::from_file_rank(File::FILE_1, Rank::RANK_1), SQ_11);
        assert_eq!(Square::from_file_rank(File::FILE_9, Rank::RANK_9), SQ_99);

        // 無効な入力
        assert_eq!(Square::from_file_rank(File::new(-1), Rank::RANK_1), SQ_NONE);
        assert_eq!(Square::from_file_rank(File::FILE_1, Rank::new(-1)), SQ_NONE);
        assert_eq!(Square::from_file_rank(File::new(9), Rank::RANK_1), SQ_NONE);
    }

    #[test]
    fn test_square_bitor_operator() {
        // File | Rank 演算子のテスト
        assert_eq!(File::FILE_5 | Rank::RANK_5, SQ_55);
        assert_eq!(File::FILE_1 | Rank::RANK_1, SQ_11);
        assert_eq!(File::FILE_9 | Rank::RANK_9, SQ_99);

        // round-trip検証
        for i in 0..81 {
            let sq = Square(i);
            let reconstructed = sq.file() | sq.rank();
            assert_eq!(reconstructed, sq);
        }
    }

    #[test]
    fn test_square_display() {
        // USI形式の出力テスト
        assert_eq!(SQ_11.to_string(), "1a"); // 1一
        assert_eq!(SQ_55.to_string(), "5e"); // 5五
        assert_eq!(SQ_99.to_string(), "9i"); // 9九
        assert_eq!(SQ_77.to_string(), "7g"); // 7七
        assert_eq!(SQ_NONE.to_string(), "NONE");

        // 無効な値
        assert_eq!(Square(-1).to_string(), "INVALID");
        assert_eq!(Square(100).to_string(), "INVALID");
    }

    #[test]
    fn test_square_from_str() {
        // USI形式のパーステスト
        assert_eq!("1a".parse::<Square>().unwrap(), SQ_11);
        assert_eq!("5e".parse::<Square>().unwrap(), SQ_55);
        assert_eq!("9i".parse::<Square>().unwrap(), SQ_99);
        assert_eq!("7g".parse::<Square>().unwrap(), SQ_77);
        assert_eq!("NONE".parse::<Square>().unwrap(), SQ_NONE);

        // 不正な入力
        assert!("".parse::<Square>().is_err());
        assert!("0a".parse::<Square>().is_err());
        assert!("5j".parse::<Square>().is_err());
        assert!("aa".parse::<Square>().is_err());
        assert!("123".parse::<Square>().is_err());
    }

    #[test]
    fn test_square_string_roundtrip() {
        // Display/FromStr round-trip検証
        for i in 0..81 {
            let sq = Square(i);
            let s = sq.to_string();
            let parsed: Square = s.parse().unwrap();
            assert_eq!(parsed, sq);
        }

        // SQ_NONEも検証
        let sq = SQ_NONE;
        let s = sq.to_string();
        let parsed: Square = s.parse().unwrap();
        assert_eq!(parsed, sq);
    }

    #[test]
    fn test_square_inv_mir_flip() {
        let sq = SQ_11;
        assert_eq!(sq.inv(), SQ_99);
        assert_eq!(sq.mir(), SQ_91);
        assert_eq!(sq.flip(), SQ_99);

        let sq = SQ_55;
        assert_eq!(sq.inv(), SQ_55);
        assert_eq!(sq.mir(), SQ_55);
        assert_eq!(sq.flip(), SQ_55);

        let sq = SQ_99;
        assert_eq!(sq.inv(), SQ_11);
        assert_eq!(sq.mir(), SQ_19);
        assert_eq!(sq.flip(), SQ_11);
    }
}
