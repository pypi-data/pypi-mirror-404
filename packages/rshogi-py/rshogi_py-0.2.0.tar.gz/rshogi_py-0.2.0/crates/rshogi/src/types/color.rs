use std::convert::TryFrom;
use std::fmt;
use std::ops::Not;
use std::str::FromStr;

/// 手番を表す型（先手 Black = 0、後手 White = 1）
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Color(pub i8);

impl Color {
    // 関連定数（YaneuraOu互換）
    /// 先手（Black）
    pub const BLACK: Self = Self(0);
    /// 後手（White）
    pub const WHITE: Self = Self(1);
    /// ゼロ値（BLACK と同じ）
    pub const COLOR_ZERO: Self = Self(0);
    /// 色の総数
    pub const COLOR_NB: usize = 2;

    /// const fn コンストラクタ
    #[inline]
    #[must_use]
    pub const fn new(value: i8) -> Self {
        Self(value)
    }
    /// 手番を反転する
    #[inline]
    #[must_use]
    pub const fn flip(self) -> Self {
        Self(self.0 ^ 1)
    }

    /// 有効な値かどうかを判定する
    #[inline]
    #[must_use]
    pub fn is_ok(self) -> bool {
        usize::try_from(self.0).map(|idx| idx < Self::COLOR_NB).unwrap_or(false)
    }

    /// 内部値を取得する（主にテスト用）
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }

    /// `Color` をインデックスに変換
    #[inline]
    #[must_use]
    #[allow(clippy::cast_sign_loss)]
    pub const fn to_index(self) -> usize {
        self.0 as usize
    }
}

impl Not for Color {
    type Output = Self;

    #[inline]
    fn not(self) -> Self::Output {
        self.flip()
    }
}

impl fmt::Display for Color {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.0 {
            0 => write!(f, "Black"),
            1 => write!(f, "White"),
            _ => write!(f, "Invalid({})", self.0),
        }
    }
}

impl FromStr for Color {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "black" => Ok(Self::BLACK),
            "white" => Ok(Self::WHITE),
            _ => Err(format!("Invalid color string: {s}")),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_constants() {
        // 定数値検証（BLACK=0, WHITE=1, COLOR_NB=2）
        assert_eq!(Color::BLACK.raw(), 0);
        assert_eq!(Color::WHITE.raw(), 1);
        assert_eq!(Color::COLOR_ZERO.raw(), 0);
        assert_eq!(Color::COLOR_NB, 2);
    }

    #[test]
    fn test_new_constructor() {
        // const fn コンストラクタのテスト
        const BLACK_CONST: Color = Color::new(0);
        const WHITE_CONST: Color = Color::new(1);

        assert_eq!(BLACK_CONST, Color::BLACK);
        assert_eq!(WHITE_CONST, Color::WHITE);
    }

    #[test]
    fn test_color_flip() {
        // 反転操作のround-trip検証（c.flip().flip() == c）
        assert_eq!(Color::BLACK.flip(), Color::WHITE);
        assert_eq!(Color::WHITE.flip(), Color::BLACK);
        assert_eq!(Color::BLACK.flip().flip(), Color::BLACK);
        assert_eq!(Color::WHITE.flip().flip(), Color::WHITE);
    }

    #[test]
    fn test_color_not_operator() {
        // Not演算子のテスト
        assert_eq!(!Color::BLACK, Color::WHITE);
        assert_eq!(!Color::WHITE, Color::BLACK);
        assert_eq!(!!Color::BLACK, Color::BLACK);
        assert_eq!(!!Color::WHITE, Color::WHITE);
    }

    #[test]
    fn test_color_display() {
        // Display トレイトのテスト
        assert_eq!(Color::BLACK.to_string(), "Black");
        assert_eq!(Color::WHITE.to_string(), "White");
        assert_eq!(Color(2).to_string(), "Invalid(2)");
    }

    #[test]
    fn test_color_from_str() {
        // FromStr トレイトのテスト
        assert_eq!(Color::from_str("Black").unwrap(), Color::BLACK);
        assert_eq!(Color::from_str("White").unwrap(), Color::WHITE);
        assert_eq!(Color::from_str("black").unwrap(), Color::BLACK);
        assert_eq!(Color::from_str("white").unwrap(), Color::WHITE);
        assert_eq!(Color::from_str("BLACK").unwrap(), Color::BLACK);
        assert_eq!(Color::from_str("WHITE").unwrap(), Color::WHITE);

        assert!(Color::from_str("invalid").is_err());
        assert!(Color::from_str("").is_err());
    }

    #[test]
    fn test_color_display_from_str_roundtrip() {
        // Display/FromStr のround-trip検証
        let black_str = Color::BLACK.to_string();
        assert_eq!(Color::from_str(&black_str).unwrap(), Color::BLACK);

        let white_str = Color::WHITE.to_string();
        assert_eq!(Color::from_str(&white_str).unwrap(), Color::WHITE);
    }

    #[test]
    fn test_color_is_ok() {
        // 境界値テスト（-1, 0, 1, 2でis_ok()を検証）
        assert!(!Color(-1).is_ok());
        assert!(Color(0).is_ok());
        assert!(Color(1).is_ok());
        assert!(!Color(2).is_ok());
        assert!(!Color(3).is_ok());
    }

    #[test]
    fn test_color_copy_clone() {
        // Copy/Clone トレイトのテスト
        let c = Color::BLACK;
        let c2 = c; // Copy
        assert_eq!(c, c2);

        #[allow(clippy::clone_on_copy)]
        let c3 = c.clone(); // Clone
        assert_eq!(c, c3);
    }
}
