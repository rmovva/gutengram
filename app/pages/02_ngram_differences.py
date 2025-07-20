import json, math, pandas as pd, plotly.express as px, streamlit as st
from streamlit_plotly_events import plotly_events
from pathlib import Path
BASE = Path(__file__).resolve().parents[2]
STATS = pd.read_parquet(BASE/'data'/'processed'/'ngram_stats.parquet')
EX_PATH = BASE/'data'/'processed'/'ngram_examples.jsonl'

st.title("N‑grams that differ most between American and British authors")

min_tot = st.slider("Min overall count", 50, 1000, 200, step=50)
min_log = st.slider("|log₂ ratio| ≥", 0.0, 4.0, 1.0, step=0.5)

df = STATS.query("total>=@min_tot and abs(log_ratio)>=@min_log")
fig = px.scatter(df, x="total", y="log_ratio",
                 hover_name="ngram", color="len",
                 labels={"total":"Total count (log10)",
                         "log_ratio":"log₂(Amer/Brit)"},
                 size=df["total"]**0.3,
                 log_x=True,
                 height=600)
selected = plotly_events(fig, click_event=True)
if selected:
    ng = df.iloc[selected[0]['pointIndex']]['ngram']
    st.subheader(f"Examples for “{ng}”")
    # look up excerpts
    ex_A, ex_B = [], []
    with open(EX_PATH,encoding='utf8') as f:
        for line in f:
            d = json.loads(line)
            if d['ngram']==ng:
                (ex_A if d['nat']=="American" else ex_B).extend(d['ex'])
    colA,colB = st.columns(2)
    with colA:
        st.markdown("**American:**")
        for t in ex_A[:3]:
            st.info(t.replace(ng, f"**{ng}**"))
    with colB:
        st.markdown("**British:**")
        for t in ex_B[:3]:
            st.warning(t.replace(ng, f"**{ng}**"))
else:
    st.plotly_chart(fig, use_container_width=True)

