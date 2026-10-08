import itertools
import math
import random

from games.cards import CardGame, build_deck, kelly, odds
import pytest

from games.fruit import CLICK_DECAY, Bag, Event, FruitGame, true_value


def test_value_and_events():
    bags = [Bag(3, 4), Bag(5, 6)]
    assert true_value(bags) == 8 * 10
    assert true_value(bags, Event("inflation")) == 160
    assert true_value(bags, Event("deflation")) == 40
    assert true_value(bags, Event("nullify", bag=0, fruit="apples")) == 5 * 10
    assert true_value(bags, Event("nullify", bag=1, fruit="oranges")) == 8 * 4


def test_fruit_pnl_and_scoring():
    g = FruitGame(duration_s=120, seed=1, now=0.0)
    v = g.value
    tr = g.trade("buy", now=1.0)
    assert tr.pnl == v - g.ask
    g.trade("sell", now=1.5)  # same market: not counted for first click
    assert len(g.first_trade_ok) == 1
    g.trade("buy", now=25.0)  # bags must have updated by 20s
    assert g.market_id >= 2 and len(g.first_trade_ok) == 2
    assert math.isclose(g.final_score, sum(t.pnl * t.weight for t in g.trades))
    assert g.trade("buy", now=500.0) is None


@pytest.mark.parametrize("bag_max", [10, 12, 25])
def test_bags_stay_in_bounds(bag_max):
    g = FruitGame(duration_s=10_000, seed=3, now=0.0, bag_max=bag_max)
    for t in range(0, 10_000, 7):
        g.tick(float(t))
        for b in g.bags:
            assert 3 <= b.apples <= bag_max and 3 <= b.oranges <= bag_max


def test_bag_max_out_of_range():
    for bad in (9, 26):
        with pytest.raises(ValueError):
            FruitGame(bag_max=bad, now=0.0)


def test_click_decay_per_market():
    g = FruitGame(duration_s=120, seed=1, now=0.0)
    trades = [g.trade("buy", now=1.0 + i * 0.1) for i in range(3)]
    assert [t.weight for t in trades] == [1.0, CLICK_DECAY, CLICK_DECAY ** 2]
    assert math.isclose(trades[2].scored_pnl, trades[2].pnl * CLICK_DECAY ** 2)
    nxt = g.trade("buy", now=25.0)  # new market: weight starts again at 100%
    assert nxt.market_id != trades[0].market_id and nxt.weight == 1.0


def test_wrong_first_click_is_not_cancelled_by_recovery():
    # Lose 10 on the first click, then win 10 on the second: net score is negative.
    g = FruitGame(duration_s=120, seed=1, now=0.0)
    g.bid, g.ask = round(g.value) + 10, round(g.value) + 12
    lose = g.trade("buy", now=1.0)
    g.bid, g.ask = round(g.value) + 10, round(g.value) + 12
    win = g.trade("sell", now=1.1)
    assert lose.pnl < 0 < win.pnl
    assert g.final_score < 0 and g.raw_profit >= g.final_score


def test_kelly_brute_force():
    for p, q in [(0.6, 0.3), (0.7, 0.2), (0.5, 0.45)]:
        fs = [i / 10000 for i in range(9999)]
        best = max(fs, key=lambda f: p * math.log(1 + f) + q * math.log(1 - f))
        assert abs(best - kelly(p, q)) < 1e-3


def test_odds_count_remaining():
    deck = build_deck(1, True)
    rem = [c for c in deck if c[0] != 7]
    hi, lo, eq = odds(7, rem)
    assert (hi, lo, eq) == (7 / 12, 5 / 12, 0)


def test_card_game_full_run():
    rng = random.Random(0)
    for suits, ace in itertools.product([1, 2, 3, 4], [True, False]):
        g = CardGame(suits, ace, 1000, seed=rng.randint(0, 999))
        n = 0
        while not g.done:
            side, k = g.hint()
            g.play(side or "skip", int(g.bankroll * k))  # play perfect Kelly
            n += 1
        sc = g.score()
        assert sc["decision_quality"] in (0.0, 1.0) or sc["decision_quality"] == 1.0
        assert sc["sizing_efficiency"] > 0.9
        assert n == 13 * suits - 1 or g.bankrupt
        assert 0 <= sc["total"] <= 13
