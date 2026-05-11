import time
import serial
import threading

# =========================
# KONFIGURASI
# =========================
SERIAL_PORT = "COM7"
BAUD_RATE = 9600

class SerialController:
    def __init__(self, port: str = SERIAL_PORT, baud_rate: int = BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.is_sending = False
        self.connect()

    def connect(self):
        try:
            if self.ser is not None:
                try:
                    self.ser.close()
                except:
                    pass
            
            print(f"🔌 Connect ke {self.port}...")
            self.ser = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=1, 
                write_timeout=1 
            )
            time.sleep(2) # Tunggu Arduino reset selesai
            print("✅ Serial connected")
            
        except Exception as e:
            print(f"❌ Serial error: {e}")

    # =========================
    # TRIGGER SERVO
    # =========================
    def trigger_servo(self):
        if self.is_sending:
            return
            
        thread = threading.Thread(target=self._send_command_with_retry)
        thread.daemon = True
        thread.start()

    def _send_command_with_retry(self):
        self.is_sending = True
        
        # Percobaan pertama mengirim kode
        sukses = self._execute_write()
        
        # Jika gagal (karena USB putus efek servo), 
        # _execute_write sudah melakukan reconnect. 
        # Sekarang kita PAKSA kirim ulang perintahnya!
        if not sukses:
            print("🔄 Mencoba kirim ulang perintah setelah reset port...")
            self._execute_write()
            
        self.is_sending = False

    def _execute_write(self):
        """Fungsi inti untuk menulis ke serial. Return True jika berhasil."""
        try:
            if self.ser is None or not self.ser.is_open:
                self.connect()

            print("📤 Kirim perintah motor...")
            self.ser.write(b"F\n")
            self.ser.flush()
            print("✅ Perintah 'F' terkirim")
            return True
            
        except Exception as e:
            print(f"❌ Gagal kirim (jalur nyangkut): {e}")
            # Reset koneksi, ini butuh waktu sekitar 2 detik
            self.connect() 
            return False

    def close(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("🔌 Serial ditutup")
        except Exception:
            pass