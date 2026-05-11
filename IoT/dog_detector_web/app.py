import cv2
import time
import serial
import threading

from flask import Flask, Response, render_template_string
from ultralytics import YOLO

# =========================
# KONFIGURASI
# =========================

SERIAL_PORT = "COM7"
BAUD_RATE = 9600

CAMERA_INDEX = 0

# Cooldown 10 jam
COOLDOWN_SECONDS = 36000

CONFIDENCE_THRESHOLD = 0.5

MODEL_PATH = "yolov8n.pt"

DOG_CLASS_ID = 16

# =========================
# FLASK APP
# =========================

app = Flask(__name__)

# =========================
# GLOBAL VARIABLE
# =========================

ser = None

last_trigger_time = 0

is_sending = False

# =========================
# LOAD YOLO
# =========================

print("📦 Memuat model YOLO...")

model = YOLO(MODEL_PATH)

# =========================
# CAMERA SETUP
# =========================

print("📷 Membuka kamera...")

camera = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    640
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    480
)

camera.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)

if not camera.isOpened():

    raise Exception(
        "❌ Kamera gagal dibuka"
    )

print("✅ Kamera berhasil dibuka")

# =========================
# SERIAL FUNCTIONS
# =========================

def connect_serial():

    global ser

    try:

        if ser is not None and ser.is_open:
            return ser

        print(
            f"🔌 Menghubungkan ke {SERIAL_PORT}..."
        )

        ser = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1
        )

        # Tunggu Arduino reset
        time.sleep(2)

        print(
            f"✅ Serial connect ke {SERIAL_PORT}"
        )

        return ser

    except Exception as e:

        print(
            f"❌ Gagal serial: {e}"
        )

        return None

# =========================
# BACKGROUND SEND
# =========================

def background_serial_send():

    global is_sending

    is_sending = True

    try:

        current_ser = connect_serial()

        if (
            current_ser
            and current_ser.is_open
        ):

            print(
                "📤 Mengirim F..."
            )

            current_ser.write(b"F\n")

            current_ser.flush()

            print(
                "✅ F terkirim"
            )

            time.sleep(0.5)

    except Exception as e:

        print(
            f"❌ Error serial: {e}"
        )

    finally:

        is_sending = False

# =========================
# TRIGGER SERVO
# =========================

def trigger_servo():

    global is_sending

    if is_sending:
        return

    thread = threading.Thread(
        target=background_serial_send
    )

    thread.daemon = True

    thread.start()

# =========================
# VIDEO GENERATOR
# =========================

def generate_frames():

    global last_trigger_time

    while True:

        # =========================
        # READ FRAME
        # =========================

        success, frame = camera.read()

        if not success:

            print(
                "⚠️ Gagal membaca frame"
            )

            time.sleep(0.1)

            continue

        current_time = time.time()

        elapsed = (
            current_time
            - last_trigger_time
        )

        dog_detected = False

        # =========================
        # MODE COOLDOWN
        # =========================

        if elapsed < COOLDOWN_SECONDS:

            remaining = int(
                COOLDOWN_SECONDS - elapsed
            )

            hours = remaining // 3600

            minutes = (
                remaining % 3600
            ) // 60

            seconds = remaining % 60

            cooldown_text = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

            cv2.putText(
                frame,
                f"COOLDOWN {cooldown_text}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

        else:

            # =========================
            # YOLO DETECTION
            # =========================

            results = model(
                frame,
                verbose=False
            )

            for result in results:

                for box in result.boxes:

                    cls_id = int(
                        box.cls[0]
                    )

                    conf = float(
                        box.conf[0]
                    )

                    if (
                        cls_id == DOG_CLASS_ID
                        and conf >= CONFIDENCE_THRESHOLD
                    ):

                        dog_detected = True

                        x1, y1, x2, y2 = map(
                            int,
                            box.xyxy[0]
                        )

                        # Bounding Box
                        cv2.rectangle(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            (0, 255, 0),
                            2,
                        )

                        # Label
                        cv2.putText(
                            frame,
                            f"Dog {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2,
                        )

            # =========================
            # JIKA DOG TERDETEKSI
            # =========================

            if dog_detected:

                print(
                    "🐶 Anjing terdeteksi!"
                )

                trigger_servo()

                last_trigger_time = (
                    time.time()
                )

        # =========================
        # FPS TEXT
        # =========================

        cv2.putText(
            frame,
            "Dog Detector Running",
            (20, 440),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # =========================
        # ENCODE FRAME
        # =========================

        ret, buffer = cv2.imencode(
            ".jpg",
            frame
        )

        frame_bytes = (
            buffer.tobytes()
        )

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )

        # Delay kecil agar stabil
        time.sleep(0.03)

# =========================
# ROUTES
# =========================

@app.route("/")

def index():

    return render_template_string("""

    <html>

    <head>

        <title>Dog Detector</title>

    </head>

    <body
        style="
            background:#111;
            color:white;
            text-align:center;
            font-family:Arial;
        "
    >

        <h1>🐶 Dog Detector</h1>

        <img
            src="/video_feed"
            style="
                width:80%;
                border:5px solid #333;
                border-radius:10px;
            "
        >

        <p>
            Sistem deteksi anjing aktif
        </p>

    </body>

    </html>

    """)

# =========================
# VIDEO FEED
# =========================

@app.route("/video_feed")

def video_feed():

    return Response(
        generate_frames(),
        mimetype=(
            "multipart/x-mixed-replace;"
            " boundary=frame"
        )
    )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    connect_serial()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )