import itertools
import math
import random

from games.cards import CardGame, build_deck, kelly, odds
from games.fruit import Bag, Event, FruitGame, true_value


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
    assert math.isclose(g.final_score, g.raw_profit * g.first_click_accuracy)
    assert g.trade("buy", now=500.0) is None


def test_bags_stay_in_bounds():
    g = FruitGame(duration_s=10_000, seed=3, now=0.0)
    for t in range(0, 10_000, 7):
        g.tick(float(t))
        for b in g.bags:
            assert 3 <= b.apples <= 12 and 3 <= b.oranges <= 12


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
