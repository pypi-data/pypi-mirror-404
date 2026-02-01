use super::types::{MoveError, PackedPiece};
use super::{Position, MINOR_PIECE_TYPES};
use crate::board::eval_list::{DirtyEvalPiece, PIECE_NUMBER_NB};
use crate::board::material;
use crate::board::zobrist::Zobrist;
use crate::types::{Bitboard, HandPiece, Move, Piece, PieceType};

impl Position {
    /// 指し手を適用
    #[allow(clippy::too_many_lines, clippy::cast_possible_truncation, clippy::cognitive_complexity)]
    pub fn do_move(&mut self, mv: Move) {
        debug_assert!(self.is_legal(mv), "do_move expects a legal move");
        let gives_check = self.gives_check(mv);
        self.do_move_with_gives_check(mv, gives_check);
    }

    /// 指し手を適用（王手判定を外部で計算済みの場合）
    #[allow(clippy::too_many_lines, clippy::cast_possible_truncation, clippy::cognitive_complexity)]
    pub fn do_move_with_gives_check(&mut self, mv: Move, gives_check: bool) {
        debug_assert!(self.is_legal(mv), "do_move expects a legal move");
        let current_state_snapshot = {
            let stack = self.state_stack();
            stack.current().clone()
        };
        self.sync_caches_from_state(&current_state_snapshot);

        let prev_continuous_check = current_state_snapshot.continuous_check;
        let prev_plies_from_null = current_state_snapshot.plies_from_null;
        let prev_material_value = current_state_snapshot.material_value;

        let state_idx = {
            let mut stack = self.state_stack_mut();
            let state_idx = stack.push_for_move();
            let state = stack.get_mut(state_idx);
            state.captured = PackedPiece::EMPTY;
            state.dirty_eval_piece = DirtyEvalPiece::default();
            state_idx
        };

        let mut dirty_eval_piece = DirtyEvalPiece::default();
        let mut captured = PackedPiece::EMPTY;
        let mut material_diff = 0;
        let last_moved_piece_type = if mv.is_drop() {
            // 駒打ち処理
            let to = mv.to_sq();
            let piece_type =
                mv.dropped_piece().expect("drop move must include a dropped piece type");
            let color = self.side_to_move;

            debug_assert!(self.board.get(to).is_empty(), "drop destination must be empty");
            let hand_piece = HandPiece::from_piece_type(piece_type)
                .expect("drop move must use a hand piece type");
            debug_assert!(
                self.hands[color.to_index()].count(hand_piece) > 0,
                "drop move must have a matching hand piece"
            );

            // 駒を配置
            let packed = PackedPiece::new(piece_type, color, false);
            self.board.set(to, packed);

            // ビットボードを更新
            self.bitboards.set(to, Piece::make(color, piece_type));

            // PieceListを更新（駒打ち）
            self.piece_list.add_piece(color, piece_type, to);

            let new_piece = Piece::make(color, piece_type);

            // EvalList更新（駒打ち）
            let piece_no = self.piece_no_of_hand(color, piece_type);
            debug_assert!(
                piece_no != PIECE_NUMBER_NB,
                "drop move expects valid piece number: {piece_type:?}"
            );
            dirty_eval_piece.dirty_num = 1;
            dirty_eval_piece.piece_no[0] = piece_no;
            dirty_eval_piece.changed_piece[0].old_piece = self.eval_list.bona_piece(piece_no);
            self.eval_list.put_piece_on_board(piece_no, to, new_piece);
            dirty_eval_piece.changed_piece[0].new_piece = self.eval_list.bona_piece(piece_no);

            // 持ち駒を減らす
            self.hands[color.to_index()].sub(hand_piece, 1);

            // Zobrist更新: 駒打ち
            // 1. 打った駒を盤上に追加
            self.board_key ^= Zobrist::psq(to, Piece::make(color, piece_type));
            if piece_type == PieceType::PAWN {
                self.pawn_key ^= Zobrist::psq(to, Piece::make(color, piece_type));
            } else {
                self.non_pawn_key[color.to_index()] ^=
                    Zobrist::psq(to, Piece::make(color, piece_type));
            }
            if MINOR_PIECE_TYPES.contains(&piece_type) {
                self.minor_piece_key ^= Zobrist::psq(to, Piece::make(color, piece_type));
            }
            self.material_key.add(Zobrist::material(Piece::make(color, piece_type)));
            // 2. 持ち駒の数を更新 (n → n-1)
            self.hand_key.sub(Zobrist::hand(color, piece_type, 1));
            piece_type
        } else {
            // 通常移動または成り
            let from = mv.from_sq();
            let to = mv.to_sq();

            // 移動元の駒を取得
            let moved_piece = self.board.get(from);
            debug_assert!(!moved_piece.is_empty(), "move must originate from a piece");
            // 移動元の駒が正しい手番かチェック
            debug_assert!(
                moved_piece.color() == self.side_to_move,
                "move must be from the side to move"
            );

            // 移動先の駒を取得（捕獲判定）
            let captured_piece = self.board.get(to);
            if !captured_piece.is_empty() {
                // 相手の駒かチェック
                debug_assert!(
                    captured_piece.color() != self.side_to_move,
                    "capture must target opponent piece"
                );
                captured = captured_piece;
                material_diff +=
                    material::capture_material_delta(self.side_to_move, captured_piece.to_piece());

                // ビットボードから削除
                self.bitboards.clear(to, captured_piece.to_piece());

                // PieceListから削除（捕獲）
                // 成り駒の場合も正しい駒種を取得するため to_piece().piece_type() を使用
                self.piece_list.remove_piece(
                    captured_piece.color(),
                    captured_piece.to_piece().piece_type(),
                    to,
                );

                // 持ち駒に追加
                let captured_hand_piece =
                    HandPiece::from_piece_type(captured_piece.piece_type().demote())
                        .expect("captured piece must map to hand piece");
                let before_count =
                    self.hands[self.side_to_move.to_index()].count(captured_hand_piece);

                // EvalList更新（捕獲された駒の手駒移動）
                let captured_piece_no = self.piece_no_of_square(to);
                debug_assert!(
                    captured_piece_no != PIECE_NUMBER_NB,
                    "capture expects valid piece number: {to:?}"
                );
                dirty_eval_piece.dirty_num = 2;
                dirty_eval_piece.piece_no[1] = captured_piece_no;
                dirty_eval_piece.changed_piece[1].old_piece =
                    self.eval_list.bona_piece(captured_piece_no);
                self.eval_list.put_piece_on_hand(
                    captured_piece_no,
                    self.side_to_move,
                    captured_piece.piece_type().demote(),
                    before_count as usize,
                );
                dirty_eval_piece.changed_piece[1].new_piece =
                    self.eval_list.bona_piece(captured_piece_no);

                self.hands[self.side_to_move.to_index()].add(captured_hand_piece, 1);

                let captured_piece = captured_piece.to_piece();
                if captured_piece.piece_type() == PieceType::PAWN {
                    self.pawn_key ^= Zobrist::psq(to, captured_piece);
                } else {
                    self.non_pawn_key[captured_piece.color().to_index()] ^=
                        Zobrist::psq(to, captured_piece);
                }
                if MINOR_PIECE_TYPES.contains(&captured_piece.piece_type()) {
                    self.minor_piece_key ^= Zobrist::psq(to, captured_piece);
                }
                self.material_key.sub(Zobrist::material(captured_piece));
            }

            // EvalList更新（移動した駒）
            let moved_piece_no = self.piece_no_of_square(from);

            // 移動元から駒を取り除く
            self.board.set(from, PackedPiece::EMPTY);
            self.bitboards.clear(from, moved_piece.to_piece());

            // 移動先に駒を配置
            let new_piece = if mv.is_promote() {
                // 成り処理
                PackedPiece::new(moved_piece.piece_type(), moved_piece.color(), true)
            } else {
                moved_piece
            };
            if mv.is_promote() {
                material_diff += material::promotion_material_delta(
                    self.side_to_move,
                    moved_piece.to_piece().piece_type(),
                    new_piece.to_piece().piece_type(),
                );
            }
            self.board.set(to, new_piece);
            self.bitboards.set(to, new_piece.to_piece());

            if moved_piece.to_piece().piece_type() == PieceType::KING {
                self.king_square[self.side_to_move.to_index()] = to;
            }

            debug_assert!(
                moved_piece_no != PIECE_NUMBER_NB,
                "move expects valid piece number: {from:?}"
            );
            if dirty_eval_piece.dirty_num == 0 {
                dirty_eval_piece.dirty_num = 1;
            }
            dirty_eval_piece.piece_no[0] = moved_piece_no;
            dirty_eval_piece.changed_piece[0].old_piece = self.eval_list.bona_piece(moved_piece_no);
            self.eval_list.put_piece_on_board(moved_piece_no, to, new_piece.to_piece());
            dirty_eval_piece.changed_piece[0].new_piece = self.eval_list.bona_piece(moved_piece_no);

            // PieceListを更新（移動または成り）
            let color = moved_piece.color();
            if mv.is_promote() {
                // 成りの場合：元の駒種を削除し、成った駒種を追加
                // 注意: PieceListにはPiece::piece_type()の値（成り駒の場合はPROM_SILVER等）を格納する
                let old_piece_type = moved_piece.to_piece().piece_type(); // 元の駒（生駒）
                let new_piece_type = new_piece.to_piece().piece_type(); // 成り駒

                self.piece_list.remove_piece(color, old_piece_type, from);
                self.piece_list.add_piece(color, new_piece_type, to);
            } else {
                // 通常移動の場合：駒を移動
                let piece_type = moved_piece.to_piece().piece_type();
                self.piece_list.move_piece(color, piece_type, from, to);
            }

            // Zobrist更新: 通常移動または成り
            // 1. 移動元の駒を削除
            self.board_key ^= Zobrist::psq(from, moved_piece.to_piece());
            let moved_piece_before = moved_piece.to_piece();
            let moved_pt_before = moved_piece_before.piece_type();

            // 2. 捕獲があった場合、捕獲された駒を削除し、持ち駒を更新
            if !captured_piece.is_empty() {
                self.board_key ^= Zobrist::psq(to, captured_piece.to_piece());

                // 持ち駒の更新 (n-1 → n)
                self.hand_key.add(Zobrist::hand(
                    self.side_to_move,
                    captured_piece.piece_type().demote(),
                    1,
                ));
            }

            // 3. 移動先に駒を追加（成りの場合は成り駒）
            self.board_key ^= Zobrist::psq(to, new_piece.to_piece());

            if moved_pt_before == PieceType::PAWN {
                self.pawn_key ^= Zobrist::psq(from, moved_piece_before);
                if mv.is_promote() {
                    let promoted_piece = new_piece.to_piece();
                    self.non_pawn_key[color.to_index()] ^= Zobrist::psq(to, promoted_piece);
                    if MINOR_PIECE_TYPES.contains(&promoted_piece.piece_type()) {
                        self.minor_piece_key ^= Zobrist::psq(to, promoted_piece);
                    }
                    self.material_key.sub(Zobrist::material(moved_piece_before));
                    self.material_key.add(Zobrist::material(promoted_piece));
                } else {
                    self.pawn_key ^= Zobrist::psq(to, moved_piece_before);
                }
            } else {
                self.non_pawn_key[color.to_index()] ^= Zobrist::psq(from, moved_piece_before);
                if MINOR_PIECE_TYPES.contains(&moved_pt_before) {
                    self.minor_piece_key ^= Zobrist::psq(from, moved_piece_before);
                }
                if mv.is_promote() {
                    let promoted_piece = new_piece.to_piece();
                    self.non_pawn_key[color.to_index()] ^= Zobrist::psq(to, promoted_piece);
                    if MINOR_PIECE_TYPES.contains(&promoted_piece.piece_type()) {
                        self.minor_piece_key ^= Zobrist::psq(to, promoted_piece);
                    }
                    self.material_key.sub(Zobrist::material(moved_piece_before));
                    self.material_key.add(Zobrist::material(promoted_piece));
                } else {
                    self.non_pawn_key[color.to_index()] ^= Zobrist::psq(to, moved_piece_before);
                    if MINOR_PIECE_TYPES.contains(&moved_pt_before) {
                        self.minor_piece_key ^= Zobrist::psq(to, moved_piece_before);
                    }
                }
            }
            moved_piece.to_piece().piece_type()
        };

        // 手番を反転し、手数を進め、Zobristを更新
        self.side_to_move = self.side_to_move.flip();
        self.ply += 1;
        self.board_key ^= Zobrist::side();
        self.zobrist = self.board_key ^ self.hand_key;

        // continuous_check と plies_from_null の更新
        let moved_color = self.side_to_move.flip();
        let mut new_continuous_check = prev_continuous_check;
        let moved_idx = moved_color.to_index();
        new_continuous_check[moved_idx] =
            if gives_check { prev_continuous_check[moved_idx] + 2 } else { 0 };
        let new_plies_from_null = prev_plies_from_null + 1;

        let state_snapshot = {
            let mut stack = self.state_stack_mut();
            {
                let state = stack.get_mut(state_idx);
                state.dirty_eval_piece = dirty_eval_piece;
                state.captured = captured;
                state.last_move = mv;
                state.last_moved_piece_type = last_moved_piece_type;
                state.plies_from_null = new_plies_from_null;
                state.board_key = self.board_key;
                state.hand_key = self.hand_key;
                state.pawn_key = self.pawn_key;
                state.minor_piece_key = self.minor_piece_key;
                state.non_pawn_key = self.non_pawn_key;
                state.material_key = self.material_key;
                state.material_value = prev_material_value + material_diff;
                state.hand = self.hands[self.side_to_move.to_index()];
                state.continuous_check = new_continuous_check;

                self.compute_caches_for_state_no_checkers(state);
                state.checkers = if gives_check {
                    self.compute_checkers_for(self.side_to_move)
                } else {
                    Bitboard::EMPTY
                };
            }

            let rep_info = self.compute_repetition_info(&stack, state_idx, new_plies_from_null);
            let state = stack.get_mut(state_idx);
            state.repetition_counter = rep_info.counter;
            state.repetition_distance = rep_info.distance;
            state.repetition_times = rep_info.times;
            state.repetition_type = rep_info.rep_type;

            state.clone()
        };
        self.sync_caches_from_state(&state_snapshot);
        self.st_index = state_idx;
    }

    /// 指し手を巻き戻す
    pub fn undo_move(&mut self, mv: Move) -> Result<(), MoveError> {
        // StateStackから前の状態を取得
        let (state, current_state, current_index) = {
            let mut stack = self.state_stack_mut();
            let prev_idx = stack.pop().ok_or(MoveError::StackUnderflow)?;
            let state = stack.get(prev_idx).clone();
            let current_index = stack.current_index();
            let current_state = stack.get(current_index).clone();
            (state, current_state, current_index)
        };
        self.st_index = current_index;

        // Zobristを復元（現局面のStateから復元）
        self.board_key = current_state.board_key;
        self.hand_key = current_state.hand_key;
        self.pawn_key = current_state.pawn_key;
        self.minor_piece_key = current_state.minor_piece_key;
        self.non_pawn_key = current_state.non_pawn_key;
        self.material_key = current_state.material_key;
        self.zobrist = self.board_key ^ self.hand_key;

        // 手番を反転（元に戻す）
        self.side_to_move = self.side_to_move.flip();
        self.ply -= 1;

        if mv.is_drop() {
            // 駒打ちの巻き戻し
            let to = mv.to_sq();
            let piece_type = mv.dropped_piece().ok_or(MoveError::NoStateInfo)?;
            let color = self.side_to_move; // 元の手番
            let hand_piece =
                HandPiece::from_piece_type(piece_type).expect("dropped piece must map to hand");
            let hand_count = self.hands[color.to_index()].count(hand_piece);
            let piece_no = self.piece_no_of_square(to);
            debug_assert!(
                piece_no != PIECE_NUMBER_NB,
                "undo drop expects valid piece number: {to:?}"
            );
            self.eval_list.put_piece_on_hand(piece_no, color, piece_type, hand_count as usize);

            // 打った駒を盤面から取り除く
            self.board.set(to, PackedPiece::EMPTY);
            self.bitboards.clear(to, Piece::make(color, piece_type));

            // PieceListから削除（駒打ちundo）
            self.piece_list.remove_piece(color, piece_type, to);

            // 持ち駒に戻す
            self.hands[color.to_index()].add(hand_piece, 1);
        } else {
            // 通常移動または成りの巻き戻し
            let from = mv.from_sq();
            let to = mv.to_sq();
            let moved_piece_no = self.piece_no_of_square(to);
            debug_assert!(
                moved_piece_no != PIECE_NUMBER_NB,
                "undo move expects valid piece number: {to:?}"
            );

            // 移動先の駒を取得（現在の駒）
            let current_piece = self.board.get(to);

            // 移動元の駒を復元（成りの場合は元に戻す）
            let original_piece = if mv.is_promote() {
                // 成り駒を元に戻す
                // to_piece().piece_type() で成り駒を含む正しい駒種を取得してから demote()
                PackedPiece::new(
                    current_piece.to_piece().piece_type().demote(),
                    current_piece.color(),
                    false,
                )
            } else {
                current_piece
            };

            // 移動先から駒を取り除く
            self.board.set(to, PackedPiece::EMPTY);
            self.bitboards.clear(to, current_piece.to_piece());

            // 移動元に駒を戻す
            self.board.set(from, original_piece);
            self.bitboards.set(from, original_piece.to_piece());

            // PieceListを復元（移動または成りのundo）
            let color = current_piece.color();
            if original_piece.to_piece().piece_type() == PieceType::KING {
                self.king_square[color.to_index()] = from;
            }
            let _restored_piece = if mv.is_promote() {
                // 成りのundo: 成った駒種を削除し、元の駒種を追加
                // 成り駒の駒種を正しく取得する
                let promoted_piece_type = current_piece.to_piece().piece_type();
                // 成りフラグが false なので piece_type() でも問題ないが、一貫性のため to_piece() を使用
                let original_piece_type = original_piece.to_piece().piece_type();

                self.piece_list.remove_piece(color, promoted_piece_type, to);
                self.piece_list.add_piece(color, original_piece_type, from);
                Piece::make(color, original_piece_type)
            } else {
                // 通常移動のundo: 駒を移動元に戻す
                // 成り駒の場合も正しい駒種を取得するため to_piece().piece_type() を使用
                let piece_type = current_piece.to_piece().piece_type();
                self.piece_list.move_piece(color, piece_type, to, from);
                current_piece.to_piece()
            };

            // 捕獲があった場合、捕獲された駒を復元
            if !state.captured.is_empty() {
                // 捕獲された駒を盤面に戻す
                self.board.set(to, state.captured);
                self.bitboards.set(to, state.captured.to_piece());

                // PieceListに追加（捕獲undo）
                // 成り駒の場合も正しい駒種を取得するため to_piece().piece_type() を使用
                self.piece_list.add_piece(
                    state.captured.color(),
                    state.captured.to_piece().piece_type(),
                    to,
                );

                // 持ち駒から取り除く
                let hand_piece = HandPiece::from_piece_type(state.captured.piece_type().demote())
                    .expect("captured piece must map to hand");
                let captured_piece_no =
                    self.piece_no_of_hand(self.side_to_move, state.captured.piece_type().demote());
                debug_assert!(
                    captured_piece_no != PIECE_NUMBER_NB,
                    "undo capture expects valid piece number"
                );
                self.eval_list.put_piece_on_board(captured_piece_no, to, state.captured.to_piece());
                self.hands[self.side_to_move.to_index()].sub(hand_piece, 1);
            }
            self.eval_list.put_piece_on_board(moved_piece_no, from, original_piece.to_piece());
        }

        // StateStackの現在値からキャッシュを復元
        self.checkers_cache = current_state.checkers;
        self.pinners_cache = current_state.pinners;
        self.blockers_for_king = current_state.blockers_for_king;
        self.check_squares_cache = current_state.check_squares;

        Ok(())
    }

    /// Null move（手を指さずに手番だけを反転）を適用する。
    ///
    /// 盤面の駒配置や持ち駒は変化させず、Zobrist手番フラグとキャッシュのみ更新する。
    pub fn do_null_move(&mut self) -> Result<(), MoveError> {
        debug_assert!(self.checkers_cache.is_empty(), "null move must not be in check");

        // 新しい状態を積む
        let state_idx = {
            let mut stack = self.state_stack_mut();
            stack.push_clone_from_prev()
        };

        // 手番を反転し、手数を進め、Zobristを更新
        self.side_to_move = self.side_to_move.flip();
        self.ply += 1;
        self.board_key ^= Zobrist::side();
        self.zobrist = self.board_key ^ self.hand_key;

        let prev_continuous_check = {
            let stack = self.state_stack();
            stack.get(state_idx).continuous_check
        };
        debug_assert!(
            prev_continuous_check[self.side_to_move.to_index()] == 0,
            "null move must not follow a continuous check for side to move"
        );
        let mut new_continuous_check = prev_continuous_check;
        let prev_side = self.side_to_move.flip();
        new_continuous_check[prev_side.to_index()] = 0;

        let state_snapshot = {
            let mut stack = self.state_stack_mut();
            let state = stack.get_mut(state_idx);
            // Null move 直後は plies_from_null を 0 にする
            state.plies_from_null = 0;
            state.board_key = self.board_key;
            state.hand_key = self.hand_key;
            state.pawn_key = self.pawn_key;
            state.minor_piece_key = self.minor_piece_key;
            state.non_pawn_key = self.non_pawn_key;
            state.material_key = self.material_key;
            state.hand = self.hands[self.side_to_move.to_index()];

            // null moveでは盤面が変わらないため、王手駒は空扱いのままチェック情報のみ更新する
            state.checkers = Bitboard::EMPTY;
            state.check_squares = self.compute_check_squares();
            state.pinners = self.pinners_cache;
            state.blockers_for_king = self.blockers_for_king;
            state.continuous_check = new_continuous_check;
            state.captured = PackedPiece::EMPTY;

            state.repetition_counter = 0;
            state.repetition_distance = 0;
            state.repetition_times = 0;
            state.repetition_type = crate::types::RepetitionState::None;

            state.clone()
        };

        self.sync_caches_from_state(&state_snapshot);
        self.st_index = state_idx;
        Ok(())
    }

    /// Null move を巻き戻す。
    pub fn undo_null_move(&mut self) -> Result<(), MoveError> {
        // 手番と手数、Zobrist手番フラグを元に戻す
        if self.ply == 0 {
            return Err(MoveError::StackUnderflow);
        }
        self.side_to_move = self.side_to_move.flip();
        self.ply -= 1;

        // スタックをポップ
        let (current_state, current_index) = {
            let mut stack = self.state_stack_mut();
            let _ = stack.pop().ok_or(MoveError::StackUnderflow)?;
            let current_index = stack.current_index();
            let current_state = stack.get(current_index).clone();
            (current_state, current_index)
        };
        self.st_index = current_index;

        // 現在のStateからキャッシュを復元
        self.checkers_cache = current_state.checkers;
        self.pinners_cache = current_state.pinners;
        self.blockers_for_king = current_state.blockers_for_king;
        self.check_squares_cache = current_state.check_squares;
        self.board_key = current_state.board_key;
        self.hand_key = current_state.hand_key;
        self.pawn_key = current_state.pawn_key;
        self.minor_piece_key = current_state.minor_piece_key;
        self.non_pawn_key = current_state.non_pawn_key;
        self.material_key = current_state.material_key;
        self.zobrist = self.board_key ^ self.hand_key;

        Ok(())
    }
}
