#[test]
// 基本局面のSFEN往復が成立しZobristも一致するかを確認
fn sfen_roundtrip_basic_positions() {
    let cases = [
        ("startpos", "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"),
        ("after_76fu", "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2"),
        (
            "bench_opening",
            "lnsgkgsnl/1r7/p1ppp1bpp/1p3pp2/7P1/2P6/PP1PPPP1P/1B3S1R1/LNSGKG1NL b - 9",
        ),
        (
            "bench_midgame1",
            "l4S2l/4g1gs1/5p1p1/pr2N1pkp/4Gn3/PP3PPPP/2GPP4/1K7/L3r+s2L w BS2N5Pb 1",
        ),
    ];

    for (name, sfen) in cases {
        let pos = crate::board::position_from_sfen(sfen)
            .unwrap_or_else(|e| panic!("Failed to parse SFEN for {name}: {e:?}\nSFEN: {sfen}"));
        let generated_sfen = pos.sfen(None);
        assert_eq!(generated_sfen, sfen, "SFEN roundtrip failed for {name}");

        let pos2 = crate::board::position_from_sfen(&generated_sfen)
            .unwrap_or_else(|e| panic!("Failed to parse generated SFEN for {name}: {e:?}"));

        assert_eq!(pos2.sfen(None), sfen, "Second roundtrip failed for {name}");
        assert_eq!(pos.key(), pos2.key(), "Zobrist hash mismatch for {name}");
    }
}

#[test]
// 持ち駒付きSFENの往復が正しく行えるか確認
fn sfen_roundtrip_with_pieces_in_hand() {
    let test_cases = [
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b P 1",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b RBG2S2N2L2P 1",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w rbg2s2n2l2p 1",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b RBrbp 1",
    ];

    for sfen in test_cases {
        let pos = crate::board::position_from_sfen(sfen).expect("Valid SFEN should parse");
        let generated = pos.sfen(None);
        let pos2 =
            crate::board::position_from_sfen(&generated).expect("Generated SFEN should parse");
        assert_eq!(pos2.sfen(None), generated, "Roundtrip with hand pieces failed");
    }
}

#[test]
// 手数フィールドが往復で保持されるかを確認
fn sfen_roundtrip_preserves_ply() {
    let ply_cases = [
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 2",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 100",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 999",
    ];

    for sfen in ply_cases {
        let pos = crate::board::position_from_sfen(sfen).expect("Valid SFEN should parse");
        assert_eq!(pos.sfen(None), sfen, "SFEN should roundtrip with ply");
    }
}
