# Market Making Games

Two short trading-skill games built in Streamlit.

- **Fruit Market:** compute value (total apples x total oranges across two bags) and trade against a bid/ask that is requoted every 5 seconds within each 20-second round. Every quote is 1 to 5% off value, so exactly one side wins, and trading is locked for 2 seconds after any quote change. Within each market, every click counts 85% of the one before, so a wrong first click is heavily penalised. Score = sum of P&L x click weight. Choose the max fruit per bag (10 to 25) to set the difficulty.
- **Next Card Betting:** higher or lower on the next card, drawn without replacement. Score = decision quality (up to 3) + Kelly sizing efficiency x participation (up to 7) + suit bonus.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pip install pytest
python -m pytest tests
```

## Structure

```
app.py            Streamlit UI (pages, timer, buttons)
games/fruit.py    Fruit Market rules, quoting, scoring
games/cards.py    Card odds, Kelly fraction, skill scoring
tests/            Unit tests for both rule engines
```

## Deploy (free)

Push to a public GitHub repo, then create an app on Streamlit Community Cloud pointing at `app.py`.

## Key parameters

Tune these at the top of `games/fruit.py`: `BAG_MAX` (default; players can pick 10 to 25), `CLICK_DECAY` (0.85), `SPREAD_PCT` (2%), `EDGE_MIN`/`EDGE_MAX` (quote sits 1 to 5% off value, always on one side), `ROUND_S` (20 s per bag round), `REQUOTE_S` (5 s), `LOCK_S` (2 s), `EVENT_PROB`.

## Kelly with pushes

Even-money bet, P(win) = p, P(lose) = q, P(push) = 1 - p - q.
Maximising p ln(1+f) + q ln(1-f) gives **f\* = (p - q) / (p + q)**.
