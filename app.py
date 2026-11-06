import json
from pathlib import Path
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Veridi · Last Mile Delivery Audit", page_icon="📦", layout="wide")
D = json.loads((Path(__file__).parent / "dashboard_data.json").read_text())
RC = {"North": "#7B5EA7", "Northeast": "#C0392B", "Central-West": "#E69F00", "Southeast": "#1F3A5F", "South": "#2E8B57"}
pct = lambda x, d=1: f"{x*100:.{d}f}%"

st.title("📦 Last Mile Logistics Audit")
st.caption("Veridi Logistics · Olist data · 96,470 delivered orders (Sep 2016 – Aug 2018)")
st.success("**Answer for the CEO: it is regional, not nationwide.** "
           f"Only {pct(D['overall']['late_pct'])} of orders miss the promised date and the typical parcel arrives "
           f"{D['overall']['median_days_early']:.0f} days early. Failures cluster in the Northeast and Rio de Janeiro.")

ne = D["region"][0]
c = st.columns(4)
c[0].metric("Orders late (any)", pct(D["overall"]["late_pct"]))
c[1].metric("Super late (>5 days)", pct(D["overall"]["super_late_pct"]))
c[2].metric("Review: on time → super late", f"{D['status']['On Time']['avg_review']:.2f} → {D['status']['Super Late']['avg_review']:.2f}")
c[3].metric("Northeast: share of late vs volume", f"{pct(ne['share_late'])} vs {pct(ne['share_orders'])}")

df = pd.DataFrame(D["state"])
t1, t2, t3, t4, t5 = st.tabs(["1 · Where?", "2 · Sentiment", "3 · Regions", "4 · Recalibrated ETA", "5 · Bonus: categories"])

with t1:
    metric = st.radio("Metric", ["Late %", "Super late %", "Avg review"], horizontal=True)
    region = st.multiselect("Regions", list(RC), default=list(RC))
    col = {"Late %": "late", "Super late %": "super", "Avg review": "review"}[metric]
    min_n = st.slider("Minimum delivered orders per state", 0, 1000, 100, 50)
    v = df[df.region.isin(region) & (df.n >= min_n)].copy()
    if col != "review":
        v[col] = v[col] * 100
    chart = (alt.Chart(v).mark_bar().encode(
        y=alt.Y("st:N", sort="-x" if col != "review" else "x", title="State"),
        x=alt.X(f"{col}:Q", title=metric),
        color=alt.Color("region:N", scale=alt.Scale(domain=list(RC), range=list(RC.values()))),
        tooltip=["st", "region", "n", alt.Tooltip(col, format=".2f")]).properties(height=max(300, 22 * len(v))))
    st.altair_chart(chart, width="stretch")
    st.caption("Hide small states with the slider: states under 100 orders swing wildly on a handful of parcels.")

with t2:
    st.write("Average review score (1–5) by delivery outcome; the drop is a cliff the moment the promise is broken.")
    a, b = st.columns(2)
    s = pd.DataFrame([{"status": k, "avg_review": v["avg_review"]} for k, v in D["status"].items()])
    a.altair_chart(alt.Chart(s).mark_bar().encode(
        x=alt.X("status:N", sort=["On Time", "Late", "Super Late"]), y=alt.Y("avg_review:Q", scale=alt.Scale(domain=[0, 5])),
        color=alt.Color("status:N", legend=None, scale=alt.Scale(domain=["On Time", "Late", "Super Late"], range=["#2E8B57", "#E69F00", "#C0392B"]))),
        width="stretch")
    cv = pd.DataFrame(D["curve"])
    cv["kind"] = cv.bucket.str.contains("late").map({True: "late", False: "on time / early"})
    b.altair_chart(alt.Chart(cv).mark_bar().encode(
        x=alt.X("bucket:N", sort=list(cv.bucket), title="Delivery delay"), y=alt.Y("review:Q", scale=alt.Scale(domain=[0, 5])),
        color=alt.Color("kind:N", legend=None, scale=alt.Scale(domain=["late", "on time / early"], range=["#C0392B", "#2E8B57"]))),
        width="stretch")
    b.caption("Left buckets (late) average 1.7–3.0; on-time and early buckets 4.0–4.3.")

with t3:
    r = pd.DataFrame(D["region"]).rename(columns={"n": "orders", "late": "late %", "share_orders": "share of orders", "share_late": "share of late", "review": "avg review"})
    for k in ["late %", "share of orders", "share of late"]:
        r[k] = (r[k] * 100).round(1)
    st.dataframe(r, hide_index=True, width="stretch")
    st.info(f"Distance from São Paulo explains little: Spearman ρ(distance, late rate) = {D['rho_late']:+.2f}. "
            "The far North has 40+ day promises; the Northeast does not.")
    m = pd.DataFrame(D["monthly"])
    st.altair_chart(alt.Chart(m).mark_line(point=True, color="#C0392B").encode(
        x=alt.X("m:N", title="Month"), y=alt.Y("late:Q", axis=alt.Axis(format="%"), title="Late rate"), tooltip=["m", "n", alt.Tooltip("late", format=".1%")]),
        width="stretch")

with t4:
    st.write("**Candidate’s choice.** Days to add to today’s estimate so that 95% of orders would have arrived on time "
             "(states with 100+ orders). It turns the diagnosis into a fix per state and shows where Veridi over-pads and could promise faster.")
    e = df[df.n >= 100].sort_values(["extra95", "late"], ascending=False).copy()
    e["late %"] = (e.late * 100).round(1)
    e["new promise"] = (e.promised + e.extra95).round(0)
    st.dataframe(e[["st", "region", "n", "promised", "actual", "late %", "extra95", "new promise"]]
                 .rename(columns={"st": "state", "extra95": "add days", "n": "orders"}), hide_index=True, width="stretch")
    L, O = D["stage"]["Late"], D["stage"]["On Time"]
    st.caption(f"Late orders: seller handling {L['seller_handling_days']} vs {O['seller_handling_days']} days (on time); "
               f"carrier transit {L['carrier_transit_days']} vs {O['carrier_transit_days']} days. The carrier leg is the bigger problem.")

with t5:
    st.write("**Is Furniture harder to ship than Electronics?** Only slightly. Category moves late rates between ~4% and ~12%; "
             "state moves them between ~3% and ~21%, so geography is the bigger lever.")
    g = pd.DataFrame(D["groups"])
    for k in ["late", "exp", "sp"]:
        g[k] = (g[k] * 100).round(1)
    st.dataframe(g.rename(columns={"g": "group", "n": "orders", "late": "late %", "exp": "expected late % (same states)", "sp": "late % (SP only)",
                                   "review": "avg review", "days": "avg days", "kg": "avg kg"}), hide_index=True, width="stretch")
    st.caption(f"Expected = late rate if the group shipped like the average order to the same states. Product weight is not a driver (Spearman {D['rho_weight']:+.2f}).")
    cat = pd.DataFrame(D["category"])
    cat["late %"] = cat.late * 100
    cat["vs national"] = (cat.late > D["overall"]["late_pct"]).map({True: "above average", False: "below average"})
    st.altair_chart(alt.Chart(cat).mark_bar().encode(
        y=alt.Y("c:N", sort="-x", title="Category (English)"), x=alt.X("late %:Q", title="% late"),
        color=alt.Color("vs national:N", scale=alt.Scale(domain=["above average", "below average"], range=["#C0392B", "#2E8B57"])),
        tooltip=["c", "n", alt.Tooltip("late %", format=".1f")]), width="stretch")
    st.caption("8 worst and 5 best categories with 300+ delivered orders.")
