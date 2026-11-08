import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
from analytics import analyze, recommend_eight, number_universe
from database import init_db, save_draws, load_draws
from sources import fetch_public_page, extract_candidate_draws
from verification import verify_server_seed, fetch_ethereum_block_hash

st.set_page_config(page_title="ZULTI NO.01 Analytics", page_icon="🔢", layout="wide")
init_db()

st.title("ZULTI.COM — NO.01 | 8-Number Analytics")
st.caption("Historical statistics and transparent verification. This tool does not predict or guarantee random outcomes.")

with st.sidebar:
    st.header("Draw configuration")
    max_number = st.number_input("Maximum number", min_value=8, max_value=200, value=45, step=1)
    draw_size = st.number_input("Numbers in each actual draw", min_value=1, max_value=int(max_number), value=6, step=1)
    st.caption("Zulti's published example uses 6 numbers from 1–45. NO.01 ranks 8 shortlist numbers from that pool.")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Collect data", "Manual / file import", "Fairness verification"])

with tab1:
    draws = load_draws()
    if draws.empty:
        st.info("No historical draws stored yet. Import a CSV/Excel file or collect public page candidates.")
    else:
        st.metric("Stored draws", len(draws))
        stats = analyze(draws, int(max_number), int(draw_size))
        picks = recommend_eight(stats, int(max_number))
        cols = st.columns(4)
        cols[0].metric("Draw records", len(draws))
        cols[1].metric("Unique numbers seen", int(draws["numbers"].explode().nunique()))
        cols[2].metric("Number pool", int(max_number))
        cols[3].metric("Actual draw size", int(draw_size))
        st.subheader("NO.01 — Recommended 8-number shortlist")
        st.caption("Ranking is descriptive/statistical only. It is not a forecast or an advantage in a fair random draw.")
        st.dataframe(pd.DataFrame(picks), use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.write("**Hot numbers**")
        c1.write(", ".join(map(str, stats["hot"])))
        c2.write("**Cold numbers**")
        c2.write(", ".join(map(str, stats["cold"])))
        c3.write("**Most overdue**")
        c3.write(", ".join(map(str, stats["overdue"])))
        st.subheader("Number frequency")
        st.bar_chart(pd.DataFrame({"Number": list(stats["frequency"].keys()), "Frequency": list(stats["frequency"].values())}).set_index("Number"))
        st.subheader("Most frequent pairs")
        st.dataframe(pd.DataFrame(stats["pairs"], columns=["Pair", "Count"]).head(15), use_container_width=True, hide_index=True)
        st.subheader("Most frequent triples")
        st.dataframe(pd.DataFrame(stats["triples"], columns=["Triple", "Count"]).head(15), use_container_width=True, hide_index=True)
        out = pd.DataFrame(picks)
        st.download_button("Download 8-number shortlist (CSV)", out.to_csv(index=False), "no01_recommendations.csv", "text/csv")
        st.download_button("Download historical data (CSV)", draws.drop(columns=["numbers"]).to_csv(index=False), "no01_history.csv", "text/csv")
        xlsx_buffer = BytesIO()
        with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
            out.to_excel(writer, sheet_name="Top 8", index=False)
            draws.drop(columns=["numbers"]).to_excel(writer, sheet_name="History", index=False)
        st.download_button("Download Excel report", xlsx_buffer.getvalue(), "no01_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab2:
    st.subheader("Automatic public-page collection")
    st.warning("Only fetch public pages you are allowed to access. This starter does not bypass logins, CAPTCHAs, paywalls, rate limits, or access controls.")
    url = st.text_input("Public results page URL", value="https://zulti.com/")
    selector = st.text_input("Optional CSS selector for result cards", placeholder=".draw-card")
    if st.button("Fetch page and preview candidates"):
        try:
            html, page_text = fetch_public_page(url)
            candidates = extract_candidate_draws(html, selector.strip() or None, int(max_number), int(draw_size))
            st.write(f"Fetched public page: {url}")
            if candidates:
                preview = pd.DataFrame(candidates)
                st.dataframe(preview, use_container_width=True, hide_index=True)
                st.caption("Check every candidate against the source website before importing. Automatic extraction can misread page layouts.")
                if st.button("Import preview candidates"):
                    saved = save_draws(preview)
                    st.success(f"Imported {saved} new records.")
            else:
                st.info("No reliable draw candidates detected. The page may be JavaScript-rendered or use a different layout. Use manual CSV/Excel import or configure a site-specific adapter.")
            with st.expander("Page text preview"):
                st.text(page_text[:5000])
        except Exception as e:
            st.error(f"Could not fetch page: {e}")

with tab3:
    st.subheader("Import historical results")
    st.markdown("Required columns: `draw_date`, `n1` … `n6` (for a six-number draw). Optional: `source`, `draw_id`. For other draw sizes, include exactly the configured number of number columns.")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(df.head(20), use_container_width=True)
            if st.button("Validate and import file"):
                number_cols = [c for c in df.columns if str(c).lower().startswith("n") and str(c)[1:].isdigit()]
                if len(number_cols) != int(draw_size):
                    st.error(f"Expected {int(draw_size)} number columns named n1...n{int(draw_size)}; found {len(number_cols)}.")
                else:
                    rows = []
                    for _, r in df.iterrows():
                        rows.append({"draw_date": str(r.get("draw_date", "")), "numbers": [int(r[c]) for c in number_cols], "source": str(r.get("source", "file")), "draw_id": str(r.get("draw_id", ""))})
                    saved = save_draws(pd.DataFrame(rows))
                    st.success(f"Imported {saved} new valid records.")
        except Exception as e:
            st.error(f"Import error: {e}")
    st.markdown("**Manual entry**")
    date = st.text_input("Draw date / identifier", placeholder="2026-11-08")
    nums = st.text_input(f"Enter {int(draw_size)} numbers separated by commas", placeholder="1, 6, 18, 20, 27, 39")
    if st.button("Add manual draw"):
        try:
            values = [int(x.strip()) for x in nums.split(",")]
            if len(values) != int(draw_size) or len(set(values)) != len(values) or min(values) < 1 or max(values) > int(max_number):
                raise ValueError("Wrong count, duplicate numbers, or number outside configured range.")
            saved = save_draws(pd.DataFrame([{"draw_date": date, "numbers": values, "source": "manual", "draw_id": ""}]))
            st.success(f"Saved {saved} record(s).")
        except Exception as e:
            st.error(str(e))

with tab4:
    st.subheader("SHA-256 commitment check")
    server_seed = st.text_input("Revealed server seed", type="password")
    published_hash = st.text_input("Published SHA-256 hash")
    if st.button("Verify server seed"):
        ok, computed = verify_server_seed(server_seed, published_hash)
        st.code(computed)
        st.success("PASS — seed matches the published hash.") if ok else st.error("FAIL — seed does not match the supplied hash.")
    st.divider()
    st.subheader("Ethereum block hash lookup")
    block_number = st.number_input("Ethereum block number", min_value=0, value=0, step=1)
    rpc_url = st.text_input("Ethereum JSON-RPC URL", value="https://cloudflare-eth.com")
    expected_hash = st.text_input("Published block hash (optional)")
    if st.button("Fetch and compare block hash"):
        try:
            actual = fetch_ethereum_block_hash(int(block_number), rpc_url)
            st.code(actual)
            if expected_hash.strip():
                st.success("PASS — block hash matches.") if actual.lower() == expected_hash.strip().lower() else st.error("FAIL — block hash mismatch.")
            else:
                st.info("Block hash retrieved. Enter the draw's published hash to compare.")
        except Exception as e:
            st.error(str(e))
    st.info("A seed-hash match and block-hash match do not alone reproduce Zulti's winning numbers. Exact reproduction also requires the precise algorithm, inputs, and compatible Erlang/OTP RNG behavior.")
