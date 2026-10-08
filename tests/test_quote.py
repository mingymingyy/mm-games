import math
import pytest

from games.quote import (INV_COST, N_DICE, TRADERS_PER_QUOTE, MarketMakerGame, Trader, check_quote,
                         fair_value, flow)


def test_fair_value():
    assert fair_value([]) == 10.5
    assert fair_value([6]) == 13.0
    assert fair_value([1, 2]) == 6.5
    assert fair_value([4, 5, 6]) == 15


def test_check_quote():
    assert check_quote(9.5, 11.5, 4) is None
    assert check_quote(10, 14, 4) is None
    assert "above" in check_quote(11, 11, 4)
    assert "wide" in check_quote(8, 13, 4)
    assert "steps" in check_quote(9.3, 11, 4)


def test_flow_informed_only_trade_when_quote_is_wrong():
    informed = [Trader(True, 0.0, "buy")]
    assert flow(informed, 9, 11, 12, 10) == ["sold"]      # true above ask: they lift you
    assert flow(informed, 9, 11, 8, 10) == ["bought"]     # true below bid: they hit you
    for true in (9, 10, 11):                              # inside or on the quote: no trade
        assert flow(informed, 9, 11, true, 10) == ["pass"]


def test_flow_noise_is_price_sensitive_not_informed():
    buyer, seller = Trader(False, 1.5, "buy"), Trader(False, 1.5, "sell")
    # within tolerance of fair (10): both trade, whatever the true value
    assert flow([buyer, seller], 9, 11, 3, 10) == ["sold", "bought"]
    # 2 wide on each side is beyond their 1.5 tolerance: both walk away
    assert flow([buyer, seller], 8, 12, 3, 10) == ["pass", "pass"]
    # skewing down attracts the buyer and repels the seller
    assert flow([buyer, seller], 8, 11, 3, 10) == ["sold", "pass"]


def test_pnl_and_inventory_accounting():
    g = MarketMakerGame(rounds=1, seed=3)
    for _ in range(N_DICE):
        fv = g.fair
        g.quote(fv - 2, fv + 2)
    assert g.settled and g.done
    s = g.summaries[0]
    expected = sum((f.price - g.true) if f.side == "sold" else (g.true - f.price) for f in g.fills)
    assert math.isclose(s.pnl, expected)
    assert math.isclose(s.inv_charge, sum(INV_COST * abs(q.position_after) for q in g.quotes))
    # quoting centred at max width every time is exactly the benchmark
    assert math.isclose(s.score, s.bench_score)
    bd = g.breakdown()
    assert math.isclose(bd["pnl"], bd["from_noise"] + bd["from_informed"])
    assert math.isclose(bd["score"], bd["pnl"] - bd["inv_charge"])


def test_position_tracks_fills():
    g = MarketMakerGame(rounds=1, seed=8)
    g.quote(9.5, 11.5)
    bought = sum(f.side == "bought" for f in g.fills)
    sold = sum(f.side == "sold" for f in g.fills)
    assert g.position == bought - sold


def test_all_informed_never_lose_on_a_single_trade():
    # informed traders only trade when you're wrong, so every fill loses (or breaks even)
    g = MarketMakerGame(rounds=20, informed_share=1.0, seed=1)
    while True:
        while not g.settled:
            g.quote(g.fair - 1, g.fair + 1)
        if g.done:
            break
        g.next_round()
    assert all(f.informed and f.pnl < 0 for f in g.fills)


def _play(width, share, rounds=600, seed=5):
    g = MarketMakerGame(rounds=rounds, informed_share=share, max_width=6, seed=seed)
    while True:
        while not g.settled:
            g.quote(g.fair - width / 2, g.fair + width / 2)
        if g.done:
            return g.breakdown()
        g.next_round()


def test_width_tradeoff():
    # too tight earns little from noise; too wide scares noise traders away
    assert _play(3, 0.0)["from_noise"] > _play(1, 0.0)["from_noise"] > 0
    assert _play(3, 0.0)["from_noise"] > _play(6, 0.0)["from_noise"]
    # informed traders punish tight quotes
    assert _play(1, 0.35)["score"] < _play(4, 0.35)["score"]


def test_invalid_quote_and_round_flow():
    g = MarketMakerGame(rounds=2, seed=0)
    with pytest.raises(ValueError):
        g.quote(12, 10)
    with pytest.raises(RuntimeError):
        g.next_round()                         # can't skip ahead mid-round
    for _ in range(N_DICE):
        g.quote(g.fair - 1, g.fair + 1)
    with pytest.raises(RuntimeError):
        g.quote(9, 11)                         # round already settled
    g.next_round()
    assert g.round_no == 2 and g.stage == 0 and g.position == 0
    for _ in range(N_DICE):
        g.quote(g.fair - 1, g.fair + 1)
    assert g.done and len(g.summaries) == 2
    assert len(g.quotes) == 2 * N_DICE


def test_shown_dice_by_stage():
    g = MarketMakerGame(rounds=1, seed=4)
    assert g.shown == []
    g.quote(9.5, 11.5)
    assert g.shown == g.dice[:1] and g.fair == fair_value(g.dice[:1])
    g.quote(g.fair - 1, g.fair + 1)
    g.quote(g.fair - 1, g.fair + 1)
    assert g.shown == g.dice


def test_trader_count_and_mix():
    g = MarketMakerGame(rounds=1, informed_share=0.4, seed=2)
    assert len(g.traders) == N_DICE and all(len(s) == TRADERS_PER_QUOTE for s in g.traders)
    traders = [t for seed in range(1500)
               for stage in MarketMakerGame(rounds=1, informed_share=0.4, seed=seed).traders
               for t in stage]
    share = sum(t.informed for t in traders) / len(traders)
    assert 0.37 < share < 0.43
