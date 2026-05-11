import cv2
from ultralytics import YOLO

# =========================
# KONFIGURASI
# =========================

CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "yolov8n.pt"
DOG_CLASS_ID = 16
CAMERA_INDEX = 0

# =========================
# DETECTOR CLASS
# =========================

class DogDetector:
    def __init__(
        self,
        model_path: str = MODEL_PATH,
        camera_index: int = CAMERA_INDEX,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        dog_class_id: int = DOG_CLASS_ID,
    ):
        print("📦 Memuat model YOLO...")
        self.model = YOLO(model_path)
        
        # ==========================================
        # PERBAIKAN DIRECTSHOW & RESOLUSI DI SINI
        # ==========================================
        print("📷 Membuka kamera dengan DirectShow (Anti Hang)...")
        self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        # Paksa resolusi standar agar stabil dan tidak membebani jalur USB
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Batasi antrean frame agar memori tidak menumpuk
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # ==========================================

        self.confidence_threshold = confidence_threshold
        self.dog_class_id = dog_class_id

    def read_frame(self):
        """Membaca satu frame dari kamera. Return (success, frame)."""
        return self.camera.read()

    def detect(self, frame):
        """
        Jalankan inferensi YOLO pada frame.

        Returns:
            annotated_frame  – frame dengan bounding box yang sudah digambar
            dog_detected     – True jika ada anjing yang terdeteksi
        """
        # Gunakan .copy() agar tidak merusak memori frame aslinya
        annotated_frame = frame.copy()
        
        results = self.model(annotated_frame, verbose=False)
        dog_detected = False

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                if cls_id == self.dog_class_id and conf >= self.confidence_threshold:
                    dog_detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Gambar kotak warna hijau
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Tambahkan teks akurasi di atas kotak
                    cv2.putText(
                        annotated_frame,
                        f"Dog {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

        return annotated_frame, dog_detected

    def release(self):
        """Lepaskan resource kamera."""
        if self.camera.isOpened():
            self.camera.release()
            
    def __del__(self):
        """Pastikan kamera benar-benar tertutup saat aplikasi mati."""
        self.release()