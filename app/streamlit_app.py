import re, time, pandas as pd, streamlit as st
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parents[1]
INDEX = pd.read_parquet(BASE/'data'/'meta'/'book_index.parquet')
NATS  = ['American','British','Canadian']
COLORS= {'American':'#1f77b4', 'British':'#ff7f0e', 'Canadian':'#2ca02c'}

st.title("Substring frequency in Project Gutenberg by author nationality")

query = st.text_input("Enter substring (case insensitive):", "")
go    = st.button("Search")
if go and query.strip():
    query = query.lower()
    # containers for counts over years and for examples
    counts = defaultdict(lambda: defaultdict(int))
    examples = defaultdict(list)

    prog_bar = st.progress(0.0, text="Scanning books…")
    for i,(row) in enumerate(INDEX.itertuples()):
        txt = Path(row.path).read_text(encoding='utf8')
        matches = [m for m in re.finditer(re.escape(query), txt)]
        if matches:
            counts[row.nationality][row.year] += len(matches)
            # keep up to 5 excerpts per nationality
            for m in matches[:2]:
                start=max(0,m.start()-300); end=min(len(txt),m.end()+300)
                snippet = txt[start:end]
                examples[row.nationality].append("…"+snippet+"…")
        prog_bar.progress((i+1)/len(INDEX))
    prog_bar.empty()

    # Convert counts dict → DataFrame
    freq = (pd.DataFrame(counts)
              .fillna(0).astype(int)
              .sort_index())
    st.line_chart(freq, use_container_width=True, color=[COLORS.get(c) for c in freq.columns])

    st.subheader("Examples")
    for nat,color in COLORS.items():
        if examples[nat]:
            with st.container():
                st.markdown(f"<div style='background:{color}10;padding:0.5em;border-radius:5px;'>"
                            f"<b>{nat}</b><br>"+"<br><br>".join(examples[nat][:3])+"</div>",
                            unsafe_allow_html=True)
else:
    st.info("Enter a substring and press **Search**.")

