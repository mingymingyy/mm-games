"""Fruit Market game logic (no Streamlit here, so it can be unit-tested).

Value = (total apples across both bags) x (total oranges across both bags).
Each bag round gets one bid/ask, held for the whole round. The quote is always
slightly mispriced so that exactly one side makes money: either value > ask
(buy) or value < bid (sell), never value inside the spread. Each trade is one
unit, marked instantly at true value.

Click decay: within one market, each click counts CLICK_DECAY times the one
before it (1, 0.85, 0.7225, ...). A wrong first click is scored at full weight,
and any later clicks that try to win it back count for less.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field

START_MIN, START_MAX = 3, 8      # fresh bag contents per fruit
GROW_MIN, GROW_MAX = 0, 3        # fruit added per update
BAG_MAX = 12                     # default cap: above this, the bag resets
BAG_MAX_MIN, BAG_MAX_MAX = 10, 25  # range the player can choose from
ROUND_S = 15                     # each bag round (one quote) lasts this long
SPREAD_PCT = 0.02                # ask - bid, as a fraction of value (min 1)
EDGE_MIN, EDGE_MAX = 0.01, 0.05  # gap from value to the near side of the quote (min 1)
EVENT_PROB = 0.3                 # chance a bag update triggers an event
CLICK_DECAY = 0.85               # each click in a market is worth this x the previous


@dataclass
class Bag:
    apples: int
    oranges: int


@dataclass
class Event:
    kind: str            # "inflation" | "deflation" | "nullify"
    bag: int = 0         # nullify only: which bag (0 or 1)
    fruit: str = "apples"  # nullify only: which fruit is worth zero

    def describe(self) -> str:
        if self.kind == "inflation":
            return "📈 Fruit inflation: value is doubled (2x)"
        if self.kind == "deflation":
            return "📉 Fruit deflation: value is halved (0.5x)"
        return f"🚫 Nullified: {self.fruit} in Bag {self.bag + 1} are worth zero"


def new_bag(rng: random.Random) -> Bag:
    return Bag(rng.randint(START_MIN, START_MAX), rng.randint(START_MIN, START_MAX))


def grow_bag(bag: Bag, rng: random.Random, bag_max: int = BAG_MAX) -> tuple[Bag, bool]:
    a = bag.apples + rng.randint(GROW_MIN, GROW_MAX)
    o = bag.oranges + rng.randint(GROW_MIN, GROW_MAX)
    if a > bag_max or o > bag_max:
        return new_bag(rng), True
    return Bag(a, o), False


def true_value(bags: list[Bag], event: Event | None = None) -> float:
    apples = [b.apples for b in bags]
    oranges = [b.oranges for b in bags]
    if event and event.kind == "nullify":
        if event.fruit == "apples":
            apples[event.bag] = 0
        else:
            oranges[event.bag] = 0
    v = sum(apples) * sum(oranges)
    if event and event.kind == "inflation":
        v *= 2
    elif event and event.kind == "deflation":
        v /= 2
    return v


def make_quote(value: float, rng: random.Random) -> tuple[int, int]:
    """Quote with value strictly outside [bid, ask], so exactly one side wins."""
    spread = max(1, round(SPREAD_PCT * value))
    edge = max(1.0, value * rng.uniform(EDGE_MIN, EDGE_MAX))
    if rng.random() < 0.5:              # market too cheap: buying wins
        ask = math.floor(value - edge)
        return ask - spread, ask
    bid = math.ceil(value + edge)       # market too rich: selling wins
    return bid, bid + spread


def random_event(rng: random.Random) -> Event:
    kind = rng.choice(["inflation", "deflation", "nullify"])
    if kind == "nullify":
        return Event(kind, bag=rng.randint(0, 1), fruit=rng.choice(["apples", "oranges"]))
    return Event(kind)


@dataclass
class Trade:
    market_id: int
    side: str
    price: int
    value: float
    pnl: float
    t: float
    weight: float = 1.0  # CLICK_DECAY ** (clicks already made in this market)

    @property
    def scored_pnl(self) -> float:
        return self.pnl * self.weight


class FruitGame:
    def __init__(self, duration_s: int = 300, events_on: bool = True,
                 seed: int | None = None, now: float | None = None,
                 bag_max: int = BAG_MAX):
        if not BAG_MAX_MIN <= bag_max <= BAG_MAX_MAX:
            raise ValueError(f"bag_max must be {BAG_MAX_MIN} to {BAG_MAX_MAX}")
        self.rng = random.Random(seed)
        self.bag_max = bag_max
        now = time.time() if now is None else now
        self.start, self.end = now, now + duration_s
        self.events_on = events_on
        self.bags = [new_bag(self.rng), new_bag(self.rng)]
        self.event: Event | None = None
        self.reset_flags = [False, False]
        self.market_id = 1
        self.next_bag_update = now + ROUND_S
        self.bid, self.ask = make_quote(self.value, self.rng)
        self.trades: list[Trade] = []
        self.first_trade_ok: dict[int, bool] = {}
        self.clicks: dict[int, int] = {}                   # market id -> clicks so far
        self.markets: dict[int, float] = {1: self.value}   # market id -> value

    # ---- state -------------------------------------------------------
    @property
    def value(self) -> float:
        return true_value(self.bags, self.event)

    def finished(self, now: float | None = None) -> bool:
        return (time.time() if now is None else now) >= self.end

    def tick(self, now: float | None = None) -> None:
        now = time.time() if now is None else min(now, self.end)
        while now >= self.next_bag_update and self.next_bag_update < self.end:
            self._update_bags(self.next_bag_update)

    def _update_bags(self, t: float) -> None:
        grown = [grow_bag(b, self.rng, self.bag_max) for b in self.bags]
        self.bags = [g[0] for g in grown]
        self.reset_flags = [g[1] for g in grown]
        self.event = random_event(self.rng) if (self.events_on and self.rng.random() < EVENT_PROB) else None
        self.market_id += 1
        self.markets[self.market_id] = self.value
        self.bid, self.ask = make_quote(self.value, self.rng)
        self.next_bag_update = t + ROUND_S

    @property
    def next_click_weight(self) -> float:
        return CLICK_DECAY ** self.clicks.get(self.market_id, 0)

    # ---- actions -----------------------------------------------------
    def trade(self, side: str, now: float | None = None) -> Trade | None:
        now = time.time() if now is None else now
        if self.finished(now):
            return None
        self.tick(now)
        v = self.value
        if side == "buy":
            price, pnl = self.ask, v - self.ask
        elif side == "sell":
            price, pnl = self.bid, self.bid - v
        else:
            raise ValueError(side)
        tr = Trade(self.market_id, side, price, v, pnl, now, self.next_click_weight)
        self.clicks[self.market_id] = self.clicks.get(self.market_id, 0) + 1
        self.trades.append(tr)
        self.first_trade_ok.setdefault(self.market_id, pnl > 0)
        return tr

    # ---- scoring -----------------------------------------------------
    @property
    def raw_profit(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def first_click_accuracy(self) -> float:
        if not self.first_trade_ok:
            return 0.0
        return sum(self.first_trade_ok.values()) / len(self.first_trade_ok)

    @property
    def final_score(self) -> float:
        """Sum of each trade's P&L times its click weight."""
        return sum(t.scored_pnl for t in self.trades)
