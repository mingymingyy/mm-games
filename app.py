"""Market-making training games. Run with:  streamlit run app.py"""
import time

import pandas as pd
import streamlit as st

from games.cards import CardGame, rank_name
from games.fruit import (BAG_MAX, BAG_MAX_MAX, BAG_MAX_MIN, CLICK_DECAY, LOCK_S, REQUOTE_S,
                         ROUND_S, FruitGame)

st.set_page_config(page_title="Market Making Games", page_icon="📊", layout="centered")

st.markdown("""
<style>
.quote {font-family: ui-monospace, monospace; font-size: 3rem; font-weight: 700;
        text-align: center; padding: .4rem 0; letter-spacing: .05em;}
.quote .bid {color:#d64545;} .quote .ask {color:#1f9d55;} .quote .at {opacity:.5;}
.bag {border:1px solid rgba(128,128,128,.35); border-radius:12px; padding:.6rem .8rem;
      font-size:1.1rem; line-height:1.7; min-height:7.5rem;}
.bag h4 {margin:0 0 .2rem 0; font-size:.9rem; opacity:.7;}
.bag .n {display:inline-block; min-width:2.2em; font-family:ui-monospace, monospace;
         font-size:1.5rem; font-weight:700;}
.card {display:inline-block; width:110px; height:150px; border-radius:12px;
       border:2px solid rgba(128,128,128,.5); background:#fff; color:#111;
       font-size:2.6rem; font-weight:700; text-align:center; line-height:150px;}
.card.red {color:#c62828;} .card.back {background:repeating-linear-gradient(45deg,#2b4c7e,#2b4c7e 8px,#3a62a0 8px,#3a62a0 16px); color:#fff;}
</style>
""", unsafe_allow_html=True)


# ======================================================================
# Fruit Market
# ======================================================================
def fruit_trade(side: str):
    g: FruitGame = st.session_state.fruit
    tr = g.trade(side)
    if tr is None:
        if g.locked():
            st.session_state.fruit_msg = "⏳ Quote just changed: trading is paused, no trade made."
        return
    verb = "Bought at" if side == "buy" else "Sold at"
    tag = "✅" if tr.pnl > 0 else ("➖" if tr.pnl == 0 else "❌")
    st.session_state.fruit_msg = (f"{tag} {verb} {tr.price} · value was {tr.value:g} · "
                                  f"P&L {tr.pnl:+g} × {tr.weight:.0%} = {tr.scored_pnl:+.2f}")


def bag_html(i: int, bag, reset: bool) -> str:
    note = " · <i>reset</i>" if reset else ""
    return (f"<div class='bag'><h4>Bag {i + 1}{note}</h4>"
            f"<span class='n'>{bag.apples}</span>{'🍎' * bag.apples}<br>"
            f"<span class='n'>{bag.oranges}</span>{'🍊' * bag.oranges}</div>")


@st.fragment(run_every=0.5)
def fruit_live():
    g: FruitGame = st.session_state.fruit
    now = time.time()
    g.tick(now)

    if g.finished(now):
        fruit_results(g)
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Time left", f"{int(g.end - now)}s")
    c2.metric("Next bag in", f"{max(0, int(g.next_bag_update - now))}s")
    c3.metric("Next quote in", f"{max(0, int(min(g.next_requote, g.next_bag_update) - now))}s")
    c4.metric("Market #", g.market_id)

    b1, b2 = st.columns(2)
    b1.markdown(bag_html(0, g.bags[0], g.reset_flags[0]), unsafe_allow_html=True)
    b2.markdown(bag_html(1, g.bags[1], g.reset_flags[1]), unsafe_allow_html=True)

    if g.event:
        st.warning(g.event.describe())

    st.markdown(f"<div class='quote'><span class='bid'>{g.bid}</span>"
                f" <span class='at'>@</span> <span class='ask'>{g.ask}</span></div>",
                unsafe_allow_html=True)

    wait = g.lock_remaining(now)
    s, b = st.columns(2)
    s.button(f"SELL at {g.bid}", on_click=fruit_trade, args=("sell",),
             width="stretch", type="secondary", disabled=wait > 0)
    b.button(f"BUY at {g.ask}", on_click=fruit_trade, args=("buy",),
             width="stretch", type="primary", disabled=wait > 0)
    if wait > 0:
        st.caption(f"⏳ New quote: trading opens in {wait:.1f}s")

    if st.session_state.get("fruit_msg"):
        st.caption(st.session_state.fruit_msg)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Score", f"{g.final_score:+.2f}")
    m2.metric("Next click worth", f"{g.next_click_weight:.0%}")
    m3.metric("First-click accuracy", f"{g.first_click_accuracy:.0%}")
    m4.metric("Trades", len(g.trades))


def fruit_results(g: FruitGame):
    st.subheader("⏱️ Time's up")
    c1, c2, c3 = st.columns(3)
    c1.metric("Raw profit", f"{g.raw_profit:+g}")
    c2.metric("First-click accuracy", f"{g.first_click_accuracy:.0%}")
    c3.metric("Final score", f"{g.final_score:+.2f}")
    if g.trades:
        df = pd.DataFrame([{"Market": t.market_id, "Side": t.side.upper(), "Price": t.price,
                            "Value": t.value, "P&L": t.pnl, "Weight": f"{t.weight:.0%}",
                            "Scored": round(t.scored_pnl, 2)} for t in g.trades])
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("No trades this game, so the score is 0.")
    if st.button("Play again", type="primary"):
        del st.session_state["fruit"]
        st.session_state.pop("fruit_msg", None)
        st.rerun(scope="app")


def fruit_page():
    st.title("🍎 Fruit Market")
    st.caption("Value = total apples × total oranges across both bags. "
               "Buy when value > ask, sell when value < bid.")

    if "fruit" not in st.session_state:
        with st.expander("Rules", expanded=True):
            st.markdown(f"""
- Two bags each start with **3 to 8** apples and **3 to 8** oranges.
- **Value = (apples in both bags) × (oranges in both bags).** Each bag shows its counts.
- The market quotes **bid @ ask**, with a **new quote every {REQUOTE_S} seconds**. Every quote is always slightly off the value (1 to 5%), so **exactly one side makes money**: buy if value > ask, sell if value < bid. Spread is about 2%.
- After **any** quote change, trading is **locked for {LOCK_S} seconds** so you can't hit an old price by accident.
- Every **{ROUND_S} seconds** a new round starts: each bag gains 0 to 3 of each fruit. If any count goes above the **max you choose ({BAG_MAX_MIN} to {BAG_MAX_MAX})**, that bag resets. Higher max = bigger numbers = harder maths. Each round is a new market.
- **Events** (if on): inflation 2x, deflation 0.5x, or one fruit in one bag is worth zero.
- **Click decay:** in each round, every click counts **{CLICK_DECAY:.0%}** of the one before (100%, {CLICK_DECAY:.0%}, {CLICK_DECAY**2:.0%}, ...). A wrong first click hits at full weight; trades to win it back count for less.
- **Final score = sum of (P&L × click weight).** First-click accuracy is shown as a stat.
""")
        with st.form("fruit_setup"):
            minutes = st.slider("Game length (minutes)", 1, 10, 5)
            bag_max = st.slider("Max apples / oranges per bag (difficulty)",
                                BAG_MAX_MIN, BAG_MAX_MAX, BAG_MAX)
            events = st.toggle("Market events", value=True)
            if st.form_submit_button("Start game", type="primary"):
                st.session_state.fruit = FruitGame(duration_s=minutes * 60, events_on=events,
                                                    bag_max=bag_max)
                st.session_state.fruit_msg = ""
                st.rerun()
        return

    fruit_live()
    if st.button("Quit game"):
        del st.session_state["fruit"]
        st.rerun()


# ======================================================================
# Next Card Betting
# ======================================================================
def card_html(card, hidden=False) -> str:
    if hidden:
        return "<div class='card back'>?</div>"
    r, s = card
    red = " red" if s in "♥♦" else ""
    return f"<div class='card{red}'>{rank_name(r)}{s}</div>"


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


def cards_page():
    st.title("🃏 Next Card Betting")
    st.caption("Higher or lower? Count the deck, find the edge, size with Kelly.")

    if "cards" not in st.session_state:
        with st.expander("Rules", expanded=True):
            st.markdown("""
- A card is shown. Bet whether the **next** card is **higher** or **lower**. Pays even money; an equal card returns your bet.
- Cards are **not replaced**, so the odds shift as the deck runs down. Count what's left.
- You can **skip** a round when there's no edge.
- **Score** (out of 10, plus suit bonus):
  - **Decision quality, up to 3:** share of your bets that were on the +EV side.
  - **Sizing efficiency, up to 7:** how close your bet (as % of bankroll) was to Kelly, scaled by how many +EV rounds you actually bet.
  - **Suit bonus:** 1 suit +0, 2 suits +1, 3 suits +2, 4 suits +3.
  - Going bankrupt scores 0.
- Kelly here: **f\\* = (p − q) / (p + q)**, with p = P(win), q = P(lose).
""")
        with st.form("card_setup"):
            suits = st.select_slider("Suits in deck", options=[1, 2, 3, 4], value=1)
            ace_high = st.radio("Ace", ["High (14)", "Low (1)"], horizontal=True) == "High (14)"
            bankroll = st.number_input("Starting bankroll", 100, 100_000, 1000, step=100)
            hints = st.toggle("Show odds and Kelly hint (practice mode)", value=False)
            if st.form_submit_button("Start game", type="primary"):
                st.session_state.cards = CardGame(suits, ace_high, int(bankroll))
                st.session_state.card_hints = hints
                st.session_state.card_msg = ""
                st.rerun()
        return

    g: CardGame = st.session_state.cards

    if g.done:
        card_results(g)
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Bankroll", f"{g.bankroll:,}")
    c2.metric("Cards left", len(g.deck))
    c3.metric("Round", len(g.rounds) + 1)

    a, b = st.columns(2)
    a.markdown(card_html(g.current), unsafe_allow_html=True)
    b.markdown(card_html(None, hidden=True), unsafe_allow_html=True)

    if st.session_state.get("card_hints"):
        p_hi, p_lo, p_eq = g.current_odds()
        side, k = g.hint()
        hint = f"Kelly: bet {k:.0%} on {side.upper()}" if side else "No edge: skip"
        st.info(f"HIGHER {p_hi:.0%} · LOWER {p_lo:.0%} · EQUAL {p_eq:.0%} · {hint}")

    st.session_state.card_bet = min(int(st.session_state.get("card_bet", 0)), g.bankroll)
    st.number_input("Bet amount", min_value=0, max_value=g.bankroll, step=10, key="card_bet")
    h, l, s = st.columns(3)
    h.button("⬆️ Higher", on_click=card_play, args=("higher",), width="stretch", type="primary")
    l.button("⬇️ Lower", on_click=card_play, args=("lower",), width="stretch", type="primary")
    s.button("Skip", on_click=card_play, args=("skip",), width="stretch")

    if st.session_state.get("card_msg"):
        st.caption(st.session_state.card_msg)

    if st.button("Quit game"):
        del st.session_state["cards"]
        st.rerun()


def card_results(g: CardGame):
    sc = g.score()
    st.subheader("💀 Bankrupt" if sc["bankrupt"] else "🏁 Deck finished")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skill score", f"{sc['total']:.2f}")
    c2.metric("Decision quality", f"{sc['dq_points']:.2f} / 3")
    c3.metric("Sizing", f"{sc['sizing_points']:.2f} / 7")
    c4.metric("Suit bonus", f"+{sc['suit_bonus']}")
    st.caption(f"Bets on +EV side: {sc['decision_quality']:.0%} · "
               f"+EV rounds taken: {sc['participation']:.0%} · "
               f"Avg sizing efficiency: {sc['sizing_efficiency']:.0%} · "
               f"Final bankroll: {g.bankroll:,}")

    df = pd.DataFrame([{
        "Card": f"{rank_name(r.card[0])}{r.card[1]}",
        "Next": f"{rank_name(r.next_card[0])}{r.next_card[1]}",
        "P(hi)": f"{r.p_hi:.0%}", "P(lo)": f"{r.p_lo:.0%}",
        "Best": (r.best_side or "none"), "Kelly": f"{r.kelly_best:.0%}",
        "You": r.choice, "Bet %": f"{r.bet_fraction:.0%}", "P&L": r.pnl,
    } for r in g.rounds])
    st.dataframe(df, hide_index=True, width="stretch")

    if st.button("Play again", type="primary"):
        del st.session_state["cards"]
        st.rerun()


# ======================================================================
# Home and navigation
# ======================================================================
def home_page():
    st.title("📊 Market Making Games")
    st.write("Short games for training the core trading skills: fast fair-value calculation, "
             "reading a two-way price, and sizing bets to your edge.")
    a, b = st.columns(2)
    with a.container(border=True):
        st.subheader("🍎 Fruit Market")
        st.caption("Easy · about 5 min")
        st.write("Calculate value from two fruit bags and trade against a noisy bid/ask.")
    with b.container(border=True):
        st.subheader("🃏 Next Card Betting")
        st.caption("Easy · about 5 min")
        st.write("Higher or lower on the next card. Count the deck and size with Kelly.")
    st.caption("Pick a game from the sidebar.")


pages = {"Home": home_page, "Fruit Market": fruit_page, "Next Card Betting": cards_page}
choice = st.sidebar.radio("Games", list(pages))
pages[choice]()
