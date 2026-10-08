"""Market-making training games. Run with:  streamlit run app.py"""
import math
import time

import pandas as pd
import streamlit as st

import ui
from games.cards import CardGame, rank_name
from games.fruit import (BAG_MAX, BAG_MAX_MAX, BAG_MAX_MIN, CLICK_DECAY, LOCK_S,
                         QUOTES_PER_ROUND, REQUOTE_S, ROUND_S, FruitGame)
from games.quote import (INFORMED_LEVELS, INV_COST, N_DICE, TICK, TRADER_NAMES, TRADERS_PER_QUOTE,
                         WIDTH_CHOICES, MarketMakerGame, check_quote, fair_value)

st.set_page_config(page_title="Market Making Games", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
ui.inject_css()
st.logo("assets/logo.svg", size="large")


def mmss(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60}:{s % 60:02d}"


# ======================================================================
# Fruit Market
# ======================================================================
FRUIT_DESC = ("Work out the value of two fruit bags and trade against a live bid/ask. "
              "Every quote is slightly off, so exactly one side makes money. Find it fast.")


def start_fruit():
    cfg = {"minutes": st.session_state.fr_minutes, "bag_max": st.session_state.fr_bagmax,
           "events": st.session_state.fr_events, "hide_score": st.session_state.fr_hidescore}
    st.session_state.fr_cfg = cfg
    st.session_state.fruit = FruitGame(duration_s=cfg["minutes"] * 60, events_on=cfg["events"],
                                       bag_max=cfg["bag_max"])
    st.session_state.fruit_msg = st.session_state.fruit_msg_hidden = ""
    st.session_state.fr_hide_live = cfg["hide_score"]


def fruit_trade(side: str):
    g: FruitGame = st.session_state.fruit
    tr = g.trade(side)
    if tr is None:
        if g.locked():
            st.session_state.fruit_msg = "⏳ Quote just changed: trading is paused, no trade made."
            st.session_state.fruit_msg_hidden = st.session_state.fruit_msg
        return
    verb = "Bought at" if side == "buy" else "Sold at"
    tag = "✅" if tr.pnl > 0 else ("➖" if tr.pnl == 0 else "❌")
    st.session_state.fruit_msg = (f"{tag} {verb} {tr.price} · value was {tr.value:g} · "
                                  f"P&L {tr.pnl:+g} × {tr.weight:.0%} = {tr.scored_pnl:+.2f}")
    # Shown instead when the score is hidden: confirms the fill, not the result.
    st.session_state.fruit_msg_hidden = f"📝 {verb} {tr.price} · trade #{len(g.trades)}"


def bag_html(i: int, bag, reset: bool) -> str:
    flag = "<span class='reset'>reset</span>" if reset else ""
    return (f"<div class='bag'><div class='h'><span>Bag {i + 1}</span>{flag}</div>"
            f"<div class='row'><span class='n'>{bag.apples}</span>"
            f"<span class='fr'>{'🍎' * bag.apples}</span></div>"
            f"<div class='row'><span class='n'>{bag.oranges}</span>"
            f"<span class='fr'>{'🍊' * bag.oranges}</span></div></div>")


@st.fragment(run_every=0.5)
def fruit_live():
    g: FruitGame = st.session_state.fruit
    now = time.time()
    g.tick(now)

    if g.finished(now):
        fruit_results(g)
        return

    with st.container(key="desk_fruit"):
        next_quote = min(g.next_requote, g.next_bag_update) - now
        ui.html("<div class='desk-top'><div class='desk-title'>🍎 Fruit Market</div><div class='stats'>"
                + ui.stat("Time left", mmss(g.end - now)) + ui.stat("Round", g.market_id)
                + ui.stat("Next quote", f"{max(0, int(next_quote))}s")
                + ui.stat("Next bag", f"{max(0, int(g.next_bag_update - now))}s") + "</div></div>")

        b1, b2 = st.columns(2)
        b1.markdown(bag_html(0, g.bags[0], g.reset_flags[0]), unsafe_allow_html=True)
        b2.markdown(bag_html(1, g.bags[1], g.reset_flags[1]), unsafe_allow_html=True)

        if g.event:
            ui.html(f"<div class='event'>{g.event.describe()}</div>")

        ui.html(f"<div class='quote'><div class='px'>"
                f"<span class='side'><small>BID</small><span class='bid'>{g.bid}</span></span>"
                f"<span class='at'>@</span>"
                f"<span class='side'><small>ASK</small><span class='ask'>{g.ask}</span></span>"
                f"</div></div>")

        wait = g.lock_remaining(now)
        ui.html(f"<div class='lock on'>⏳ New quote: trading opens in {wait:.1f}s</div>" if wait > 0
                else "<div class='lock off'>● Trading open</div>")

        s, b = st.columns(2)
        s.button(f"SELL at {g.bid}", key="sell_btn", on_click=fruit_trade, args=("sell",),
                 width="stretch", disabled=wait > 0)
        b.button(f"BUY at {g.ask}", key="buy_btn", on_click=fruit_trade, args=("buy",),
                 width="stretch", disabled=wait > 0)

        hide = st.session_state.get("fr_hide_live", False)
        msg = st.session_state.get("fruit_msg_hidden" if hide else "fruit_msg")
        m, q = st.columns([5, 1], vertical_alignment="center")
        m.markdown(f"<div class='msg'>{msg or 'No trades yet.'}</div>", unsafe_allow_html=True)
        with q.container(key="quit_fruit"):
            if st.button("Quit", width="stretch"):
                del st.session_state["fruit"]
                st.rerun(scope="app")

    st.toggle("Hide score while playing", key="fr_hide_live",
              help="Hides your score, accuracy and each trade's P&L until the game ends.")
    hide = st.session_state.fr_hide_live
    ui.html("<div class='tiles'>"
            + (ui.tile("Score", "Hidden") if hide
               else ui.tile("Score", f"{g.final_score:+.2f}", ui.tone(g.final_score)))
            + ui.tile("Next click worth", f"{g.next_click_weight:.0%}")
            + ui.tile("First-click accuracy", "Hidden" if hide else f"{g.first_click_accuracy:.0%}")
            + ui.tile("Trades", str(len(g.trades))) + "</div>")


def fruit_results(g: FruitGame):
    with st.container(key="desk_fruit_done"):
        ui.html("<div class='desk-top'><div class='desk-title'>⏱️ Time's up</div></div>"
                "<div class='stats'>" + ui.stat("Final score", f"{g.final_score:+.2f}")
                + ui.stat("Raw profit", f"{g.raw_profit:+g}")
                + ui.stat("First-click accuracy", f"{g.first_click_accuracy:.0%}")
                + ui.stat("Trades", len(g.trades)) + "</div>")
    if g.trades:
        df = pd.DataFrame([{"Round": t.market_id, "Side": t.side.upper(), "Price": t.price,
                            "Value": t.value, "P&L": t.pnl, "Weight": f"{t.weight:.0%}",
                            "Scored": round(t.scored_pnl, 2)} for t in g.trades])
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("No trades this game, so the score is 0.")
    with st.container(key="big_fruit_again"):
        if st.button("Play again", type="primary", icon=":material/replay:"):
            del st.session_state["fruit"]
            st.session_state.pop("fruit_msg", None)
            st.rerun(scope="app")


def fruit_tabs():
    t1, t2, t3, t4 = st.tabs([":material/menu_book: Rules", ":material/calculate: Value Calculation",
                              ":material/play_circle: Examples", ":material/lightbulb: Strategies"])
    with t1:
        ui.section("info", "Overview")
        st.markdown(f"""
Two bags of fruit, one market. Work out what the fruit is worth, compare it with the market's
**bid @ ask**, and hit the side that makes money before the quote moves.

| Every round ({ROUND_S}s) | |
|---|---|
| **0s** | Bags update, new quote, trading locked for {LOCK_S}s |
| **{REQUOTE_S:.2f}s** | New quote, locked for {LOCK_S}s |
| **{2 * REQUOTE_S:.2f}s** | New quote, locked for {LOCK_S}s |
| **{ROUND_S}s** | Next round |

- Two bags each start with **3 to 8** apples and **3 to 8** oranges.
- Each round, every bag gains **0 to 3** of each fruit. If a count goes above the **max you
  choose ({BAG_MAX_MIN} to {BAG_MAX_MAX})**, that bag resets.
- The market quotes {QUOTES_PER_ROUND} times per round. Every quote sits just **0.5 to 1.5% off**
  the value with a spread of about **1%**, so **exactly one side makes money**, but only a little.
- **Events** (if on): inflation 2x, deflation 0.5x, or one fruit in one bag is worth zero.
- **Click decay:** within a round, each click counts **{CLICK_DECAY:.0%}** of the one before
  (100%, {CLICK_DECAY:.0%}, {CLICK_DECAY ** 2:.0%}, …). It resets each round.
- **Score = sum of (P&L × click weight).**
""")
    with t2:
        ui.section("calc", "Value Calculation")
        ui.html("<div class='formula'>value = (apples in both bags) × (oranges in both bags)</div>")
        st.markdown("""
Example: **Bag 1** has 7 🍎 and 5 🍊, **Bag 2** has 4 🍎 and 8 🍊.
Apples = 7 + 4 = **11**, oranges = 5 + 8 = **13**, so value = 11 × 13 = **143**.

| Event | Calculation | Value |
|---|---|---|
| None | 11 × 13 | **143** |
| 📈 Inflation (2x) | 143 × 2 | **286** |
| 📉 Deflation (0.5x) | 143 ÷ 2 | **71.5** |
| 🚫 Apples in Bag 2 worth zero | 7 × 13 | **91** |
| 🚫 Oranges in Bag 1 worth zero | 11 × 8 | **88** |
""")
    with t3:
        ui.section("play", "Examples")
        st.markdown("""
Value is **143** in each example.

| Quote | Compare | Right move | P&L |
|---|---|---|---|
| **145 @ 146** | 143 is below the bid 145 | **Sell** at 145 | **+2** |
| **141 @ 142** | 143 is above the ask 142 | **Buy** at 142 | **+1** |

**Why the first click matters.** Quote 145 @ 146: you panic and buy at 146 (−3 at 100%), then
sell at 145 (+2 at 85% = +1.70). Round score: **−1.30**, even though you ended up on the right side.
Edges are thin, so one wrong click wipes out several right ones.
""")
    with t4:
        ui.section("bulb", "Strategies")
        st.markdown("""
1. **Add the bags first, multiply once.** Total apples × total oranges, not bag by bag.
2. **Update, don't recompute.** When apples go up by *a*, value goes up by *a* × oranges.
3. **Read the event banner before the quote.** It changes the value, not the bags.
4. **Use the lock as thinking time.** The quote is already on screen for 1.5s before you can trade.
5. **Make the first click count.** Later clicks in the same round are worth less.
6. **Raise the max as you improve.** At 25 per bag, values reach 2,500 and the maths gets real.
""")


def fruit_page():
    if "fruit" in st.session_state:
        fruit_live()
        return

    cta = ui.hero(ui.fruit_art(), "Fruit Market", [("Solo", "green"), ("Easy → Hard", "slate")],
                  FRUIT_DESC, "1 player", "~5 min")
    with cta.container(key="big_fruit_hero"):
        st.button("Play Now", key="fr_play_hero", type="primary", icon=":material/play_arrow:",
                  on_click=start_fruit, width="stretch")

    cfg = st.session_state.get("fr_cfg", {})
    with st.container(border=True, key="settings_fruit"):
        ui.html("<div class='sec-h' style='font-size:1.15rem'>Game settings</div>")
        a, b, c = st.columns(3, gap="large")
        a.slider("Game length (minutes)", 1, 10, cfg.get("minutes", 5), key="fr_minutes")
        b.slider("Max apples / oranges per bag", BAG_MAX_MIN, BAG_MAX_MAX,
                 cfg.get("bag_max", BAG_MAX), key="fr_bagmax", help="Higher = bigger numbers")
        with c:
            st.toggle("Market events", value=cfg.get("events", True), key="fr_events")
            st.toggle("Hide score while playing", value=cfg.get("hide_score", False),
                      key="fr_hidescore", help="See your score only when the game ends. "
                      "You can also switch this during the game.")

    fruit_tabs()
    ui.play_bar("Fruit Market", "1 player", "~5 min", start_fruit, "fr_play_bar")


# ======================================================================
# Next Card Betting
# ======================================================================
CARDS_DESC = ("Higher or lower on the next card, drawn without replacement. Count the deck to "
              "find the edge, then size every bet with the Kelly criterion.")


def start_cards():
    cfg = {"suits": st.session_state.cd_suits, "ace_high": st.session_state.cd_ace == "High (14)",
           "bankroll": int(st.session_state.cd_bankroll), "hints": st.session_state.cd_hints}
    st.session_state.cd_cfg = cfg
    st.session_state.cards = CardGame(cfg["suits"], cfg["ace_high"], cfg["bankroll"])
    st.session_state.card_hints = cfg["hints"]
    st.session_state.card_msg = ""


def card_html(card, hidden=False) -> str:
    if hidden:
        return "<div class='pcard back'>?</div>"
    r, s = card
    red = " red" if s in "♥♦" else ""
    return f"<div class='pcard{red}'>{rank_name(r)}{s}</div>"


def card_play(choice: str):
    g: CardGame = st.session_state.cards
    bet = 0 if choice == "skip" else int(st.session_state.get("card_bet", 0))
    if choice != "skip" and bet <= 0:
        st.session_state.card_msg = "⚠️ Enter a bet above 0, or press Skip."
        return
    bet = min(bet, g.bankroll)
    r = g.play(choice, bet)
    nxt = f"{rank_name(r.next_card[0])}{r.next_card[1]}"
    if choice == "skip":
        st.session_state.card_msg = f"Skipped. Next card was {nxt}."
    elif r.pnl > 0:
        st.session_state.card_msg = f"✅ {nxt}: won {r.pnl}"
    elif r.pnl < 0:
        st.session_state.card_msg = f"❌ {nxt}: lost {-r.pnl}"
    else:
        st.session_state.card_msg = f"➖ {nxt}: equal card, bet returned"


def cards_tabs():
    t1, t2, t3, t4 = st.tabs([":material/menu_book: Rules", ":material/calculate: Odds & Kelly",
                              ":material/play_circle: Examples", ":material/lightbulb: Strategies"])
    with t1:
        ui.section("info", "Overview")
        st.markdown("""
- A card is shown. Bet whether the **next** card is **higher** or **lower**. Pays even money;
  an equal card returns your bet.
- Cards are **not replaced**, so the odds shift as the deck runs down. Count what's left.
- You can **skip** a round when there's no edge.
- **Score** (out of 10, plus suit bonus):
  - **Decision quality, up to 3:** share of your bets that were on the +EV side.
  - **Sizing efficiency, up to 7:** how close your bet (as % of bankroll) was to Kelly, scaled
    by how many +EV rounds you actually bet.
  - **Suit bonus:** 1 suit +0, 2 suits +1, 3 suits +2, 4 suits +3.
  - Going bankrupt scores 0.
""")
    with t2:
        ui.section("calc", "Odds & Kelly")
        ui.html("<div class='formula'>p = higher cards left ÷ cards left &nbsp;·&nbsp; "
                "q = lower cards left ÷ cards left<br>Kelly bet f* = (p − q) ÷ (p + q)</div>")
        st.markdown("""
Equal cards return your stake, so they drop out of the sizing. Bet on the side with the larger
probability; if p = q there is no edge, so skip.
""")
    with t3:
        ui.section("play", "Examples")
        st.markdown("""
| Deck | Card shown | Left: higher / lower / equal | p, q | Kelly |
|---|---|---|---|---|
| 1 suit, Ace high | **5** | 9 / 3 / 0 | 75%, 25% | **50% on Higher** |
| 2 suits, Ace high | **7♠** | 14 / 10 / 1 | 56%, 40% | **17% on Higher** |
| Late in the deck | **9** | 1 / 1 / 0 | 50%, 50% | **Skip** |
""")
    with t4:
        ui.section("bulb", "Strategies")
        st.markdown("""
1. **Count, don't guess.** The edge comes from the cards already gone.
2. **Never bet more than Kelly.** Overbetting lowers long-run growth and risks a 0 score.
3. **Skip when p = q.** No edge means no bet.
4. **More suits = more equal cards.** They return your stake but still cost you time.
""")


def cards_page():
    if "cards" in st.session_state:
        cards_live()
        return

    cta = ui.hero(ui.cards_art(), "Next Card Betting", [("Solo", "green"), ("Medium", "slate")],
                  CARDS_DESC, "1 player", "~5 min")
    with cta.container(key="big_cards_hero"):
        st.button("Play Now", key="cd_play_hero", type="primary", icon=":material/play_arrow:",
                  on_click=start_cards, width="stretch")

    cfg = st.session_state.get("cd_cfg", {})
    with st.container(border=True, key="settings_cards"):
        ui.html("<div class='sec-h' style='font-size:1.15rem'>Game settings</div>")
        a, b, c, d = st.columns(4, gap="large")
        a.select_slider("Suits in deck", options=[1, 2, 3, 4], value=cfg.get("suits", 1),
                        key="cd_suits")
        b.radio("Ace", ["High (14)", "Low (1)"], horizontal=True,
                index=0 if cfg.get("ace_high", True) else 1, key="cd_ace")
        c.number_input("Starting bankroll", 100, 100_000, cfg.get("bankroll", 1000), step=100,
                       key="cd_bankroll")
        d.toggle("Practice hints (odds + Kelly)", value=cfg.get("hints", False), key="cd_hints")

    cards_tabs()
    ui.play_bar("Next Card Betting", "1 player", "~5 min", start_cards, "cd_play_bar")


def cards_live():
    g: CardGame = st.session_state.cards
    if g.done:
        card_results(g)
        return

    with st.container(key="desk_cards"):
        ui.html("<div class='desk-top'><div class='desk-title'>🃏 Next Card Betting</div>"
                "<div class='stats'>" + ui.stat("Bankroll", f"{g.bankroll:,}")
                + ui.stat("Cards left", len(g.deck)) + ui.stat("Round", len(g.rounds) + 1)
                + "</div></div>")
        ui.html(f"<div class='big-card'>{card_html(g.current)}{card_html(None, hidden=True)}</div>")

        if st.session_state.get("card_hints"):
            p_hi, p_lo, p_eq = g.current_odds()
            side, k = g.hint()
            hint = f"Kelly: bet {k:.0%} on {side.upper()}" if side else "No edge: skip"
            ui.html(f"<div class='odds'>HIGHER {p_hi:.0%} · LOWER {p_lo:.0%} · EQUAL {p_eq:.0%}"
                    f" · {hint}</div>")

        st.session_state.card_bet = min(int(st.session_state.get("card_bet", 0)), g.bankroll)
        st.number_input("Bet amount", min_value=0, max_value=g.bankroll, step=10, key="card_bet")
        h, l, s = st.columns(3)
        h.button("Higher", key="hi_btn", icon=":material/arrow_upward:", on_click=card_play,
                 args=("higher",), width="stretch")
        l.button("Lower", key="lo_btn", icon=":material/arrow_downward:", on_click=card_play,
                 args=("lower",), width="stretch")
        s.button("Skip", key="skip_btn", on_click=card_play, args=("skip",), width="stretch")

        m, q = st.columns([5, 1], vertical_alignment="center")
        m.markdown(f"<div class='msg'>{st.session_state.get('card_msg') or 'Place a bet or skip.'}"
                   "</div>", unsafe_allow_html=True)
        with q.container(key="quit_cards"):
            if st.button("Quit", width="stretch"):
                del st.session_state["cards"]
                st.rerun()


def card_results(g: CardGame):
    sc = g.score()
    with st.container(key="desk_cards_done"):
        ui.html(f"<div class='desk-top'><div class='desk-title'>"
                f"{'💀 Bankrupt' if sc['bankrupt'] else '🏁 Deck finished'}</div></div>"
                "<div class='stats'>" + ui.stat("Skill score", f"{sc['total']:.2f}")
                + ui.stat("Decision quality", f"{sc['dq_points']:.2f} / 3")
                + ui.stat("Sizing", f"{sc['sizing_points']:.2f} / 7")
                + ui.stat("Suit bonus", f"+{sc['suit_bonus']}")
                + ui.stat("Final bankroll", f"{g.bankroll:,}") + "</div>")
    st.caption(f"Bets on +EV side: {sc['decision_quality']:.0%} · "
               f"+EV rounds taken: {sc['participation']:.0%} · "
               f"Avg sizing efficiency: {sc['sizing_efficiency']:.0%}")

    df = pd.DataFrame([{
        "Card": f"{rank_name(r.card[0])}{r.card[1]}",
        "Next": f"{rank_name(r.next_card[0])}{r.next_card[1]}",
        "P(hi)": f"{r.p_hi:.0%}", "P(lo)": f"{r.p_lo:.0%}",
        "Best": (r.best_side or "none"), "Kelly": f"{r.kelly_best:.0%}",
        "You": r.choice, "Bet %": f"{r.bet_fraction:.0%}", "P&L": r.pnl,
    } for r in g.rounds])
    st.dataframe(df, hide_index=True, width="stretch")

    with st.container(key="big_cards_again"):
        if st.button("Play again", type="primary", icon=":material/replay:"):
            del st.session_state["cards"]
            st.rerun()


# ======================================================================
# Make a Market
# ======================================================================
MM_DESC = ("Now you're the market maker. Quote a bid and ask on the sum of three hidden dice. "
           "Earn the spread from regular traders, don't get picked off by informed ones, "
           "and keep your inventory in check.")


def start_mm():
    cfg = {"rounds": st.session_state.mm_rounds, "informed": st.session_state.mm_informed,
           "width": float(st.session_state.mm_width), "hint": st.session_state.mm_hint}
    st.session_state.mm_cfg = cfg
    st.session_state.mm = MarketMakerGame(cfg["rounds"], INFORMED_LEVELS[cfg["informed"]],
                                          cfg["width"])
    mm_set_quote(*opening_quote(cfg["width"]))
    st.session_state.mm_err = ""
    st.session_state.mm_results = False


def opening_quote(width: float) -> tuple[float, float]:
    """A quote of the given width centred as close as the tick allows on the opening fair value."""
    bid = math.floor((fair_value([]) - width / 2) / TICK) * TICK
    return bid, bid + width


def mm_set_quote(bid: float, ask: float):
    # Kept outside the widget keys too: Streamlit drops widget state while the inputs are hidden
    # (between rounds), so the inputs are re-seeded from these.
    st.session_state.mm_bid = st.session_state.mm_last_bid = float(bid)
    st.session_state.mm_ask = st.session_state.mm_last_ask = float(ask)


def mm_send():
    g: MarketMakerGame = st.session_state.mm
    bid, ask = float(st.session_state.mm_bid), float(st.session_state.mm_ask)
    err = check_quote(bid, ask, g.max_width)
    st.session_state.mm_err = err or ""
    st.session_state.mm_last_bid, st.session_state.mm_last_ask = bid, ask
    if not err:
        g.quote(bid, ask)


def mm_shift(delta: float):
    mm_set_quote(float(st.session_state.mm_bid) + delta, float(st.session_state.mm_ask) + delta)


def mm_next():
    g: MarketMakerGame = st.session_state.mm
    if g.done:
        st.session_state.mm_results = True
    else:
        g.next_round()
        width = st.session_state.mm_last_ask - st.session_state.mm_last_bid
        mm_set_quote(*opening_quote(min(max(width, TICK), g.max_width)))


def pos_text(p: int) -> str:
    return "flat" if p == 0 else (f"+{p} long" if p > 0 else f"{p} short")


def dice_html(g: MarketMakerGame) -> str:
    faces = []
    for i, d in enumerate(g.dice):
        shown = g.settled or i < g.stage
        faces.append(f"<div class='die{'' if shown else ' hidden'}'>{d if shown else '?'}</div>")
    return f"<div class='dice-row'>{''.join(faces)}</div>"


def flow_lines(g: MarketMakerGame, reveal: bool) -> str:
    """This round's quotes and what each trader did. Trader types only after settlement."""
    fills = {(f.stage, f.trader): f for f in g.fills if f.round_no == g.round_no}
    rows = []
    for q in [q for q in g.quotes if q.round_no == g.round_no]:
        acts = []
        for name, o in zip(TRADER_NAMES, q.outcomes):
            f = fills.get((q.stage, name))
            who = f"{name}{' (informed)' if reveal and f and f.informed else ''}"
            if o == "sold":
                acts.append(f"<span class='lift'>{who} bought at your ask</span>")
            elif o == "bought":
                acts.append(f"<span class='hit'>{who} sold at your bid</span>")
            else:
                acts.append(f"<span class='pass'>{name} passed</span>")
        rows.append(f"<div class='fl'><b>{q.stage} shown · {q.bid:g} @ {q.ask:g}</b>"
                    f"<span>{' · '.join(acts)}</span>"
                    f"<em>position {pos_text(q.position_after)} · cost {q.inv_charge:g}</em></div>")
    return "<div class='flow'>" + ("".join(rows) or "<div class='fl'>No quotes yet this round.</div>") + "</div>"


def mm_live():
    g: MarketMakerGame = st.session_state.mm
    if st.session_state.get("mm_results"):
        mm_results(g)
        return

    cost_now = sum(q.inv_charge for q in g.quotes if q.round_no == g.round_no)
    with st.container(key="desk_mm"):
        ui.html("<div class='desk-top'><div class='desk-title'>🎲 Make a Market</div><div class='stats'>"
                + ui.stat("Round", f"{g.round_no} / {g.rounds}")
                + ui.stat("Dice shown", f"{len(g.shown)} / {N_DICE}")
                + ui.stat("Position", pos_text(g.position))
                + ui.stat("Inventory cost", f"{cost_now:g}")
                + ui.stat("Banked score", f"{g.banked:+.1f}") + "</div></div>")
        ui.html(dice_html(g))

        if not g.settled:
            caption = "Settles at the sum of all three dice."
            if st.session_state.mm_cfg.get("hint"):
                caption += f" &nbsp;Fair value now: <b>{g.fair:g}</b>"
            ui.html(f"<div class='odds'>{caption}</div>")

            for k in ("bid", "ask"):
                if f"mm_{k}" not in st.session_state:
                    st.session_state[f"mm_{k}"] = st.session_state[f"mm_last_{k}"]
            b, a, s = st.columns([1, 1, 1.2], vertical_alignment="bottom")
            b.number_input("Your bid", min_value=0.0, max_value=30.0, step=TICK, format="%.1f",
                           key="mm_bid")
            a.number_input("Your ask", min_value=0.0, max_value=30.0, step=TICK, format="%.1f",
                           key="mm_ask")
            s.button(f"Send quote ({g.stage + 1}/{N_DICE})", key="send_btn", on_click=mm_send,
                     icon=":material/send:", width="stretch")
            bid, ask = float(st.session_state.mm_bid), float(st.session_state.mm_ask)
            d, u, info = st.columns([1, 1, 2.6], vertical_alignment="center")
            with d.container(key="shift_dn"):
                st.button("Shift down", icon=":material/south:", on_click=mm_shift, args=(-TICK,),
                          width="stretch")
            with u.container(key="shift_up"):
                st.button("Shift up", icon=":material/north:", on_click=mm_shift, args=(TICK,),
                          width="stretch")
            info.markdown(f"<div class='odds' style='text-align:left'>Width {ask - bid:g} "
                          f"(max {g.max_width:g}) · Mid {(bid + ask) / 2:g}</div>",
                          unsafe_allow_html=True)
            if st.session_state.get("mm_err"):
                ui.html(f"<div class='event'>⚠️ {st.session_state.mm_err}</div>")
        else:
            s = g.summaries[-1]
            ui.html(f"<div class='settle'>Total = {' + '.join(map(str, g.dice))} = <b>{g.true}</b>"
                    f" &nbsp;·&nbsp; Round P&L {s.pnl:+g} &nbsp;·&nbsp; Inventory cost {s.inv_charge:g}"
                    f" &nbsp;·&nbsp; <b>Round score {s.score:+.2f}</b>"
                    f" &nbsp;·&nbsp; Benchmark {s.bench_score:+.2f}</div>")

        ui.html(flow_lines(g, reveal=g.settled))

        m, q = st.columns([5, 1], vertical_alignment="center")
        if g.settled:
            with m.container(key="big_mm_next"):
                st.button("See results" if g.done else "Next round", type="primary",
                          icon=":material/arrow_forward:", on_click=mm_next, width="stretch")
        with q.container(key="quit_mm"):
            if st.button("Quit", width="stretch"):
                del st.session_state["mm"]
                st.rerun()


def mm_results(g: MarketMakerGame):
    bd = g.breakdown()
    with st.container(key="desk_mm_done"):
        beat = bd["score"] - bd["benchmark"]
        ui.html("<div class='desk-top'><div class='desk-title'>🏁 Market closed</div></div>"
                "<div class='stats'>" + ui.stat("Final score", f"{bd['score']:+.2f}")
                + ui.stat("Benchmark", f"{bd['benchmark']:+.2f}")
                + ui.stat("vs benchmark", f"{beat:+.2f}")
                + ui.stat("Earned from noise", f"{bd['from_noise']:+g}")
                + ui.stat("Lost to informed", f"{bd['from_informed']:+g}")
                + ui.stat("Inventory cost", f"{-bd['inv_charge']:+g}")
                + ui.stat("Mid vs fair (avg)", f"{bd['centring']:.2f}") + "</div>")

    notes = []
    if bd["score"] > bd["benchmark"]:
        notes.append("✅ You beat the benchmark: better than quoting centred at max width every time.")
    else:
        notes.append("📏 The benchmark beat you. It just quotes centred on fair value at max width.")
    if bd["centring"] > 0.75:
        notes.append(f"🎯 Your mid was {bd['centring']:.2f} from fair value on average. "
                     "Re-centre after every die: fair = shown dice + 3.5 × hidden dice.")
    if bd["fills"] and bd["informed_fills"] / bd["fills"] > 0.5:
        notes.append("🦈 Most of your fills were informed traders. Your quotes were often on the wrong "
                     "side of the total: widen when few dice are showing.")
    if bd["from_noise"] > 0 and bd["inv_charge"] > 0.4 * bd["from_noise"]:
        notes.append("📦 Inventory cost ate a big share of your spread income. When long, shade both "
                     "quotes down; when short, shade them up.")
    if bd["fills"] < 2 * g.rounds:
        notes.append("🌵 Few trades: your quotes may be too wide for regular traders. Tighten once "
                     "dice are revealed.")
    for n in notes:
        st.markdown(n)

    df = pd.DataFrame([{"Round": s.round_no, "Dice": " ".join(map(str, s.dice)), "Total": s.true,
                        "P&L": s.pnl, "Inventory cost": s.inv_charge, "Score": round(s.score, 2),
                        "Benchmark": round(s.bench_score, 2)} for s in g.summaries])
    st.dataframe(df, hide_index=True, width="stretch")

    with st.container(key="big_mm_again"):
        if st.button("Play again", type="primary", icon=":material/replay:"):
            del st.session_state["mm"]
            st.rerun()


def mm_tabs():
    t1, t2, t3, t4 = st.tabs([":material/menu_book: Rules", ":material/calculate: Fair Value",
                              ":material/play_circle: Examples", ":material/lightbulb: Strategies"])
    with t1:
        ui.section("info", "Overview")
        st.markdown(f"""
You are the **market maker**. Each round hides three dice, and the asset settles at **their sum**.
You quote a **bid @ ask** three times per round: with **0**, **1** and **2** dice showing.
Then the last die is revealed and every trade settles at the true total.

After each quote, **{TRADERS_PER_QUOTE} traders** arrive:

| Trader | What they know | What they do |
|---|---|---|
| **Regular (noise)** | Fair value only | Buys or sells for their own reasons, but only if your price is close enough to fair. Quote too wide and they go elsewhere. |
| **Informed** | The **true total** | Buys your ask only if the total is above it; sells your bid only if it's below. They only trade when you're wrong. |

- You **don't** see who is informed until the round settles.
- Your quote can be at most the **max width** you chose (ask − bid), in steps of {TICK:g}.
- **Inventory cost:** after every quote you pay **{INV_COST:g} per unit** you hold, long or short.
- **Score = trading P&L − inventory cost.** You're compared with a **benchmark** that faces the
  exact same traders but always quotes centred on fair value at max width.
""")
    with t2:
        ui.section("calc", "Fair Value")
        ui.html("<div class='formula'>fair value = (sum of dice shown) + 3.5 × (dice still hidden)</div>")
        st.markdown("""
| Dice shown | Fair value | Uncertainty (std. dev.) |
|---|---|---|
| none | 0 + 3.5 × 3 = **10.5** | ± 2.96 |
| 6 | 6 + 3.5 × 2 = **13** | ± 2.42 |
| 6, 2 | 8 + 3.5 = **11.5** | ± 1.71 |
| 6, 2, 5 | **13** (settled) | none |

The uncertainty shrinks as dice are revealed, so informed traders have less of an edge over you.
""")
    with t3:
        ui.section("play", "Examples")
        st.markdown("""
**1. Opening quote.** No dice shown, fair value 10.5. You quote **9 @ 12** (width 3).
A regular buyer pays 12: you earn **1.5** on average. An informed trader only pays 12 when the
total is **13 or more**, and then you lose.

**2. Re-centre after a die.** The first die is a **6**, so fair value jumps to **13**.
If you leave 9 @ 12 up, informed traders buy at 12 whenever the other two dice sum to 7+
(**58%** of the time). Move to about **11.5 @ 14.5**.

**3. Skew to flatten.** You're **long 2** after two regular sellers hit your bid. Fair value is 13.
Instead of 11.5 @ 14.5, quote **11 @ 14**: buyers are now more likely to lift you and sellers
less likely to hit you, so your position shrinks and so does your inventory cost.
""")
    with t4:
        ui.section("bulb", "Strategies")
        st.markdown("""
1. **Centre on fair value, every time.** Shown dice + 3.5 for each hidden die.
2. **Width pays for risk.** Go wider when uncertainty is high (no dice shown) or there are many
   informed traders; go tighter as dice are revealed.
3. **Too wide is also a mistake.** Regular traders walk away, and then you earn nothing.
4. **Read the flow.** If your ask keeps getting lifted, the total may be higher than fair value.
   Informed traders are telling you something.
5. **Skew, don't sit on inventory.** Long → shade both quotes down. Short → shade them up.
""")


def mm_page():
    if "mm" in st.session_state:
        mm_live()
        return

    cta = ui.hero(ui.mm_art(), "Make a Market", [("Solo", "green"), ("Medium", "slate")],
                  MM_DESC, "1 player", "~5 min")
    with cta.container(key="big_mm_hero"):
        st.button("Play Now", key="mm_play_hero", type="primary", icon=":material/play_arrow:",
                  on_click=start_mm, width="stretch")

    cfg = st.session_state.get("mm_cfg", {})
    with st.container(border=True, key="settings_mm"):
        ui.html("<div class='sec-h' style='font-size:1.15rem'>Game settings</div>")
        a, b, c, d = st.columns(4, gap="large")
        a.slider("Rounds", 3, 15, cfg.get("rounds", 8), key="mm_rounds")
        b.select_slider("Informed traders", options=list(INFORMED_LEVELS),
                        value=cfg.get("informed", "Medium"), key="mm_informed",
                        format_func=lambda k: f"{k} ({INFORMED_LEVELS[k]:.0%})")
        c.select_slider("Max width", options=list(WIDTH_CHOICES), value=cfg.get("width", 4.0),
                        key="mm_width", format_func=lambda w: f"{w:g}")
        d.toggle("Show fair value (practice)", value=cfg.get("hint", False), key="mm_hint")

    mm_tabs()
    ui.play_bar("Make a Market", "1 player", "~5 min", start_mm, "mm_play_bar")


# ======================================================================
# Home and navigation
# ======================================================================
def game_card(key: str, art: str, title: str, badge_items, desc: str, page) -> None:
    with st.container(border=True, key=f"gc_{key}"):
        ui.html(f"{art}<div class='on-light'><div class='gc-title'>{title}"
                f"{ui.badges(badge_items)}</div></div><div class='gc-desc'>{desc}</div>"
                + ui.meta("1 player", "~5 min", light=True))
        with st.container(key=f"big_link_{key}"):
            st.page_link(page, label="Play", icon=":material/play_arrow:", width="stretch")


def home_page():
    cta = ui.hero("", "Market Making Games", [("Free", "green")],
                  "Short, focused games for the skills trading interviews test: fast fair-value "
                  "maths, reading a two-way price, sizing bets to your edge, and making a market "
                  "yourself.",
                  "Solo practice", "~5 min per game", back=False)
    with cta.container(key="big_link_home"):
        st.page_link(FRUIT, label="Start playing", icon=":material/play_arrow:", width="stretch")

    ui.html("<div class='section-title'>Games</div>"
            "<div class='section-sub'>Pick a game. Each one trains a different skill.</div>")
    a, b, c = st.columns(3, gap="large")
    with a:
        game_card("fruit", ui.fruit_art(small=True), "Fruit Market",
                  [("Solo", "green"), ("Easy → Hard", "slate")], FRUIT_DESC, FRUIT)
    with b:
        game_card("cards", ui.cards_art(small=True), "Next Card Betting",
                  [("Solo", "green"), ("Medium", "slate")], CARDS_DESC, CARDS)
    with c:
        game_card("mm", ui.mm_art(small=True), "Make a Market",
                  [("Solo", "green"), ("Medium", "slate")], MM_DESC, MM)


HOME = st.Page(home_page, title="Games", url_path="games", default=True)
FRUIT = st.Page(fruit_page, title="Fruit Market", url_path="fruit-market")
CARDS = st.Page(cards_page, title="Next Card Betting", url_path="next-card")
MM = st.Page(mm_page, title="Make a Market", url_path="make-a-market")
st.navigation([HOME, FRUIT, CARDS, MM], position="top").run()
