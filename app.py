import streamlit as st
import pandas as pd
from database import init_db, save_draw, load_draws
from fairness import verify_server_seed, fetch_ethereum_block_hash, verify_zulti_result

st.set_page_config(page_title="NO.01 Zulti Analytics", page_icon="🔎", layout="wide")
init_db()
st.title("NO.01 — Zulti Analytics")
st.caption("Historical draw records • SHA-256 checks • Provably-fair verification")
tab1, tab2, tab3 = st.tabs(["Dashboard", "Historical Data", "Fairness Verification"])

with tab1:
    df = load_draws()
    a, b, c = st.columns(3)
    a.metric("Saved draws", len(df))
    b.metric("Latest draw", str(df.iloc[0]["draw_date"]) if not df.empty else "—")
    c.metric("Database", "SQLite")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No records yet. Import a CSV in Historical Data.")

with tab2:
    st.subheader("Import historical results")
    st.write("CSV columns: draw_date, numbers (example: 4 10 17 24 31 32); optional draw_id.")
    uploaded = st.file_uploader("Upload draw CSV", type=["csv"])
    if uploaded:
        try:
            data = pd.read_csv(uploaded)
            if not {"draw_date", "numbers"}.issubset(data.columns):
                st.error("CSV must contain draw_date and numbers.")
            else:
                added = skipped = 0
                for _, row in data.iterrows():
                    nums = [int(x) for x in str(row["numbers"]).replace(",", " ").split()]
                    ok, _ = save_draw(str(row["draw_date"]), str(row.get("draw_id", "")), nums, "CSV")
                    added += int(ok)
                    skipped += int(not ok)
                st.success(f"Imported {added}; skipped {skipped} invalid/duplicate records.")
        except Exception as e:
            st.error(f"CSV import failed: {e}")
    df = load_draws()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download saved CSV", df.to_csv(index=False), "zulti_historical_data.csv", "text/csv")

with tab3:
    st.subheader("Server seed commitment")
    st.caption("Use values shown on the relevant Zulti draw verification page. Never enter passwords, cookies, or private keys.")
    left, right = st.columns(2)
    with left:
        published = st.text_input("Published encrypted server-seed hash (SHA-256)")
        revealed = st.text_input("Revealed server seed", type="password")
        client_seed = st.text_input("Client seed (optional)")
        nonce = st.text_input("Nonce (optional)")
    with right:
        block_number = st.text_input("Ethereum block number (optional)")
        block_hash = st.text_input("Ethereum block hash (optional, 0x...)")
        actual = st.text_input("Published winning numbers", placeholder="4 10 17 24 31 32")
        max_num = st.number_input("Maximum selectable number", 1, 1000, 45)
        count = st.number_input("Winning-number count", 1, 100, 6)

    if st.button("Verify fairness", type="primary"):
        if not published.strip() or not revealed:
            st.error("Enter both published hash and revealed server seed.")
        else:
            matched, calculated = verify_server_seed(revealed, published)
            st.write("Calculated SHA-256 hash")
            st.code(calculated)
            if matched:
                st.success("MATCH — revealed seed produces the published SHA-256 hash.")
            else:
                st.error("MISMATCH — revealed seed does not produce the published hash.")
            if client_seed or nonce:
                st.info("Client seed/nonce recorded as reference only. They are not inputs in the algorithm published on Zulti's fairness page.")
            if block_number.strip():
                try:
                    chain_hash = fetch_ethereum_block_hash(block_number.strip())
                    if block_hash.strip():
                        if chain_hash.lower() == block_hash.strip().lower():
                            st.success("Ethereum block hash MATCH.")
                        else:
                            st.error(f"Ethereum block hash MISMATCH. RPC returned {chain_hash}")
                    else:
                        st.info(f"Ethereum RPC block hash: {chain_hash}")
                except Exception as e:
                    st.warning(f"Block lookup unavailable: {e}")
            if actual.strip():
                actual_nums = [int(x) for x in actual.replace(",", " ").split()]
                result = verify_zulti_result(revealed, block_hash.strip(), actual_nums, int(max_num), int(count))
                if result["status"] == "MATCH":
                    st.success("DRAW RESULT MATCH — exact published Elixir algorithm reproduced the numbers.")
                    st.write("Reproduced winning numbers:", result["numbers"])
                elif result["status"] == "MISMATCH":
                    st.error(result["message"])
                    st.write("Reproduced winning numbers:", result["numbers"])
                else:
                    st.warning(result["message"])
            else:
                st.info("Enter the published winning numbers to compare the reproduced result.")

st.divider()
st.caption("This tool verifies supplied evidence. It does not predict winning numbers or access private accounts.")
