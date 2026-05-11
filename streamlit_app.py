import time
import cv2
import streamlit as st
import pandas as pd

from datetime import datetime

from detector import DogDetector
from serial_controller import SerialController
from app.firebase_config import db

# =========================
# KONFIGURASI
# =========================

COOLDOWN_SECONDS = 15

# =========================
# STREAMLIT CONFIG
# =========================

st.set_page_config(
    page_title="Smart Dog Feeding System",
    page_icon="🐶",
    layout="wide",
)

st.title("🐶 Smart Dog Feeding System")

st.caption(
    "AI-powered IoT system for automatic and manual dog feeding using YOLOv8."
)

# =========================
# STATUS PANEL
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("System", "ACTIVE")

with col2:
    st.metric("Mode", "AUTO")

with col3:
    st.metric("Cooldown", f"{COOLDOWN_SECONDS}s")

# =========================
# SESSION STATE
# =========================

if "last_trigger_time" not in st.session_state:

    st.session_state.last_trigger_time = (
        time.time() - COOLDOWN_SECONDS
    )

if "detector" not in st.session_state:

    st.session_state.detector = DogDetector()

if "serial" not in st.session_state:

    controller = SerialController()

    controller.connect()

    st.session_state.serial = controller

# =========================
# OBJECT
# =========================

detector: DogDetector = st.session_state.detector

serial: SerialController = st.session_state.serial

# =========================
# MANUAL FEED BUTTON
# =========================

if st.button("🍖 Manual Feed"):

    serial.trigger_servo()

    db.collection("feeding_logs").add({
        "timestamp": datetime.now(),
        "mode": "manual",
        "dog_detected": False
    })

    st.success("Manual feeding triggered!")

# =========================
# SIDEBAR PLACEHOLDER
# =========================

history_placeholder = st.sidebar.empty()

# =========================
# UI PLACEHOLDER
# =========================

status_placeholder = st.empty()

frame_placeholder = st.empty()

cooldown_placeholder = st.empty()

# =========================
# MAIN LOOP
# =========================

while True:

    # =========================
    # BACA FRAME
    # =========================

    success, frame = detector.read_frame()

    if not success:

        status_placeholder.error(
            "⚠️ Kamera tidak terbaca"
        )

        time.sleep(0.1)

        continue

    current_time = time.time()

    elapsed = (
        current_time
        - st.session_state.last_trigger_time
    )

    # =========================
    # HITUNG COOLDOWN
    # =========================

    remaining = max(
        0,
        COOLDOWN_SECONDS - int(elapsed)
    )

    # =========================
    # JIKA MASIH COOLDOWN
    # =========================

    if remaining > 0:

        status_placeholder.warning(
            f"⏳ Cooldown aktif ({remaining} detik)"
        )

        annotated_frame = frame

        cv2.putText(
            annotated_frame,
            f"Cooldown: {remaining}s",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2,
        )

    else:

        # =========================
        # DETEKSI YOLO
        # =========================

        annotated_frame, dog_detected = (
            detector.detect(frame)
        )

        # =========================
        # JIKA ADA ANJING
        # =========================

        if dog_detected:

            status_placeholder.success(
                "🐶 Dog detected!"
            )

            # Trigger servo
            serial.trigger_servo()

            # SAVE TO FIREBASE
            db.collection("feeding_logs").add({
                "timestamp": datetime.now(),
                "mode": "auto",
                "dog_detected": True
            })

            # RESET COOLDOWN
            st.session_state.last_trigger_time = (
                time.time()
            )

        else:

            status_placeholder.info(
                "📷 Waiting for dog..."
            )

    # =========================
    # DISPLAY FRAME
    # =========================

    rgb_frame = cv2.cvtColor(
        annotated_frame,
        cv2.COLOR_BGR2RGB
    )

    frame_placeholder.image(
        rgb_frame,
        channels="RGB",
        use_container_width=True
    )

    # =========================
    # REFRESH HISTORY
    # =========================

    docs = (
        db.collection("feeding_logs")
        .order_by("timestamp", direction="DESCENDING")
        .limit(10)
        .stream()
    )

    history = [doc.to_dict() for doc in docs]

    with history_placeholder.container():

        st.subheader("📜 Latest Feeding Logs")

        if history:

            df = pd.DataFrame(history)

            st.dataframe(
                df,
                use_container_width=True
            )

        else:

            st.info("No feeding history yet.")

    # =========================
    # STABILIZER
    # =========================

    time.sleep(0.03)
