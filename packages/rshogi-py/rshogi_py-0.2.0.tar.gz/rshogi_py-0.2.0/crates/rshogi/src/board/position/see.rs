//! SEE（Static Exchange Evaluation）。
//!
//! 取る手に対して、目標マスでの取り合いを静的にシミュレートし、
//! 最終的な駒得（センチポーン）を返す。

use super::Position;
use crate::board::Bitboard;
use crate::types::{Color, Move, Piece, PieceType, Square};
use std::sync::OnceLock;

static TRACE_SEE_1A1E: OnceLock<bool> = OnceLock::new();
static TRACE_SEE_GE_MOVE: OnceLock<Option<String>> = OnceLock::new();

#[inline]
fn trace_see_1a1e_enabled() -> bool {
    *TRACE_SEE_1A1E
        .get_or_init(|| std::env::var("TOCCATINA_TRACE_SEE_1A1E").map_or(false, |v| v != "0"))
}

#[inline]
fn trace_see_ge_target() -> Option<&'static str> {
    TRACE_SEE_GE_MOVE.get_or_init(|| std::env::var("TOCCATINA_TRACE_SEE_GE_MOVE").ok()).as_deref()
}

#[inline]
fn trace_see_ge_enabled(mv: Move) -> bool {
    let Some(target) = trace_see_ge_target() else {
        return false;
    };
    let usi = mv.to_usi();
    usi.eq_ignore_ascii_case(target)
}

#[inline]
fn bitboard_to_squares(mut bits: Bitboard) -> String {
    if bits.is_empty() {
        return "-".to_string();
    }
    let mut squares = Vec::new();
    while let Some(sq) = bits.pop_lsb() {
        squares.push(format!("{sq}"));
    }
    squares.join(",")
}

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

/// 駒種に対応するSEE用価値を返す。
#[must_use]
pub const fn piece_value(pt: PieceType) -> i32 {
    PIECE_VALUES[pt.to_index()]
}

#[inline]
fn is_debug_see_1a1e_move(from: Square, to: Square) -> bool {
    from.file().raw() == 0 && from.rank().raw() == 0 && to.file().raw() == 0 && to.rank().raw() == 4
}

/// 指定された色の王をピンしている相手の駒（pinners）を計算する。
/// YaneuraOuのst->pinners[~c]に相当。
#[must_use]
fn compute_pinners(pos: &Position, king_color: Color) -> Bitboard {
    use crate::board::attack_tables::{bishop_attacks, lance_attacks, rook_attacks};

    let king_bb = pos.bitboards().pieces_of(PieceType::KING, king_color);
    let Some(king_sq) = king_bb.lsb() else {
        return Bitboard::EMPTY;
    };

    let them = king_color.flip();
    let rook_like = pos.bitboards().pieces_of(PieceType::ROOK, them)
        | pos.bitboards().pieces_of(PieceType::DRAGON, them);
    let bishop_like = pos.bitboards().pieces_of(PieceType::BISHOP, them)
        | pos.bitboards().pieces_of(PieceType::HORSE, them);
    let lance_like = pos.bitboards().pieces_of(PieceType::LANCE, them);

    // snipersを計算（相手の長距離駒で王に向かって利きがある駒）
    let rook_snipers = rook_like & rook_attacks(king_sq, Bitboard::EMPTY);
    let bishop_snipers = bishop_like & bishop_attacks(king_sq, Bitboard::EMPTY);
    let lance_snipers = lance_like & lance_attacks(king_sq, Bitboard::EMPTY, king_color);

    let mut snipers = rook_snipers | bishop_snipers | lance_snipers;

    // snipersがpinnersになる（王との間に1個だけ駒がある場合）
    let occupancy = pos.bitboards().occupied();
    let our_pieces = pos.bitboards().color_pieces(king_color);

    let mut pinners = Bitboard::EMPTY;
    while let Some(sniper_sq) = snipers.pop_lsb() {
        let between = crate::board::Bitboard::between(sniper_sq, king_sq) & occupancy;

        // 間に1個だけ駒があり、かつそれが自分の駒なら、sniperはpinner
        if between.count() == 1 && !(between & our_pieces).is_empty() {
            pinners.set(sniper_sq);
        }
    }

    pinners
}

#[inline]
fn piece_on(pos: &Position, sq: Square) -> Piece {
    pos.piece_on(sq)
}

fn least_valuable_attacker(
    pos: &Position,
    attackers: Bitboard,
    color: Color,
) -> Option<(Square, PieceType)> {
    // 駒価値の安い順に走査して、該当する攻撃駒を返す。
    // 成駒は基底種にフォールバック（価値で十分表現できる）。
    fn first_bit(bb: Bitboard) -> Option<Square> {
        bb.lsb()
    }

    let pawn_attackers = pos.bitboards().pieces_of(PieceType::PAWN, color) & attackers;
    if let Some(sq) = first_bit(pawn_attackers) {
        return Some((sq, PieceType::PAWN));
    }

    let lance_attackers = pos.bitboards().pieces_of(PieceType::LANCE, color) & attackers;
    if let Some(sq) = first_bit(lance_attackers) {
        return Some((sq, PieceType::LANCE));
    }

    let knight_attackers = pos.bitboards().pieces_of(PieceType::KNIGHT, color) & attackers;
    if let Some(sq) = first_bit(knight_attackers) {
        return Some((sq, PieceType::KNIGHT));
    }

    let silver_attackers = pos.bitboards().pieces_of(PieceType::SILVER, color) & attackers;
    if let Some(sq) = first_bit(silver_attackers) {
        return Some((sq, PieceType::SILVER));
    }

    let gold_like = pos.bitboards().pieces_of(PieceType::GOLD, color)
        | pos.bitboards().pieces_of(PieceType::PRO_PAWN, color)
        | pos.bitboards().pieces_of(PieceType::PRO_LANCE, color)
        | pos.bitboards().pieces_of(PieceType::PRO_KNIGHT, color)
        | pos.bitboards().pieces_of(PieceType::PRO_SILVER, color);
    let gold_attackers = gold_like & attackers;
    if let Some(sq) = first_bit(gold_attackers) {
        // 判別のために実際の駒種を取得
        let piece = pos.piece_on(sq).piece_type();
        return Some((sq, piece));
    }

    let bishop_attackers = pos.bitboards().pieces_of(PieceType::BISHOP, color) & attackers;
    if let Some(sq) = first_bit(bishop_attackers) {
        return Some((sq, PieceType::BISHOP));
    }

    let rook_attackers = pos.bitboards().pieces_of(PieceType::ROOK, color) & attackers;
    if let Some(sq) = first_bit(rook_attackers) {
        return Some((sq, PieceType::ROOK));
    }

    let horse_attackers = pos.bitboards().pieces_of(PieceType::HORSE, color) & attackers;
    if let Some(sq) = first_bit(horse_attackers) {
        return Some((sq, PieceType::HORSE));
    }

    let dragon_attackers = pos.bitboards().pieces_of(PieceType::DRAGON, color) & attackers;
    if let Some(sq) = first_bit(dragon_attackers) {
        return Some((sq, PieceType::DRAGON));
    }

    let king_attackers = pos.bitboards().pieces_of(PieceType::KING, color) & attackers;
    first_bit(king_attackers).map(|sq| (sq, PieceType::KING))
}

#[derive(Clone, Copy)]
enum Direction {
    North,
    South,
    East,
    West,
    NorthEast,
    NorthWest,
    SouthEast,
    SouthWest,
}

fn direction_between(to: Square, sq: Square) -> Option<Direction> {
    let to_file = to.file().raw();
    let to_rank = to.rank().raw();
    let sq_file = sq.file().raw();
    let sq_rank = sq.rank().raw();

    let df = sq_file - to_file;
    let dr = sq_rank - to_rank;

    if df == 0 && dr == 0 {
        return None;
    }

    let file_step = df.signum();
    let rank_step = dr.signum();

    match (file_step, rank_step) {
        (0, 1) => Some(Direction::South),
        (0, -1) => Some(Direction::North),
        (1, 0) => Some(Direction::East),
        (-1, 0) => Some(Direction::West),
        (1, 1) if df.abs() == dr.abs() => Some(Direction::SouthEast),
        (1, -1) if df.abs() == dr.abs() => Some(Direction::NorthEast),
        (-1, 1) if df.abs() == dr.abs() => Some(Direction::SouthWest),
        (-1, -1) if df.abs() == dr.abs() => Some(Direction::NorthWest),
        _ => None,
    }
}

const fn direction_delta(dir: Direction) -> (i8, i8) {
    match dir {
        Direction::North => (0, -1),
        Direction::South => (0, 1),
        Direction::East => (1, 0),
        Direction::West => (-1, 0),
        Direction::NorthEast => (1, -1),
        Direction::NorthWest => (-1, -1),
        Direction::SouthEast => (1, 1),
        Direction::SouthWest => (-1, 1),
    }
}

fn ray_effect(to: Square, dir: Direction, occupied: Bitboard) -> Bitboard {
    // YaneuraOuのrayEffectはQUGIY_STEP_EFFECTでRU/R/RD方向をbyte_reverseしている。
    // SEE用のray_effectは盤上の占有で停止するため単純な走査だが、方向定義は同じ。
    let (df, dr) = direction_delta(dir);
    let mut file = to.file().raw() + df;
    let mut rank = to.rank().raw() + dr;
    let mut ray = Bitboard::EMPTY;

    while (0..9).contains(&file) && (0..9).contains(&rank) {
        let file_idx = usize::try_from(file).expect("file within board bounds");
        let rank_idx = usize::try_from(rank).expect("rank within board bounds");
        let idx = file_idx * 9 + rank_idx;
        let sq = Square::from_index(idx);
        ray.set(sq);
        if occupied.test(sq) {
            break;
        }
        file += df;
        rank += dr;
    }

    ray
}

fn xray_attackers(
    to: Square,
    removed_sq: Square,
    occupied: Bitboard,
    bishop_like: Bitboard,
    rook_like: Bitboard,
    black_lances: Bitboard,
    white_lances: Bitboard,
) -> Bitboard {
    let Some(dir) = direction_between(to, removed_sq) else {
        return Bitboard::EMPTY;
    };

    let ray = ray_effect(to, dir, occupied);
    match dir {
        Direction::North => ray & (rook_like | white_lances),
        Direction::South => ray & (rook_like | black_lances),
        Direction::East | Direction::West => ray & rook_like,
        Direction::NorthEast
        | Direction::NorthWest
        | Direction::SouthEast
        | Direction::SouthWest => ray & bishop_like,
    }
}

fn remove_from_slider_sets(
    pt: PieceType,
    color: Color,
    mask: Bitboard,
    bishop_like: &mut Bitboard,
    rook_like: &mut Bitboard,
    black_lances: &mut Bitboard,
    white_lances: &mut Bitboard,
) {
    match pt {
        PieceType::BISHOP | PieceType::HORSE => *bishop_like = *bishop_like & !mask,
        PieceType::ROOK | PieceType::DRAGON => *rook_like = *rook_like & !mask,
        PieceType::LANCE => {
            if color == Color::BLACK {
                *black_lances = *black_lances & !mask;
            } else if color == Color::WHITE {
                *white_lances = *white_lances & !mask;
            }
        }
        _ => {}
    }
}

#[derive(Clone, Copy)]
struct SelectedAttacker {
    sq: Square,
    value: i32,
    remove_pt: PieceType,
    add_xray: bool,
    is_king: bool,
}

struct AttackerSets {
    pawns: [Bitboard; 2],
    lances: [Bitboard; 2],
    knights: [Bitboard; 2],
    silvers: [Bitboard; 2],
    gold_like: [Bitboard; 2],
    bishops: [Bitboard; 2],
    rooks: [Bitboard; 2],
    horses: [Bitboard; 2],
    dragons: [Bitboard; 2],
    kings: [Bitboard; 2],
}

#[allow(clippy::too_many_lines)]
fn select_attacker(
    stm_attackers: Bitboard,
    stm: Color,
    sets: &AttackerSets,
) -> Option<SelectedAttacker> {
    let stm_index = stm.to_index();

    let mut bb = stm_attackers & sets.pawns[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::PAWN),
            remove_pt: PieceType::NO_PIECE_TYPE,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.lances[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::LANCE),
            remove_pt: PieceType::LANCE,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.knights[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::KNIGHT),
            remove_pt: PieceType::NO_PIECE_TYPE,
            add_xray: false,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.silvers[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::SILVER),
            remove_pt: PieceType::NO_PIECE_TYPE,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.gold_like[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::GOLD),
            remove_pt: PieceType::NO_PIECE_TYPE,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.bishops[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::BISHOP),
            remove_pt: PieceType::BISHOP,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.rooks[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::ROOK),
            remove_pt: PieceType::ROOK,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.horses[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::HORSE),
            remove_pt: PieceType::HORSE,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.dragons[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: piece_value(PieceType::DRAGON),
            remove_pt: PieceType::DRAGON,
            add_xray: true,
            is_king: false,
        });
    }

    bb = stm_attackers & sets.kings[stm_index];
    if !bb.is_empty() {
        return Some(SelectedAttacker {
            sq: bb.lsb().expect("attackers not empty"),
            value: 0,
            remove_pt: PieceType::NO_PIECE_TYPE,
            add_xray: false,
            is_king: true,
        });
    }

    None
}

/// 取る手に対する静的交換評価。
#[must_use]
#[allow(clippy::too_many_lines)]
pub fn see(pos: &Position, mv: Move) -> i32 {
    // YaneuraOu互換: 成りによる価値上昇と駒打ちコストはSEEに含めない。
    // see_ge()と同様に盤上の取り合いのみを評価する。

    let to = mv.to_sq();
    let from = mv.from_sq();
    // Drop logic is handled inline, verify from is None only for drops
    if !mv.is_drop() && from.is_none() {
        return 0; // Invalid move if not drop and no from
    }

    let us = pos.side_to_move();
    let them = us.flip();

    let victim = piece_on(pos, to);
    // 自分の駒を取る手は0を返す（基本生成されないはずだが防御的記述）
    if victim != Piece::NO_PIECE && victim.color() == us {
        return 0;
    }
    // 駒のないマスへの移動で、かつ成りでないなら（ただの移動）、SEEは0
    // ただし、駒打ちはSEEを持つ（持ち駒を失う）ので除外
    if victim == Piece::NO_PIECE && !mv.is_promote() && !mv.is_drop() {
        return 0;
    }

    let moving_piece = if mv.is_drop() {
        // Drop: Create piece from dropped type and side to move
        Piece::make(us, mv.dropped_piece().unwrap())
    } else {
        piece_on(pos, from)
    };

    let mut gains = [0i32; 32];
    let mut depth = 0usize;

    // 初期獲得価値
    // Captures: Value (Victim)
    let initial_gain = if victim == Piece::NO_PIECE { 0 } else { piece_value(victim.piece_type()) };
    gains[depth] = initial_gain;

    let mut current_piece_value = piece_value(moving_piece.piece_type());
    let trace_1a1e = trace_see_1a1e_enabled() && !mv.is_drop() && is_debug_see_1a1e_move(from, to);
    if trace_1a1e {
        eprintln!(
            "DEBUG_SEE_1a1e: victim={:?} initial_gain={} mover_value={}",
            victim.piece_type(),
            gains[depth],
            current_piece_value
        );
    }

    let mut occupied = pos.bitboards().occupied();
    let to_mask = Bitboard::from_square(to);
    occupied = occupied ^ to_mask;

    // For non-drop moves, also toggle the from square
    if !mv.is_drop() {
        let from_mask = Bitboard::from_square(from);
        occupied = occupied ^ from_mask;
    }

    let mut bishop_like = pos.bitboards().pieces_of(PieceType::BISHOP, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::BISHOP, Color::WHITE)
        | pos.bitboards().pieces_of(PieceType::HORSE, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::HORSE, Color::WHITE);
    let mut rook_like = pos.bitboards().pieces_of(PieceType::ROOK, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::ROOK, Color::WHITE)
        | pos.bitboards().pieces_of(PieceType::DRAGON, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::DRAGON, Color::WHITE);
    let mut black_lances = pos.bitboards().pieces_of(PieceType::LANCE, Color::BLACK);
    let mut white_lances = pos.bitboards().pieces_of(PieceType::LANCE, Color::WHITE);

    // For non-drop moves, remove the moving piece from slider sets
    if !mv.is_drop() {
        let from_mask = Bitboard::from_square(from);
        remove_from_slider_sets(
            moving_piece.piece_type(),
            us,
            from_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );
    }
    if victim != Piece::NO_PIECE {
        remove_from_slider_sets(
            victim.piece_type(),
            victim.color(),
            to_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );
    }

    let pinners_black = compute_pinners(pos, Color::WHITE);
    let pinners_white = compute_pinners(pos, Color::BLACK);
    let blockers_black = pos.blockers_for_king(Color::BLACK);
    let blockers_white = pos.blockers_for_king(Color::WHITE);
    let color_occupancies =
        [pos.bitboards().color_pieces(Color::BLACK), pos.bitboards().color_pieces(Color::WHITE)];

    let mut attackers = pos.attackers_to(to, occupied);
    let mut side = them;
    if trace_1a1e {
        let sq_1f = Square::from_usi("1f").expect("square 1f");
        eprintln!(
            "DEBUG_SEE_1a1e: attackers_start={} black_attackers=[{}] white_attackers=[{}]",
            attackers.count(),
            bitboard_to_squares(attackers & color_occupancies[Color::BLACK.to_index()]),
            bitboard_to_squares(attackers & color_occupancies[Color::WHITE.to_index()])
        );
        eprintln!(
            "DEBUG_SEE_1a1e: us={:?} piece_1f={:?} piece_1i={:?}",
            us,
            pos.piece_on(sq_1f),
            pos.piece_on(Square::from_usi("1i").expect("square 1i"))
        );
        eprintln!("DEBUG_SEE_1a1e: position_sfen={}", pos.sfen(None));
        eprintln!("DEBUG_SEE_1a1e: initial_side={side:?}");
    }

    loop {
        attackers = attackers & occupied;
        let mut stm_attackers = attackers & color_occupancies[side.to_index()];
        if trace_1a1e {
            eprintln!(
                "DEBUG_SEE_1a1e: side={:?} stm_attackers=[{}]",
                side,
                bitboard_to_squares(stm_attackers)
            );
        }

        let pinners_of_opponent = if side == Color::BLACK { pinners_white } else { pinners_black };
        if !(pinners_of_opponent & occupied).is_empty() {
            let blockers = if side == Color::BLACK { blockers_black } else { blockers_white };
            stm_attackers = stm_attackers & !blockers;
            if stm_attackers.is_empty() {
                if trace_1a1e {
                    eprintln!(
                        "DEBUG_SEE_1a1e: side={:?} attackers_all_pinned blockers=[{}]",
                        side,
                        bitboard_to_squares(blockers & occupied)
                    );
                }
                break;
            }
        }

        if stm_attackers.is_empty() {
            break;
        }

        let Some((att_sq, att_pt)) = least_valuable_attacker(pos, stm_attackers, side) else {
            break;
        };

        depth += 1;
        if depth >= gains.len() {
            break;
        }

        let prev = gains[depth - 1];
        gains[depth] = current_piece_value - prev;
        if trace_1a1e {
            eprintln!(
                "DEBUG_SEE_1a1e: round={} attacker={:?} attacker_color={:?} attacker_value={} prev_gain={} new_gain={}",
                depth,
                att_pt,
                side,
                piece_value(att_pt),
                prev,
                gains[depth]
            );
        }

        let att_mask = Bitboard::from_square(att_sq);
        occupied = occupied ^ att_mask;
        remove_from_slider_sets(
            att_pt,
            side,
            att_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );
        let xray = xray_attackers(
            to,
            att_sq,
            occupied,
            bishop_like,
            rook_like,
            black_lances,
            white_lances,
        );
        attackers = attackers | xray;
        if trace_1a1e {
            eprintln!("DEBUG_SEE_1a1e: xray_from={} added=[{}]", att_sq, bitboard_to_squares(xray));
        }

        current_piece_value = piece_value(att_pt);
        side = side.flip();
    }

    while depth > 0 {
        let capture = gains[depth];
        let reply = gains[depth - 1];
        let best_reply = (-reply).max(capture);
        gains[depth - 1] = -best_reply;
        depth -= 1;
    }

    if trace_1a1e {
        eprintln!("DEBUG_SEE_1a1e: final_result={}", gains[0]);
    }

    gains[0]
}

/// SEE の閾値比較。
#[must_use]
#[allow(clippy::too_many_lines)]
pub fn see_ge(pos: &Position, mv: Move, threshold: i32) -> bool {
    // YaneuraOu の `Position::see_ge()` 相当の「null-window風」判定で互換性を優先する。
    //
    // - 捕獲だけでなく quiet / drop / 成り にも適用する（探索のSEE pruning用途）。
    // - 成りによる価値上昇（最後になった駒による成り差分）は考慮しない（YaneuraOu互換）。
    // - `occupied = pieces() ^ from ^ to` で pinned piece / x-ray を合わせる（YaneuraOuコメント互換）。

    let to = mv.to_sq();
    let us = pos.side_to_move();
    let trace_this = trace_see_ge_enabled(mv);

    let (from_square, moving_pt) = if mv.is_drop() {
        // Drop Case
        (None, mv.dropped_piece().unwrap())
    } else {
        let from = mv.from_sq();
        let moving_piece = pos.piece_on(from);
        if moving_piece == Piece::NO_PIECE || moving_piece.color() != us {
            return threshold <= 0;
        }
        (Some(from), moving_piece.piece_type())
    };

    // [YaneuraOu Correspondence]:
    // Logic Phase 1: Initial Swap Calculation (Victim - Threshold)
    // Corresponds to YaneuraOu `position.cpp`:
    // `int swap = PieceValue[piece_on(to)] - threshold;`
    //
    // 成りなら価値上昇分を加算する。
    let victim = pos.piece_on(to);
    let victim_value = if victim == Piece::NO_PIECE { 0 } else { piece_value(victim.piece_type()) };

    let mut swap = victim_value - threshold;

    // [YaneuraOu Correspondence]:
    // Check if initial swap is already negative (Early Pruning)
    // `if (swap < 0) return false;`
    if swap < 0 {
        if trace_this {
            println!(
                "info string trace see_ge move={} threshold={} victim_value={} swap_init={} result=false(reason=swap<0)",
                mv.to_usi(),
                threshold,
                victim_value,
                swap
            );
        }
        return false;
    }

    // [YaneuraOu Correspondence]:
    // Logic Phase 2: First Update (Attacker - Swap)
    // Corresponds to YaneuraOu `position.cpp`:
    // `PieceType from_pt = drop ? m.move_dropped_piece() : type_of(piece_on(from));`
    // `swap = PieceValue[from_pt] - swap;`
    swap = piece_value(moving_pt) - swap;

    // [YaneuraOu Correspondence]:
    // Check if updated swap is safe (Early Success)
    // `if (swap <= 0) return true;`
    if swap <= 0 {
        if trace_this {
            println!(
                "info string trace see_ge move={} threshold={} victim_value={} from_value={} swap_after_from={} result=true(reason=swap<=0)",
                mv.to_usi(),
                threshold,
                victim_value,
                piece_value(moving_pt),
                swap
            );
        }
        return true;
    }

    let mut occupied = pos.bitboards().occupied();
    let to_mask = Bitboard::from_square(to);
    occupied = occupied ^ to_mask;
    if let Some(from) = from_square {
        let from_mask = Bitboard::from_square(from);
        occupied = occupied ^ from_mask;
    }

    let mut bishop_like = pos.bitboards().pieces_of(PieceType::BISHOP, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::BISHOP, Color::WHITE)
        | pos.bitboards().pieces_of(PieceType::HORSE, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::HORSE, Color::WHITE);
    let mut rook_like = pos.bitboards().pieces_of(PieceType::ROOK, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::ROOK, Color::WHITE)
        | pos.bitboards().pieces_of(PieceType::DRAGON, Color::BLACK)
        | pos.bitboards().pieces_of(PieceType::DRAGON, Color::WHITE);
    let mut black_lances = pos.bitboards().pieces_of(PieceType::LANCE, Color::BLACK);
    let mut white_lances = pos.bitboards().pieces_of(PieceType::LANCE, Color::WHITE);

    if let Some(from) = from_square {
        let from_piece = piece_on(pos, from);
        let from_mask = Bitboard::from_square(from);
        remove_from_slider_sets(
            from_piece.piece_type(),
            us,
            from_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );
    }
    if victim != Piece::NO_PIECE && victim.color() != us {
        remove_from_slider_sets(
            victim.piece_type(),
            victim.color(),
            to_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );
    }

    let pinners_black = compute_pinners(pos, Color::WHITE);
    let pinners_white = compute_pinners(pos, Color::BLACK);
    let blockers_black = pos.blockers_for_king(Color::BLACK);
    let blockers_white = pos.blockers_for_king(Color::WHITE);
    let color_occupancies =
        [pos.bitboards().color_pieces(Color::BLACK), pos.bitboards().color_pieces(Color::WHITE)];

    let pawns = [
        pos.bitboards().pieces_of(PieceType::PAWN, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::PAWN, Color::WHITE),
    ];
    let lances = [black_lances, white_lances];
    let knights = [
        pos.bitboards().pieces_of(PieceType::KNIGHT, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::KNIGHT, Color::WHITE),
    ];
    let silvers = [
        pos.bitboards().pieces_of(PieceType::SILVER, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::SILVER, Color::WHITE),
    ];
    let gold_like = [
        pos.bitboards().pieces_of(PieceType::GOLD, Color::BLACK)
            | pos.bitboards().pieces_of(PieceType::PRO_PAWN, Color::BLACK)
            | pos.bitboards().pieces_of(PieceType::PRO_LANCE, Color::BLACK)
            | pos.bitboards().pieces_of(PieceType::PRO_KNIGHT, Color::BLACK)
            | pos.bitboards().pieces_of(PieceType::PRO_SILVER, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::GOLD, Color::WHITE)
            | pos.bitboards().pieces_of(PieceType::PRO_PAWN, Color::WHITE)
            | pos.bitboards().pieces_of(PieceType::PRO_LANCE, Color::WHITE)
            | pos.bitboards().pieces_of(PieceType::PRO_KNIGHT, Color::WHITE)
            | pos.bitboards().pieces_of(PieceType::PRO_SILVER, Color::WHITE),
    ];
    let bishops = [
        pos.bitboards().pieces_of(PieceType::BISHOP, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::BISHOP, Color::WHITE),
    ];
    let rooks = [
        pos.bitboards().pieces_of(PieceType::ROOK, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::ROOK, Color::WHITE),
    ];
    let horses = [
        pos.bitboards().pieces_of(PieceType::HORSE, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::HORSE, Color::WHITE),
    ];
    let dragons = [
        pos.bitboards().pieces_of(PieceType::DRAGON, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::DRAGON, Color::WHITE),
    ];
    let kings = [
        pos.bitboards().pieces_of(PieceType::KING, Color::BLACK),
        pos.bitboards().pieces_of(PieceType::KING, Color::WHITE),
    ];
    let attacker_sets = AttackerSets {
        pawns,
        lances,
        knights,
        silvers,
        gold_like,
        bishops,
        rooks,
        horses,
        dragons,
        kings,
    };

    let mut attackers = pos.attackers_to(to, occupied);
    let mut stm = us;
    let mut res = 1i32;

    loop {
        stm = stm.flip();
        attackers = attackers & occupied;

        let mut stm_attackers = attackers & color_occupancies[stm.to_index()];
        if stm_attackers.is_empty() {
            break;
        }

        let pinners_of_opponent = if stm == Color::BLACK { pinners_white } else { pinners_black };
        let mut pinners_present = false;
        let mut blockers = Bitboard::EMPTY;
        if !(pinners_of_opponent & occupied).is_empty() {
            pinners_present = true;
            blockers = if stm == Color::BLACK { blockers_black } else { blockers_white };
            stm_attackers = stm_attackers & !blockers;
            if stm_attackers.is_empty() {
                break;
            }
        }

        res ^= 1;

        let Some(selected) = select_attacker(stm_attackers, stm, &attacker_sets) else {
            break;
        };

        if selected.is_king {
            let pieces_stm = color_occupancies[stm.to_index()];
            let opponent_attackers = attackers & occupied & !pieces_stm;
            let result = if opponent_attackers.is_empty() { res } else { res ^ 1 };
            if trace_this {
                println!(
                    "info string trace see_ge move={} threshold={} king_capture stm={:?} res={} opponent_attackers={} result={}",
                    mv.to_usi(),
                    threshold,
                    stm,
                    res,
                    i32::from(!opponent_attackers.is_empty()),
                    result
                );
            }
            return result != 0;
        }

        if trace_this {
            println!(
                "info string trace see_ge move={} threshold={} step stm={:?} res={} pinners_present={} blockers_count={} select_sq={} selected_is_blocker={} select_value={} swap_before={}",
                mv.to_usi(),
                threshold,
                stm,
                res,
                i32::from(pinners_present),
                blockers.count(),
                selected.sq,
                i32::from(blockers.test(selected.sq)),
                selected.value,
                swap
            );
        }

        swap = selected.value - swap;
        if swap < res {
            if trace_this {
                println!(
                    "info string trace see_ge move={} threshold={} step_result stm={:?} res={} swap_after={} break=true",
                    mv.to_usi(),
                    threshold,
                    stm,
                    res,
                    swap
                );
            }
            break;
        }
        if trace_this {
            println!(
                "info string trace see_ge move={} threshold={} step_result stm={:?} res={} swap_after={} break=false",
                mv.to_usi(),
                threshold,
                stm,
                res,
                swap
            );
        }

        let att_mask = Bitboard::from_square(selected.sq);
        occupied = occupied ^ att_mask;
        remove_from_slider_sets(
            selected.remove_pt,
            stm,
            att_mask,
            &mut bishop_like,
            &mut rook_like,
            &mut black_lances,
            &mut white_lances,
        );

        if !selected.add_xray {
            continue;
        }

        attackers = attackers
            | xray_attackers(
                to,
                selected.sq,
                occupied,
                bishop_like,
                rook_like,
                black_lances,
                white_lances,
            );
    }

    if trace_this {
        println!(
            "info string trace see_ge move={} threshold={} final_res={}",
            mv.to_usi(),
            threshold,
            res
        );
    }
    res != 0
}

impl Position {
    /// 指し手のSEE値を返す（YaneuraOu互換）。
    #[must_use]
    pub fn see(&self, mv: Move) -> i32 {
        see(self, mv)
    }

    /// SEE が閾値以上かを判定する（YaneuraOu互換）。
    #[must_use]
    pub fn see_ge(&self, mv: Move, threshold: i32) -> bool {
        see_ge(self, mv, threshold)
    }
}

#[cfg(test)]
mod tests {
    #![allow(
        clippy::uninlined_format_args,
        clippy::cast_possible_truncation,
        clippy::cast_sign_loss
    )]

    use super::*;
    use crate::board::movegen::{generate_moves, NonEvasions};
    use crate::board::MoveList;

    /// Test that GOLD drops to squares that can be captured fail SEE threshold.
    /// This test verifies YaneuraOu compatibility for check bonus filtering.
    #[test]
    fn test_gold_drop_see_ge_negative() {
        use crate::types::{Color, PieceType};

        // Position from YaneuraOu debug: White to move with Gold in hand
        // GOLD drops at 2g, 3e, 3g, 4g should fail see_ge(mv, -75) because they can be captured.
        let sfen = "lns3knl/3g1gP2/2pp1ps1p/pp3p2B/1r5p1/P1PP5/1PS1PP2P/3K1G1R1/LN4GNL w BSb2p 50";
        let pos = crate::board::position_from_sfen(sfen).expect("valid sfen");

        // White to move, test GOLD drops that give check
        assert_eq!(pos.side_to_move(), Color::WHITE);

        // Test G*2g - this is a drop that can be captured by Black's Rook at 2h
        let to_sq = Square::from_usi("2g").unwrap();
        let mv = Move::make_drop(PieceType::GOLD, to_sq, Color::WHITE);
        let see_value = see(&pos, mv);
        let see_ge_result = see_ge(&pos, mv, -75);

        // YaneuraOu returns see_ge = false for this drop because it can be captured by the Rook
        // This is critical for correct check bonus filtering
        assert!(
            see_value < 0,
            "Expected SEE(G*2g) < 0 (drop can be captured), but got {}",
            see_value
        );
        assert!(
            !see_ge_result,
            "Expected see_ge(G*2g, -75) = false (YaneuraOu compatible), but got true. SEE={}",
            see_value
        );
    }

    #[test]
    #[ignore]
    fn test_1a1e_see_value() {
        // 1i1e局面（ln1g3nl depth 2探索のply=3で1a1eが探索される親局面）
        // ログから取得した正しいSFEN
        let sfen =
            "ln1g3nl/1r3kg2/2psppsp1/p2p2p2/1p5PL/P1PP2P2/1PS1PP3/2G1GS1R1/LN2K2N1 w BPbp 30";
        let pos = crate::board::position_from_sfen(sfen).unwrap();

        // 合法手を生成して1a1eを探す
        let mut list = MoveList::new();
        generate_moves::<NonEvasions>(&pos, &mut list);
        let Some(mv) = list.iter().find(|m| m.to_usi() == "1a1e") else {
            panic!("1a1e not found");
        };

        let see_value = see(&pos, *mv);
        eprintln!("SEE(1a1e) = {}", see_value);
        if see_value >= -78 {
            eprintln!(
                "\n!!! WARNING: SEE value {} is >= -78, but YaneuraOu expects < -78",
                see_value
            );
        }
        assert!(
            see_value < -78,
            "Expected SEE(1a1e) < -78 (YaneuraOu behavior), got {}",
            see_value
        );
    }
}
