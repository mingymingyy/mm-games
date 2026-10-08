"""Next Card Betting game logic (no Streamlit here, so it can be unit-tested).

Cards are drawn without replacement, so the odds change as the deck runs down
(card counting). Bets pay even money; an equal card returns the stake.

Kelly fraction for an even-money bet with pushes:
    maximise p*ln(1+f) + q*ln(1-f)  ->  f* = (p - q) / (p + q)
where p = P(win), q = P(lose). Push probability drops out.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

SUITS = "♠♥♦♣"
FACE = {1: "A", 11: "J", 12: "Q", 13: "K", 14: "A"}
SUIT_BONUS = {1: 0, 2: 1, 3: 2, 4: 3}


def rank_name(r: int) -> str:
    return FACE.get(r, str(r))


def build_deck(n_suits: int, ace_high: bool) -> list[tuple[int, str]]:
    ranks = range(2, 15) if ace_high else range(1, 14)
    return [(r, s) for s in SUITS[:n_suits] for r in ranks]


def odds(current: int, remaining: list[tuple[int, str]]) -> tuple[float, float, float]:
    n = len(remaining)
    if n == 0:
        return 0.0, 0.0, 0.0
    hi = sum(1 for r, _ in remaining if r > current)
    lo = sum(1 for r, _ in remaining if r < current)
    return hi / n, lo / n, (n - hi - lo) / n


def kelly(p_win: float, p_lose: float) -> float:
    if p_win <= p_lose:
        return 0.0
    return (p_win - p_lose) / (p_win + p_lose)


@dataclass
class Round:
    card: tuple[int, str]
    next_card: tuple[int, str]
    p_hi: float
    p_lo: float
    p_eq: float
    choice: str            # "higher" | "lower" | "skip"
    bet: int
    bankroll_before: int
    pnl: int
    kelly_best: float      # Kelly fraction on the better side
    best_side: str | None  # None when p_hi == p_lo (no edge)

    @property
    def bet_fraction(self) -> float:
        return self.bet / self.bankroll_before if self.bankroll_before else 0.0

    @property
    def chosen_ev(self) -> float:
        if self.choice == "higher":
            return self.p_hi - self.p_lo
        if self.choice == "lower":
            return self.p_lo - self.p_hi
        return 0.0


class CardGame:
    def __init__(self, n_suits: int = 1, ace_high: bool = True,
                 bankroll: int = 1000, seed: int | None = None):
        self.rng = random.Random(seed)
        self.n_suits, self.ace_high = n_suits, ace_high
        self.start_bankroll = self.bankroll = bankroll
        self.deck = build_deck(n_suits, ace_high)
        self.rng.shuffle(self.deck)
        self.current = self.deck.pop()
        self.rounds: list[Round] = []

    @property
    def done(self) -> bool:
        return not self.deck or self.bankroll <= 0

    @property
    def bankrupt(self) -> bool:
        return self.bankroll <= 0

    def current_odds(self) -> tuple[float, float, float]:
        return odds(self.current[0], self.deck)

    def hint(self) -> tuple[str | None, float]:
        p_hi, p_lo, _ = self.current_odds()
        if p_hi > p_lo:
            return "higher", kelly(p_hi, p_lo)
        if p_lo > p_hi:
            return "lower", kelly(p_lo, p_hi)
        return None, 0.0

    def play(self, choice: str, bet: int) -> Round:
        if self.done:
            raise RuntimeError("game over")
        if choice not in ("higher", "lower", "skip"):
            raise ValueError(choice)
        bet = 0 if choice == "skip" else int(bet)
        if not 0 <= bet <= self.bankroll:
            raise ValueError("bet must be between 0 and your bankroll")
        p_hi, p_lo, p_eq = self.current_odds()
        best_side, k = self.hint()
        nxt = self.deck.pop()
        if choice == "skip" or nxt[0] == self.current[0]:
            pnl = 0
        elif (nxt[0] > self.current[0]) == (choice == "higher"):
            pnl = bet
        else:
            pnl = -bet
        rnd = Round(self.current, nxt, p_hi, p_lo, p_eq, choice, bet,
                    self.bankroll, pnl, k, best_side)
        self.rounds.append(rnd)
        self.bankroll += pnl
        self.current = nxt
        return rnd

    # ---- skill scoring -------------------------------------------------
    def score(self) -> dict:
        bets = [r for r in self.rounds if r.choice != "skip" and r.bet > 0]
        plus_ev = [r for r in self.rounds if r.best_side is not None]
        good_bets = [r for r in bets if r.chosen_ev > 0]
        taken = [r for r in plus_ev if r.choice == r.best_side and r.bet > 0]

        decision_quality = len(good_bets) / len(bets) if bets else 0.0
        participation = len(taken) / len(plus_ev) if plus_ev else 0.0
        effs = [max(0.0, 1 - abs(r.bet_fraction - r.kelly_best) / r.kelly_best) for r in taken]
        sizing = sum(effs) / len(effs) if effs else 0.0

        dq_pts = 3 * decision_quality
        size_pts = 7 * sizing * participation
        bonus = SUIT_BONUS[self.n_suits]
        total = 0.0 if self.bankrupt else dq_pts + size_pts + bonus
        return {
            "decision_quality": decision_quality,
            "participation": participation,
            "sizing_efficiency": sizing,
            "dq_points": dq_pts,
            "sizing_points": size_pts,
            "suit_bonus": bonus,
            "total": total,
            "bankrupt": self.bankrupt,
        }
