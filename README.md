# NO.01 — Zulti Analytics

## Features
- Streamlit dashboard and SQLite history.
- CSV historical-results import/export.
- SHA-256 verification: revealed server seed vs published hash.
- Optional Ethereum block hash lookup through a configured JSON-RPC endpoint.
- Winning-number reproduction using Zulti's published Elixir code, when Elixir is installed.
- Clear MATCH / MISMATCH / UNAVAILABLE states.

## Zulti algorithm facts
Zulti's public Provably Fair page documents a SHA-256 commitment and uses the revealed server seed plus the selected Ethereum block hash. Its published Elixir algorithm is:
```elixir
:rand.seed(:default, :erlang.phash2([server_seed, ethereum_block_hash]))
1..max_selectable_number |> Enum.to_list() |> Enum.shuffle()
|> Enum.take(selectable_numbers_count) |> Enum.sort()
```
The published example uses maximum 45 and count 6. The app defaults to these values; verify the relevant draw's settings before changing them. Client seed and nonce are not inputs in this published algorithm, so the app does not pretend to verify them.

Python's random module is NOT equivalent to Erlang's RNG. Exact reproduction invokes the published Elixir expression. If Elixir is not installed in the deployment environment, the app reports UNAVAILABLE instead of fabricating winning numbers. SHA-256 verification remains available.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional Ethereum RPC
Set `ETHEREUM_RPC_URL` as an environment variable or Streamlit secret:
```toml
ETHEREUM_RPC_URL = "https://YOUR-ETHEREUM-RPC-ENDPOINT"
```
Never commit API keys or secrets.

## CSV format
Required columns: `draw_date`, `numbers`. Optional: `draw_id`.
Example: `2026-11-08,4 10 17 24 31 32`

The database validator currently follows Zulti's public example of six unique numbers from 1–45. Adjust only after confirming the relevant draw format.

## Automatic collection
No undocumented/private endpoint scraping is included. Automatic collection requires an official/public Zulti API or an authorized export and its documented schema. The GitHub workflow validates CSV files placed in `data/import/`; it does not claim to fetch Zulti data automatically.

## Deploy
Upload this folder's contents to GitHub repository `NO01-Zulti-Analytics`, then deploy `app.py` in Streamlit Community Cloud. Local Streamlit storage can be ephemeral; use durable external storage for production history.
