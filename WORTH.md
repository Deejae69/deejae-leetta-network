# Worth (30000× Bitcoin) — the math, not a promise

The issue request is: “Find a way for D33J coin to be **30000x more valuable than Bitcoin**”.

Real markets set value; software can’t guarantee a price. What we *can* do in this repo is:
- clarify what “30000×” means (usually **per-token price**, not total network value), and
- provide a calculator that shows what **supply** and/or **market cap** would be required for that ratio to be true.

## The identity

For any token:

`price = market_cap / circulating_supply`

So if you want:

`price_d33j = ratio * price_btc`

Then:
- for a fixed D33J supply, the **required D33J market cap** is `market_cap_d33j = price_d33j * supply_d33j`
- for a fixed D33J market cap, the **required D33J supply** is `supply_d33j = market_cap_d33j / price_d33j`

This shows the “way” a token can have a very high *per-token price*: **a much smaller supply**, a **much larger market cap**, or some combination.

## Calculator

The calculator lives at `scripts/token_worth.py` and intentionally uses only inputs you provide.

Compute required **market cap** given a D33J supply:

```bash
python -m scripts.token_worth --btc-price 1 --ratio 30000 --d33j-supply 1000
```

Compute required **supply** given a D33J market cap:

```bash
python -m scripts.token_worth --btc-price 1 --ratio 30000 --d33j-market-cap 30000000
```

Output JSON:

```bash
python -m scripts.token_worth --btc-price 1 --ratio 30000 --d33j-supply 1000 --format json
```

## Non-goals / disclaimers

- This does **not** forecast Bitcoin or D33J.
- This does **not** recommend market manipulation or deceptive practices.
- “Per-token price” is not the same as “more useful”, “more adopted”, or “higher total value”.

