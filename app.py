from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────────────────────
#  UrbanPulse Smart City Command Center  (Streamlit edition)
#  Layout, colours and pages follow the original Power BI report.
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UrbanPulse Smart City Command Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "UrbanPulse_Dataset.xlsx"
FOOTER = "UrbanPulse Smart City Command Center | Synthetic Dataset | Original Power BI report by Shardul Rane"

BLUE, NAVY, RED, WHITE = "#118DFF", "#12239E", "#D64550", "#FFFFFF"
PALETTE = ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7",
           "#744EC2", "#D9B300", "#D64550", "#197278", "#1AAB40"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PAGES = ["Executive Overview", "Traffic Analytics", "Environment",
         "Utilities", "Public Safety", "AI Insights"]
# If the map background is blank, pick "No basemap" (needs no internet tiles)
MAP_STYLES = {
    "Light map (Carto)": "carto-positron",
    "Dark map (Carto)": "carto-darkmatter",
    "Street map (OSM)": "open-street-map",
    "No basemap (always works)": "white-bg",
}

# Streamlit renamed use_container_width -> width="stretch" in newer versions
_NEW = tuple(int(p) for p in st.__version__.split(".")[:2]) >= (1, 50)
STRETCH = {"width": "stretch"} if _NEW else {"use_container_width": True}

# ──────────────────────────────  STYLE  ──────────────────────────────
st.markdown(
    """
<style>
.stApp {background:#0E1628;}
header[data-testid="stHeader"] {background:transparent;}
#MainMenu, footer {visibility:hidden;}
.block-container {padding-top:1rem; padding-bottom:0.5rem; max-width:100%;}

section[data-testid="stSidebar"] {background:#0A1020; min-width:235px; max-width:235px;}
section[data-testid="stSidebar"] .block-container {padding-top:1rem;}
.side-h {font-size:1.9rem; font-weight:700; color:#fff; margin:0 0 .4rem 0;}
section[data-testid="stSidebar"] label p {font-weight:600; color:#fff;}

section[data-testid="stSidebar"] [data-testid^="stBaseButton"] {
    border-radius:18px; border:none; border-left:6px solid #118DFF;
    min-height:46px; margin-bottom:2px;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {background:#fff !important;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {color:#111 !important; font-weight:500;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {background:#1F1F23 !important;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p {color:#fff !important; font-weight:600;}

.ptitle {text-align:center; font-size:2.6rem; font-weight:700; color:#fff; line-height:1.15; margin:0;}
.psub {text-align:center; color:#B8C0D0; margin:0 0 .5rem 0;}
.ctitle {font-size:1.25rem; font-weight:700; color:#fff; margin:.6rem 0 0 0;}

.kpi-band {display:grid; gap:12px; background:#15233F; padding:12px; border-radius:6px; margin:.5rem 0 .4rem 0;}
.kpi-band.narrow {max-width:75%; margin-left:auto; margin-right:auto;}
.kpi {background:#fff; border-radius:12px; border-left:7px solid #118DFF; padding:10px 14px;
      display:flex; justify-content:space-between; align-items:center; min-height:78px;}
.kpi-val {font-size:2.3rem; font-weight:400; color:#111; line-height:1.05;}
.kpi-lab {font-size:.8rem; color:#444;}
.kpi-ico {font-size:2.1rem;}

.foot {text-align:center; color:#fff; font-size:.75rem; font-weight:600; margin-top:.8rem;}
.insight {color:#fff; font-size:.95rem; line-height:1.45;}
.insight b {font-size:1.05rem;}
</style>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────  DATA  ──────────────────────────────
@st.cache_data(show_spinner="Loading city data…")
def load_data():
    path = Path(__file__).parent / DATA_FILE
    s = pd.read_excel(path, sheet_name=None)
    return (
        s["Fact_CityOperations"]
        .merge(s["Dim_Date"], on="Date_ID", how="left")
        .merge(s["Dim_Time"], on="Time_ID", how="left")
        .merge(s["Dim_Zone"], on="Zone_ID", how="left")
        .merge(s["Dim_Weather"], on="Weather_ID", how="left")
        .merge(s["Dim_Event"], on="Event_ID", how="left")
    )


try:
    data = load_data()
except FileNotFoundError:
    st.error(f"Could not find {DATA_FILE}. Keep it in the same folder as app.py.")
    st.stop()


# ──────────────────────────────  HELPERS  ──────────────────────────────
def hum(v, small=0, big=0):
    """Human-readable number: 1,250,000 -> 1M (big=0) or 1.3M (big=1)."""
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:.{big}f}B"
    if a >= 1e6:
        return f"{v / 1e6:.{big}f}M"
    if a >= 1e3:
        return f"{v / 1e3:.{big}f}K"
    return f"{v:.{small}f}"


def kpi_row(items):
    cards = "".join(
        f'<div class="kpi"><div><div class="kpi-val">{val}</div>'
        f'<div class="kpi-lab">{label}</div></div><div class="kpi-ico">{icon}</div></div>'
        for label, val, icon in items
    )
    cls = "kpi-band narrow" if len(items) < 4 else "kpi-band"
    st.markdown(
        f'<div class="{cls}" style="grid-template-columns:repeat({len(items)},1fr)">{cards}</div>',
        unsafe_allow_html=True,
    )


def page_title(text, sub=None):
    st.markdown(f'<div class="ptitle">{text}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="psub">{sub}</div>', unsafe_allow_html=True)


def ctitle(text):
    st.markdown(f'<div class="ctitle">{text}</div>', unsafe_allow_html=True)


def footer():
    st.markdown(f'<div class="foot">{FOOTER}</div>', unsafe_allow_html=True)


def base(fig, h=300, legend=False):
    fig.update_layout(
        height=h,
        margin=dict(l=0, r=8, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE, size=12),
        showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    grid = dict(gridcolor="rgba(255,255,255,0.14)", griddash="dot", zeroline=False)
    fig.update_xaxes(**grid, linecolor="rgba(0,0,0,0)")
    fig.update_yaxes(**grid, linecolor="rgba(0,0,0,0)")
    return fig


def show(fig, key):
    st.plotly_chart(fig, key=key, config={"displayModeBar": False}, **STRETCH)


def by_month(df, col, agg="sum"):
    g = df.groupby("Month")[col].agg(agg).reindex(range(1, 13)).reset_index()
    g["Mon"] = g["Month"].map(lambda m: MONTHS[m - 1])
    return g.dropna(subset=[col])


def hbar(d, cat, val, key, n=8, small=0, big=1, h=300):
    d = d.sort_values(val, ascending=False).head(n)
    fig = go.Figure(go.Bar(
        x=d[val], y=d[cat], orientation="h", marker_color=BLUE,
        text=[hum(v, small, big) for v in d[val]],
        textposition="inside", insidetextanchor="end", textfont=dict(color=WHITE),
    ))
    base(fig, h)
    fig.update_yaxes(autorange="reversed", title=None, showgrid=False)
    fig.update_xaxes(title=None)
    show(fig, key)


def vbar(d, cat, val, key, small=0, big=1, h=300, order=None):
    d = d.sort_values(val, ascending=False) if order is None else d
    fig = go.Figure(go.Bar(
        x=d[cat], y=d[val], marker_color=BLUE,
        text=[hum(v, small, big) for v in d[val]],
        textposition="outside", cliponaxis=False, textfont=dict(color=WHITE),
    ))
    base(fig, h)
    fig.update_xaxes(title=None, showgrid=False, tickangle=-35)
    fig.update_yaxes(title=None)
    show(fig, key)


def line_chart(x, series, key, h=300, area=False, tick=".2s"):
    """series = [(name, values, colour), ...]"""
    fig = go.Figure()
    for name, ys, colour in series:
        fig.add_scatter(
            x=x, y=ys, name=name, mode="lines+markers",
            line=dict(color=colour, width=3), marker=dict(size=8),
            fill="tozeroy" if area else None,
            fillcolor="rgba(17,141,255,0.30)" if area else None,
        )
    base(fig, h, legend=len(series) > 1)
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, tickformat=tick)
    if area:
        lo, hi = min(series[0][1]), max(series[0][1])
        fig.update_yaxes(range=[lo - (hi - lo) * 0.3, hi + (hi - lo) * 0.1])
    show(fig, key)


def combo_chart(x, bar, line, key, h=300):
    """bar = (name, values), line = (name, values) on a secondary axis."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=x, y=bar[1], name=bar[0], marker_color=BLUE, secondary_y=False)
    fig.add_scatter(
        x=x, y=line[1], name=line[0], mode="lines+markers",
        line=dict(color=WHITE, width=3), marker=dict(size=8), secondary_y=True,
    )
    base(fig, h, legend=True)
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, showgrid=True, secondary_y=False)
    fig.update_yaxes(title=None, showgrid=False, secondary_y=True)
    show(fig, key)


def zone_map(df, size_col, key, h):
    z = df.groupby(["Zone_Name", "Latitude", "Longitude"], as_index=False)[size_col].sum()
    style = MAP_STYLES[map_choice]
    kw = dict(lat="Latitude", lon="Longitude", size=size_col, hover_name="Zone_Name",
              zoom=9.1, size_max=15, color_discrete_sequence=[BLUE],
              hover_data={"Latitude": False, "Longitude": False})
    if style == "white-bg":
        kw["text"] = "Zone_Name"
    try:
        fig = px.scatter_map(z, map_style=style, **kw)
    except AttributeError:  # older plotly
        fig = px.scatter_mapbox(z, mapbox_style=style, **kw)
    if style == "white-bg":
        fig.update_traces(textposition="top center", textfont=dict(size=10, color="#333"))
    fig.update_layout(height=h, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)")
    show(fig, key)


# ──────────────────────────────  SIDEBAR  ──────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = PAGES[0]


def go_to(page):
    st.session_state.page = page


with st.sidebar:
    st.markdown('<div class="side-h">Navigation 📍</div>', unsafe_allow_html=True)
    for p in PAGES:
        st.button(p, key=f"nav_{p}", on_click=go_to, args=(p,),
                  type="primary" if st.session_state.page == p else "secondary",
                  **STRETCH)

    st.markdown('<div class="side-h" style="margin-top:1rem">Slicers 🔽</div>',
                unsafe_allow_html=True)
    month_names = (data.drop_duplicates("Month").sort_values("Month")["Month_Name"].tolist())
    f_month = st.selectbox("📅 Month", ["All"] + month_names)
    f_zone = st.selectbox("📍 Zone", ["All"] + sorted(data["Zone_Name"].unique()))
    f_weather = st.selectbox("⛅ Weather", ["All"] + sorted(data["Weather_Condition"].unique()))
    f_event = st.selectbox("🗓️ Event", ["All"] + sorted(data["Event_Name"].dropna().unique()))
    map_choice = st.selectbox("🗺️ Map style", list(MAP_STYLES))

df = data
if f_month != "All":
    df = df[df["Month_Name"] == f_month]
if f_zone != "All":
    df = df[df["Zone_Name"] == f_zone]
if f_weather != "All":
    df = df[df["Weather_Condition"] == f_weather]
if f_event != "All":
    df = df[df["Event_Name"] == f_event]

if df.empty:
    st.warning("No records match the selected slicers. Reset a filter to continue.")
    st.stop()


# ──────────────────────────────  PAGES  ──────────────────────────────
def page_executive():
    page_title("UrbanPulse Smart City Command Center", "Real-time Urban Operations Dashboard")
    kpi_row([
        ("City Health Score", hum(df.City_Health_Score.mean()), "❤️"),
        ("Average AQI", hum(df.AQI.mean()), "☁️"),
        ("Total Vehicles", hum(df.Vehicle_Count.sum()), "🚚"),
        ("Citizen Satisfaction", hum(df.Citizen_Satisfaction.mean()), "😊"),
        ("Total Emergency Calls", hum(df.Emergency_Calls.sum()), "📞"),
        ("Total Electricity", hum(df.Electricity_Consumption_kWh.sum()), "💡"),
    ])
    left, right = st.columns([3.1, 1.15], gap="medium")
    with left:
        c1, c2, c3 = st.columns([1.1, 1.5, 1.25])
        with c1:
            ctitle("Most Congested Zones")
            hbar(df.groupby("Zone_Name", as_index=False).Congestion_Index.mean(),
                 "Zone_Name", "Congestion_Index", "ex_cong", small=1)
        with c2:
            ctitle("Vehicle Trend")
            m = by_month(df, "Vehicle_Count")
            line_chart(m.Mon, [("Vehicles", m.Vehicle_Count, BLUE)], "ex_trend", area=True)
        with c3:
            ctitle("Average AQI by Weather")
            hbar(df.groupby("Weather_Condition", as_index=False).AQI.mean(),
                 "Weather_Condition", "AQI", "ex_aqi", n=6)
        c4, c5 = st.columns([1.7, 1.2])
        with c4:
            ctitle("Electricity vs Water Consumption")
            e, w = by_month(df, "Electricity_Consumption_kWh"), by_month(df, "Water_Consumption_KL")
            fig = go.Figure([
                go.Bar(x=e.Mon, y=e.Electricity_Consumption_kWh, name="Total Electricity", marker_color=BLUE),
                go.Bar(x=w.Mon, y=w.Water_Consumption_KL, name="Total Water", marker_color=NAVY),
            ])
            base(fig, 300, legend=True)
            fig.update_layout(barmode="group")
            fig.update_xaxes(title=None, showgrid=False)
            fig.update_yaxes(title=None, tickformat=".2s")
            show(fig, "ex_elec_water")
        with c5:
            ctitle("Emergency Calls by Event Type")
            ev = df[df.Event_Name != "Normal Day"].groupby("Event_Name", as_index=False).Emergency_Calls.sum()
            if ev.empty:
                st.info("No event records for this selection.")
            else:
                hbar(ev, "Event_Name", "Emergency_Calls", "ex_event")
    with right:
        ctitle("Traffic Density Map")
        zone_map(df, "Vehicle_Count", "ex_map", 655)
    footer()


def page_traffic():
    page_title("Traffic Analytics Dashboard")
    kpi_row([
        ("Total Vehicles", hum(df.Vehicle_Count.sum()), "🚚"),
        ("Average Congestion", hum(df.Congestion_Index.mean()), "🚦"),
        ("Total Accidents", hum(df.Accident_Count.sum()), "💥"),
        ("Total Bus Ridership", hum(df.Bus_Ridership.sum()), "🚌"),
        ("Total Metro Ridership", hum(df.Metro_Ridership.sum()), "🚇"),
    ])
    c1, c2, c3 = st.columns([2.2, 1.5, 1.3])
    with c1:
        ctitle("Traffic Congestion Trend")
        hr = df.groupby("Hour", as_index=False).Congestion_Index.mean()
        line_chart(hr.Hour, [("Avg Congestion", hr.Congestion_Index, BLUE)], "tr_hour", tick=".0f")
    with c2:
        ctitle("Most Congested Zones")
        hbar(df.groupby("Zone_Name", as_index=False).Congestion_Index.mean(),
             "Zone_Name", "Congestion_Index", "tr_cong", small=1)
    with c3:
        ctitle("Average Parking Utilization")
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=df.Parking_Occupancy.mean(),
            number={"font": {"size": 44, "color": WHITE}, "valueformat": ".0f"},
            gauge={"axis": {"range": [0, 100], "tickcolor": WHITE},
                   "bar": {"color": BLUE}, "bgcolor": "#F2F2F2", "borderwidth": 0,
                   "threshold": {"line": {"color": NAVY, "width": 4}, "thickness": 0.9, "value": 85}},
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(color=WHITE))
        show(fig, "tr_gauge")
    c4, c5, c6 = st.columns([1.5, 1.8, 1.5])
    with c4:
        ctitle("Vehicle Volume by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).Vehicle_Count.sum(),
             "Zone_Name", "Vehicle_Count", "tr_vol")
    with c5:
        ctitle("Public Transport Usage")
        b, mt = by_month(df, "Bus_Ridership"), by_month(df, "Metro_Ridership")
        combo_chart(b.Mon, ("Total Bus Ridership", b.Bus_Ridership),
                    ("Total Metro Ridership", mt.Metro_Ridership.values[: len(b)]), "tr_pt")
    with c6:
        ctitle("Accident Hotspots")
        hbar(df.groupby("Zone_Name", as_index=False).Accident_Count.sum(),
             "Zone_Name", "Accident_Count", "tr_acc")
    footer()


def page_environment():
    page_title("Environmental Health Dashboard")
    kpi_row([
        ("Average CO₂", hum(df.CO2_Level.mean()), "🌫️"),
        ("Average AQI", hum(df.AQI.mean()), "☁️"),
        ("Average PM2.5", hum(df.PM2_5.mean()), "🌡️"),
        ("Total Water Consumption", hum(df.Water_Consumption_KL.sum()), "💧"),
        ("Average City Health Score", hum(df.City_Health_Score.mean()), "❤️"),
    ])
    c1, c2, c3 = st.columns([1.8, 1.6, 1.3])
    with c1:
        ctitle("Average CO₂ and PM2.5 by Month")
        co2, pm = by_month(df, "CO2_Level", "mean"), by_month(df, "PM2_5", "mean")
        combo_chart(co2.Mon, ("Average CO₂", co2.CO2_Level),
                    ("Average PM2.5", pm.PM2_5.values[: len(co2)]), "en_co2")
    with c2:
        ctitle("Average AQI by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).AQI.mean(), "Zone_Name", "AQI", "en_aqi_zone")
    with c3:
        ctitle("Average AQI by Weather Category")
        vbar(df.groupby("Weather_Category", as_index=False).AQI.mean(),
             "Weather_Category", "AQI", "en_aqi_cat")
    c4, c5, c6 = st.columns([1.8, 1.8, 1.3])
    with c4:
        ctitle("Average AQI by Month")
        a = by_month(df, "AQI", "mean")
        line_chart(a.Mon, [("Avg AQI", a.AQI, BLUE)], "en_aqi_month", tick=".0f")
    with c5:
        ctitle("Total Water Consumption by Zone")
        vbar(df.groupby("Zone_Name", as_index=False).Water_Consumption_KL.sum().sort_values(
            "Water_Consumption_KL", ascending=False).head(10),
            "Zone_Name", "Water_Consumption_KL", "en_water", order="keep")
    with c6:
        ctitle("Weather Distribution")
        wd = df.groupby("Weather_Condition", as_index=False).size()
        fig = go.Figure(go.Pie(
            labels=wd.Weather_Condition, values=wd["size"], hole=0.55,
            marker=dict(colors=PALETTE), textinfo="percent", sort=True,
        ))
        base(fig, 300, legend=False)
        fig.update_layout(showlegend=True, legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=10)))
        show(fig, "en_weather")
    footer()


def page_utilities():
    page_title("Utilities &amp; Infrastructure Dashboard")
    elec, water = df.Electricity_Consumption_kWh.sum(), df.Water_Consumption_KL.sum()
    zones = max(df.Zone_Name.nunique(), 1)
    kpi_row([
        ("Total Electricity", hum(elec), "💡"),
        ("Total Water", hum(water), "💧"),
        ("Average Electricity per Zone", hum(elec / zones, big=2), "💡"),
    ])
    c1, c2 = st.columns(2)
    e, w = by_month(df, "Electricity_Consumption_kWh"), by_month(df, "Water_Consumption_KL")
    with c1:
        ctitle("Total Electricity by Month")
        line_chart(e.Mon, [("Total Electricity", e.Electricity_Consumption_kWh, BLUE)], "ut_elec")
    with c2:
        ctitle("Total Electricity and Water by Month")
        line_chart(e.Mon, [("Total Electricity", e.Electricity_Consumption_kWh, BLUE),
                           ("Total Water", w.Water_Consumption_KL.values[: len(e)], WHITE)], "ut_both")
    c3, c4 = st.columns([1, 1.15])
    with c3:
        ctitle("Total Water by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).Water_Consumption_KL.sum(),
             "Zone_Name", "Water_Consumption_KL", "ut_water", h=330)
    with c4:
        ctitle("Total Electricity by Zone")
        z = df.groupby("Zone_Name", as_index=False).Electricity_Consumption_kWh.sum()
        fig = px.treemap(z, path=["Zone_Name"], values="Electricity_Consumption_kWh",
                         color="Zone_Name", color_discrete_sequence=PALETTE)
        fig.update_traces(texttemplate="%{label}<br>%{value:.2s}", textposition="top left",
                          marker_line_color="#0E1628")
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=0, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        show(fig, "ut_tree")
    footer()


def page_safety():
    page_title("Public Safety Dashboard")
    kpi_row([
        ("Total Crime", hum(df.Crime_Count.sum()), "🕵️"),
        ("Total Emergency Calls", hum(df.Emergency_Calls.sum()), "📞"),
        ("Total Accidents", hum(df.Accident_Count.sum()), "💥"),
        ("Average Road Condition", hum(df.Road_Condition_Score.mean()), "🛣️"),
        ("Citizen Satisfaction", hum(df.Citizen_Satisfaction.mean()), "😊"),
    ])
    c1, c2, c3 = st.columns([1.9, 1.5, 1.7])
    with c1:
        ctitle("Total Emergency Calls by Month")
        em = by_month(df, "Emergency_Calls")
        line_chart(em.Mon, [("Emergency Calls", em.Emergency_Calls, BLUE)], "ps_em", tick=",.0f")
    with c2:
        ctitle("Total Crime by Time Period")
        vbar(df.groupby("Time_Period", as_index=False).Crime_Count.sum(),
             "Time_Period", "Crime_Count", "ps_time")
    with c3:
        ctitle("Average Road Condition by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).Road_Condition_Score.mean(),
             "Zone_Name", "Road_Condition_Score", "ps_road", small=2)
    c4, c5, c6 = st.columns([1.5, 1.9, 1.7])
    with c4:
        ctitle("Accident Hotspots")
        zone_map(df, "Accident_Count", "ps_map", 300)
    with c5:
        ctitle("Total Accidents by Weather Condition")
        vbar(df.groupby("Weather_Condition", as_index=False).Accident_Count.sum(),
             "Weather_Condition", "Accident_Count", "ps_weather")
    with c6:
        ctitle("Total Crime by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).Crime_Count.sum(),
             "Zone_Name", "Crime_Count", "ps_crime")
    footer()


def build_insights(d):
    out = []
    z = d.groupby("Zone_Name").City_Health_Score.mean().sort_values(ascending=False)
    out.append(f"{z.index[0]} has the highest City Health Score ({z.iloc[0]:.0f}), "
               "indicating strong overall urban performance.")
    if len(d) > 30:
        corr = d[["City_Health_Score", "Congestion_Index", "Crime_Count"]].corr()["City_Health_Score"]
        if corr["Congestion_Index"] < 0 and corr["Crime_Count"] < 0:
            out.append("Higher congestion and crime are associated with lower City Health Scores "
                       f"(correlation {corr['Congestion_Index']:.2f} and {corr['Crime_Count']:.2f}).")
    sev = d[d.Weather_Category == "Severe"]
    rest = d[d.Weather_Category != "Severe"]
    if len(sev) and len(rest) and sev.Accident_Count.mean() > rest.Accident_Count.mean() \
            and sev.Emergency_Calls.mean() > rest.Emergency_Calls.mean():
        out.append("Heavy rain and thunderstorms correspond with increased accidents and emergency calls.")
    zt = d.groupby("Zone_Type").Citizen_Satisfaction.mean()
    if {"Residential", "Industrial"} <= set(zt.index) and zt["Residential"] > zt["Industrial"]:
        out.append("Residential zones show higher citizen satisfaction than industrial areas.")
    return out


def page_ai():
    page_title("AI INSIGHTS")
    kpi_row([
        ("Average City Health Score", hum(df.City_Health_Score.mean()), "❤️"),
        ("Average Congestion", hum(df.Congestion_Index.mean()), "🚦"),
        ("Average AQI", hum(df.AQI.mean()), "☁️"),
        ("Citizen Satisfaction", hum(df.Citizen_Satisfaction.mean()), "😊"),
        ("Total Emergency Calls", hum(df.Emergency_Calls.sum()), "📞"),
    ])
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        ctitle("Key influencers")
        st.caption("What influences City Health Score? (correlation, −1 to +1)")
        drivers = ["Congestion_Index", "Vehicle_Count", "Average_Speed", "Parking_Occupancy", "AQI",
                   "PM2_5", "CO2_Level", "Noise_Level", "Accident_Count", "Crime_Count",
                   "Emergency_Calls", "Road_Condition_Score", "Citizen_Satisfaction"]
        corr = df[drivers + ["City_Health_Score"]].corr()["City_Health_Score"].drop("City_Health_Score").dropna()
        corr = corr.reindex(corr.abs().sort_values(ascending=False).index).head(8)
        fig = go.Figure(go.Bar(
            x=corr.values, y=[n.replace("_", " ") for n in corr.index], orientation="h",
            marker_color=[BLUE if v >= 0 else RED for v in corr.values],
            text=[f"{v:+.2f}" for v in corr.values], textposition="outside", cliponaxis=False,
        ))
        base(fig, 300)
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(range=[-1, 1], title=None)
        show(fig, "ai_infl")
    with c2, st.container(border=True):
        ctitle("Decomposition")
        options = {"Weather Condition": "Weather_Condition", "Zone Type": "Zone_Type",
                   "Time Period": "Time_Period", "Season": "Season",
                   "Event": "Event_Name", "Weekday": "Weekday"}
        choice = st.selectbox("Average City Health Score by", list(options), key="ai_decomp")
        hbar(df.groupby(options[choice], as_index=False).City_Health_Score.mean(),
             options[choice], "City_Health_Score", "ai_decomp_chart", n=10, small=1, h=250)

    c3, c4, c5 = st.columns([1.5, 1.4, 1.3])
    with c3:
        ctitle("City Performance Relationship")
        zs = df.groupby(["Zone_Name", "Zone_Type"], as_index=False).agg(
            Congestion=("Congestion_Index", "mean"),
            Satisfaction=("Citizen_Satisfaction", "mean"),
            Population=("Population", "first"))
        fig = px.scatter(zs, x="Congestion", y="Satisfaction", size="Population",
                         hover_name="Zone_Name", color_discrete_sequence=[BLUE], size_max=18)
        base(fig, 300)
        fig.update_xaxes(title="Average Congestion")
        fig.update_yaxes(title="Citizen Satisfaction")
        show(fig, "ai_scatter")
    with c4:
        ctitle("Key Business Insights")
        bullets = "".join(f"<div>• {t}</div>" for t in build_insights(df))
        st.markdown(f'<div class="insight">{bullets}</div>', unsafe_allow_html=True)
    with c5:
        ctitle("City Health Score by Zone")
        hbar(df.groupby("Zone_Name", as_index=False).City_Health_Score.mean(),
             "Zone_Name", "City_Health_Score", "ai_zone", n=8)
    footer()


{
    "Executive Overview": page_executive,
    "Traffic Analytics": page_traffic,
    "Environment": page_environment,
    "Utilities": page_utilities,
    "Public Safety": page_safety,
    "AI Insights": page_ai,
}[st.session_state.page]()
