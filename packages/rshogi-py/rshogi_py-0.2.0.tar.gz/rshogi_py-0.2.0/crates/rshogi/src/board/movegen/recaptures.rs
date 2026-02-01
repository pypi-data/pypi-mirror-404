use crate::board::{MoveList, Position};
use crate::types::Square;

use super::generate::generate_moves_to;
use super::types::{Recaptures, RecapturesAll};

/// 指定マスへの移動手（Recaptures）を生成
pub fn generate_recaptures(pos: &Position, target: Square, list: &mut MoveList) {
    generate_moves_to::<Recaptures>(pos, target, list);
}

/// 指定マスへの移動手（Recaptures, 歩の不成なども含む）を生成
pub fn generate_recaptures_all(pos: &Position, target: Square, list: &mut MoveList) {
    generate_moves_to::<RecapturesAll>(pos, target, list);
}
