"""Make a Market game logic (no Streamlit here, so it can be unit-tested).

You are the market maker. Each round hides N_DICE dice; the asset settles at
their sum. You quote bid @ ask once with 0 dice shown, once with 1, once with 2,
and then everything settles at the true total.

After each quote, TRADERS_PER_QUOTE traders arrive:
  * informed traders know the true total. They buy at your ask only if the
    total is above it, sell at your bid only if the total is below it.
    That is adverse selection: they only trade when you are wrong.
  * noise traders want to buy or sell for their own reasons, but they are
    price-sensitive: a buyer only trades if your ask is within their
    tolerance of fair value (a seller likewise for your bid). Quote too wide
    and they go elsewhere; quote tight and the informed traders pick you off.

Holding inventory costs INV_COST per unit after every quote, so it pays to
skew quotes to get flat. Trader arrivals are drawn up front for each round,
so a benchmark strategy can be replayed against exactly the same flow.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

N_DICE = 3
DIE_EV = 3.5
TRADERS_PER_QUOTE = 3
NOISE_TOL_MAX = 3.0             # noise tolerance ~ U(0, this): max distance from fair they accept
INV_COST = 0.25                 # charge per unit of |position| after each quote
TICK = 0.5                      # quotes are in steps of 0.5
INFORMED_LEVELS = {"Low": 0.2, "Medium": 0.35, "High": 0.5}
WIDTH_CHOICES = (2.0, 3.0, 4.0, 6.0)
TRADER_NAMES = "ABC"


@dataclass(frozen=True)
class Trader:
    informed: bool
    tolerance: float      # noise only: trades if your price is within this of fair value
    noise_side: str       # noise only: "buy" or "sell" (from the trader's view)


@dataclass
class Fill:
    round_no: int
    stage: int            # dice shown when you quoted
    trader: str
    informed: bool
    side: str             # "sold" (you sold at your ask) or "bought" (you bought at your bid)
    price: float
    fair: float           # fair value when you quoted
    true: int             # settlement value

    @property
    def edge(self) -> float:
        """Edge vs fair value at the time: what the trade was worth on average."""
        return self.price - self.fair if self.side == "sold" else self.fair - self.price

    @property
    def pnl(self) -> float:
        """Realised P&L once the dice settle."""
        return self.price - self.true if self.side == "sold" else self.true - self.price


@dataclass
class QuoteRecord:
    round_no: int
    stage: int
    bid: float
    ask: float
    fair: float
    outcomes: list[str]          # per trader: "bought" / "sold" / "pass", from your view
    position_after: int
    inv_charge: float


@dataclass
class RoundSummary:
    round_no: int
    dice: list[int]
    true: int
    pnl: float
    inv_charge: float
    bench_score: float

    @property
    def score(self) -> float:
        return self.pnl - self.inv_charge


def fair_value(shown: list[int]) -> float:
    return sum(shown) + DIE_EV * (N_DICE - len(shown))


def check_quote(bid: float, ask: float, max_width: float) -> str | None:
    """Return an error message, or None if the quote is valid."""
    if ask <= bid:
        return "Your ask must be above your bid."
    if ask - bid > max_width + 1e-9:
        return f"Too wide: max width is {max_width:g}."
    if abs(bid / TICK - round(bid / TICK)) > 1e-9 or abs(ask / TICK - round(ask / TICK)) > 1e-9:
        return f"Quote in steps of {TICK:g}."
    return None


def flow(traders: list[Trader], bid: float, ask: float, true: int, fair: float) -> list[str]:
    """What each trader does against a quote, from the market maker's view."""
    out = []
    for t in traders:
        if t.informed:
            out.append("sold" if true > ask else "bought" if true < bid else "pass")
        elif t.noise_side == "buy":
            out.append("sold" if ask - fair <= t.tolerance else "pass")
        else:
            out.append("bought" if fair - bid <= t.tolerance else "pass")
    return out


class MarketMakerGame:
    def __init__(self, rounds: int = 8, informed_share: float = 0.4, max_width: float = 4.0,
                 seed: int | None = None):
        if rounds < 1:
            raise ValueError("rounds must be at least 1")
        if not 0 <= informed_share <= 1:
            raise ValueError("informed_share must be 0 to 1")
        self.rng = random.Random(seed)
        self.rounds, self.informed_share, self.max_width = rounds, informed_share, max_width
        self.round_no = 0
        self.fills: list[Fill] = []
        self.quotes: list[QuoteRecord] = []
        self.summaries: list[RoundSummary] = []
        self._start_round()

    # ---- round lifecycle -------------------------------------------------
    def _start_round(self) -> None:
        self.round_no += 1
        self.dice = [self.rng.randint(1, 6) for _ in range(N_DICE)]
        self.traders = [[Trader(self.rng.random() < self.informed_share,
                                self.rng.uniform(0, NOISE_TOL_MAX),
                                self.rng.choice(("buy", "sell")))
                         for _ in range(TRADERS_PER_QUOTE)] for _ in range(N_DICE)]
        self.stage = 0
        self.position = 0
        self.settled = False

    def next_round(self) -> None:
        if not self.settled:
            raise RuntimeError("finish quoting this round first")
        if self.done:
            raise RuntimeError("game over")
        self._start_round()

    @property
    def done(self) -> bool:
        return self.settled and self.round_no >= self.rounds

    @property
    def true(self) -> int:
        return sum(self.dice)

    @property
    def shown(self) -> list[int]:
        return self.dice if self.settled else self.dice[:self.stage]

    @property
    def fair(self) -> float:
        return fair_value(self.dice[:self.stage])

    # ---- quoting -----------------------------------------------------------
    def quote(self, bid: float, ask: float) -> QuoteRecord:
        if self.settled:
            raise RuntimeError("round already settled")
        err = check_quote(bid, ask, self.max_width)
        if err:
            raise ValueError(err)
        fair = self.fair
        outcomes = flow(self.traders[self.stage], bid, ask, self.true, fair)
        for name, t, o in zip(TRADER_NAMES, self.traders[self.stage], outcomes):
            if o == "pass":
                continue
            self.position += 1 if o == "bought" else -1
            self.fills.append(Fill(self.round_no, self.stage, name, t.informed, o,
                                   ask if o == "sold" else bid, fair, self.true))
        charge = INV_COST * abs(self.position)
        rec = QuoteRecord(self.round_no, self.stage, bid, ask, fair, outcomes, self.position, charge)
        self.quotes.append(rec)
        self.stage += 1
        if self.stage == N_DICE:
            self._settle()
        return rec

    def _settle(self) -> None:
        self.settled = True
        rf = [f for f in self.fills if f.round_no == self.round_no]
        charge = sum(q.inv_charge for q in self.quotes if q.round_no == self.round_no)
        self.summaries.append(RoundSummary(self.round_no, list(self.dice), self.true,
                                           sum(f.pnl for f in rf), charge, self._benchmark()))

    def _benchmark(self) -> float:
        """Always quote centred on fair value at max width, against the same traders."""
        pos, pnl, charge = 0, 0.0, 0.0
        half = self.max_width / 2
        for stage in range(N_DICE):
            fv = fair_value(self.dice[:stage])
            bid, ask = fv - half, fv + half
            for o in flow(self.traders[stage], bid, ask, self.true, fv):
                if o == "sold":
                    pos, pnl = pos - 1, pnl + ask - self.true
                elif o == "bought":
                    pos, pnl = pos + 1, pnl + self.true - bid
            charge += INV_COST * abs(pos)
        return pnl - charge

    # ---- scoring -----------------------------------------------------------
    @property
    def banked(self) -> float:
        return sum(s.score for s in self.summaries)

    def breakdown(self) -> dict:
        pnl = sum(f.pnl for f in self.fills)
        charge = sum(s.inv_charge for s in self.summaries)
        noise = sum(f.pnl for f in self.fills if not f.informed)
        informed = sum(f.pnl for f in self.fills if f.informed)
        quotes = [q for q in self.quotes if q.round_no <= len(self.summaries)]
        centring = (sum(abs((q.bid + q.ask) / 2 - q.fair) for q in quotes) / len(quotes)
                    if quotes else 0.0)
        return {
            "score": pnl - charge,
            "pnl": pnl,
            "inv_charge": charge,
            "from_noise": noise,
            "from_informed": informed,
            "edge": sum(f.edge for f in self.fills),
            "benchmark": sum(s.bench_score for s in self.summaries),
            "centring": centring,
            "fills": len(self.fills),
            "informed_fills": sum(f.informed for f in self.fills),
        }
