# ZULTI NO.01 — Android-friendly starter

## Android par kaise chalayein
Sabse aasaan tareeqa: project ko GitHub par upload karein, phir Streamlit Community Cloud par deploy karein. Android Chrome se dashboard URL khol sakte hain. Local Android/Pydroid par dependencies install karna device ke hisaab se mushkil ho sakta hai.

## Computer / cloud par install
1. Python 3.10+ install karein.
2. Is folder ko extract karein.
3. Terminal mein:
   `pip install -r requirements.txt`
4. Run:
   `streamlit run app.py`
5. Browser mein Streamlit ka diya hua local URL kholein.

## Data format
CSV/Excel mein `draw_date,n1,n2,n3,n4,n5,n6` columns rakhein. Zulti ke published example format mein 1–45 pool se 6 unique numbers hain. `sample_draws.csv` mein examples hain; ye sirf format demo hain, complete historical data nahi.

## Automatic website collection
Collect data tab mein public results URL daalein. Optional CSS selector use karein, jaise `.draw-card`. Generic extraction sirf candidate number sequences dhoondhta hai. Import se pehle source page se har row verify karein. Zulti ka stable public API/selector is starter mein assume nahi kiya gaya; page JavaScript se render hota ho to manual import ya a dedicated authorized adapter chahiye.

## NO.01 ranking
Eight-number shortlist transparent heuristic score use karti hai: 70% historical frequency normalization + 30% time-since-last-seen normalization. Score probability nahi hai aur fair random draw mein future outcome ko predict nahi karta.

## Provably fair
SHA-256 section revealed server seed ka hash supplied published hash se compare karta hai. Ethereum section JSON-RPC se block hash fetch karta hai. Ye dono checks alag-alag hain. Zulti ke actual winning numbers ko independently reproduce karne ke liye exact inputs, algorithm aur compatible Erlang/OTP RNG behavior chahiye. Seed hash match ko complete draw verification na samjhein.

## Safety / access
Public pages only. Login, CAPTCHA, paywall, rate limits, or access controls bypass nahi hote. Private account cookies/passwords is app mein paste na karein. Respect site terms and robots/access rules.

## Files
- `app.py`: Streamlit UI
- `analytics.py`: frequency, pairs, triples, gaps, shortlist
- `database.py`: SQLite storage and deduplication
- `sources.py`: public page fetch and candidate extraction
- `verification.py`: SHA-256 and Ethereum RPC checks
- `sample_draws.csv`: sample import format
