# Market Making Games

Two short trading-skill games built in Streamlit.

- **Fruit Market:** compute value (total apples x total oranges across two bags) and trade against a noisy bid/ask. Score = raw profit x first-click accuracy.
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

Tune these at the top of `games/fruit.py`: `BAG_MAX`, `QUOTE_NOISE` (how mispriced the market is), `REQUOTE_S`, `EVENT_PROB`, update interval.

## Kelly with pushes

Even-money bet, P(win) = p, P(lose) = q, P(push) = 1 - p - q.
Maximising p ln(1+f) + q ln(1-f) gives **f\* = (p - q) / (p + q)**.
