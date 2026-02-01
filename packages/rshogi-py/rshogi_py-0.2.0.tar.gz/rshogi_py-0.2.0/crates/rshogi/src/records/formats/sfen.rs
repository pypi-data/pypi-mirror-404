use crate::board::{generate_sfen, generate_sfen_with_ply, parse_sfen, Position};

pub use crate::board::{SfenData, SfenError};

/// `records` 用に SFEN 文字列のパースをラップします。
pub fn parse(sfen: &str) -> Result<SfenData, SfenError> {
    parse_sfen(sfen)
}

/// `records` 用の SFEN 生成（手数なし）。
#[must_use]
pub fn generate(pos: &Position) -> String {
    generate_sfen(pos)
}

/// `records` 用の SFEN 生成（手数指定）。
#[must_use]
pub fn generate_with_ply(pos: &Position, ply: Option<i32>) -> String {
    generate_sfen_with_ply(pos, ply)
}
