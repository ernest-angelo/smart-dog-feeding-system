import streamlit as st
import pandas as pd
import plotly.express as px

from streamlit_webrtc import webrtc_streamer

from app.firebase_config import db

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Smart Dog Feeding Dashboard",
    page_icon="🐶",
    layout="wide"
)

# =========================
# HEADER
# =========================

st.title("🐶 Smart Dog Feeding System")

st.caption(
    "Realtime IoT monitoring dashboard using Firebase + Webcam Browser."
)

# =========================
# WEBCAM SECTION
# =========================

st.subheader("📷 Live Camera")

st.info(
    "Izinkan akses camera browser untuk menampilkan webcam laptop."
)

webrtc_streamer(
    key="dog-camera"
)

# =========================
# FIREBASE DATA
# =========================

st.subheader("📡 Realtime Firebase Logs")

docs = (
    db.collection("feeding_logs")
    .stream()
)

history = [
    doc.to_dict()
    for doc in docs
]

# =========================
# EMPTY CHECK
# =========================

if not history:

    st.warning(
        "Belum ada feeding logs."
    )

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

latest_mode = df.iloc[-1]["mode"]

# =========================
# METRIC UI
# =========================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "📜 Total Logs",
        total_logs
    )

with col2:

    st.metric(
        "🤖 Auto Feed",
        auto_count
    )

with col3:

    st.metric(
        "👨 Manual Feed",
        manual_count
    )

with col4:

    st.metric(
        "🕒 Latest Mode",
        latest_mode.upper()
    )

# =========================
# LATEST LOG
# =========================

st.subheader("🐶 Latest Detection")

latest = history[-1]

st.json(latest)

# =========================
# TABLE
# =========================

st.subheader("📋 Feeding History")

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
# FOOTER
# =========================

st.caption(
    "🚀 Smart Dog Feeding System • Firebase + Streamlit + Browser Camera"
)