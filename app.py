import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="UrbanPulse Command Center", page_icon="🚦", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("UrbanPulse_Dataset.xlsx")
    # auto-detect date columns
    for c in df.columns:
        if df[c].dtype == "object" and any(k in c.lower() for k in ["date", "time"]):
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().mean() > 0.8:
                df[c] = parsed
    return df

df = load_data()

date_cols = df.select_dtypes("datetime").columns.tolist()
num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = [c for c in df.select_dtypes(["object", "category"]).columns if df[c].nunique() <= 30]

# ---------- Sidebar filters ----------
st.sidebar.title("🚦 Filters")
for c in cat_cols[:3]:
    options = sorted(df[c].dropna().unique())
    chosen = st.sidebar.multiselect(c, options, default=options)
    df = df[df[c].isin(chosen)]

if date_cols:
    dcol = date_cols[0]
    lo, hi = df[dcol].min().date(), df[dcol].max().date()
    start, end = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    df = df[(df[dcol].dt.date >= start) & (df[dcol].dt.date <= end)]

# ---------- Header + KPIs ----------
st.title("🚦 UrbanPulse Smart City Command Center")
st.caption("Synthetic smart-city dataset · Traffic, Environment, Utilities, Public Safety")

kpi_cols = st.columns(min(5, len(num_cols)))
for col, name in zip(kpi_cols, num_cols[:5]):
    col.metric(f"Avg {name}", f"{df[name].mean():,.1f}")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "📊 Breakdown", "🗺️ Map", "🗃️ Data"])

with tab1:
    if date_cols:
        metric = st.selectbox("Metric", num_cols, key="trend_metric")
        ts = df.set_index(date_cols[0])[metric].resample("D").mean().reset_index()
        st.plotly_chart(px.line(ts, x=date_cols[0], y=metric), use_container_width=True)
    else:
        st.info("No date column detected.")

with tab2:
    if cat_cols:
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Group by", cat_cols)
        metric = c2.selectbox("Metric", num_cols, key="bar_metric")
        grp = df.groupby(cat)[metric].mean().reset_index().sort_values(metric, ascending=False)
        st.plotly_chart(px.bar(grp, x=cat, y=metric, color=metric), use_container_width=True)
        st.plotly_chart(px.pie(grp, names=cat, values=metric, hole=0.5), use_container_width=True)

with tab3:
    lat = next((c for c in df.columns if c.lower() in ("lat", "latitude")), None)
    lon = next((c for c in df.columns if c.lower() in ("lon", "lng", "longitude")), None)
    if lat and lon:
        st.map(df[[lat, lon]].dropna().rename(columns={lat: "latitude", lon: "longitude"}))
    else:
        st.info("No latitude/longitude columns found.")

with tab4:
    st.dataframe(df.head(1000), use_container_width=True)
    st.download_button("Download filtered CSV", df.to_csv(index=False), "urbanpulse_filtered.csv")