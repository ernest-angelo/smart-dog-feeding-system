import streamlit as st
import pandas as pd
import plotly.express as px

from app.firebase_config import db

# =========================
# STREAMLIT CONFIG
# =========================

st.set_page_config(
    page_title="Smart Dog Feeding Dashboard",
    page_icon="🐶",
    layout="wide",
)

# =========================
# HEADER
# =========================

st.title("🐶 Smart Dog Feeding Dashboard")

st.caption(
    "Realtime IoT monitoring dashboard using Firebase + Streamlit."
)

# =========================
# FETCH FIREBASE DATA
# =========================

docs = (
    db.collection("feeding_logs")
    .order_by("timestamp", direction="DESCENDING")
    .stream()
)

history = [doc.to_dict() for doc in docs]

# =========================
# EMPTY CHECK
# =========================

if not history:

    st.warning("Belum ada data feeding logs.")

    st.stop()

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(history)

# =========================
# CLEAN TIMESTAMP
# =========================

if "timestamp" in df.columns:

    df["timestamp"] = df["timestamp"].astype(str)

# =========================
# METRICS
# =========================

total_logs = len(df)

manual_count = len(
    df[df["mode"] == "manual"]
)

auto_count = len(
    df[df["mode"] == "auto"]
)

latest_mode = df.iloc[0]["mode"]

# =========================
# TOP METRICS
# =========================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "📜 Total Logs",
        total_logs
    )

with col2:

    st.metric(
        "🤖 Auto Feeding",
        auto_count
    )

with col3:

    st.metric(
        "👨 Manual Feeding",
        manual_count
    )

with col4:

    st.metric(
        "🕒 Latest Mode",
        latest_mode.upper()
    )

# =========================
# LATEST DETECTION
# =========================

st.subheader("🐶 Latest Detection")

latest = history[0]

st.json(latest)

# =========================
# HISTORY TABLE
# =========================

st.subheader("📜 Feeding History")

st.dataframe(
    df,
    use_container_width=True
)

# =========================
# PIE CHART
# =========================

st.subheader("📊 Feeding Statistics")

mode_counts = (
    df["mode"]
    .value_counts()
    .reset_index()
)

mode_counts.columns = [
    "mode",
    "count"
]

fig = px.pie(
    mode_counts,
    names="mode",
    values="count",
    title="Manual vs Auto Feeding"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================
# AUTO REFRESH
# =========================

st.caption(
    "🔄 Refresh page untuk update realtime terbaru dari Firebase."
)