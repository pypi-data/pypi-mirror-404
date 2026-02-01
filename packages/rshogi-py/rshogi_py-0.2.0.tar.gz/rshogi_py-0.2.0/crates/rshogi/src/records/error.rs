use thiserror::Error;

/// 共通の棋譜エラー型。
#[derive(Debug, Error)]
pub enum RecordError {
    /// 初期局面 SFEN が空。
    #[error("initial position SFEN cannot be empty")]
    EmptyInitPosition,

    /// 終局情報に含まれる手数と実際の手数が一致しない。
    #[error("ply_count mismatch: expected {expected}, got {actual}")]
    PlyCountMismatch { expected: usize, actual: usize },
}
