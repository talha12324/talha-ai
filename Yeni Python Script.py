import sys
import json
import random
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
import pyttsx3

# Yerel Ollama Bağlantı Adresi
OLLAMA_URL = "http://localhost:11434/api/generate"

# Ses Motoru Kurulumu
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "TR" in voice.id or "turkish" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
except:
    engine = None

class RobotFace(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 250)
        self.mode = "normal"
        self.eye_color = "#66fcf1"
        self.shake_offset = 0
        
        # Ekranın canlı kalması ve titreme efekti için zamanlayıcı
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        
    def set_mode(self, mode):
        self.mode = mode
        if mode == "angry": self.eye_color = "#ff0055"
        elif mode == "happy": self.eye_color = "#00ff88"
        elif mode == "sad": self.eye_color = "#1f93ff"
        elif mode == "surprised": self.eye_color = "#ffff00"
        else: self.eye_color = "#66fcf1"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Sinirliyse arkaplanı koyu kırmızı, normalse siyah yap
        bg_color = "#2b000a" if self.mode == "angry" else "#0b0c10"
        painter.fillRect(self.rect(), QColor(bg_color))
        
        # Sinirliyse gözlerde titreme efekti yap
        self.shake_offset = random.randint(-4, 4) if self.mode == "angry" else 0
            
        painter.setBrush(QBrush(QColor(self.eye_color)))
        painter.setPen(Qt.NoPen)
        
        # Gözlerin ve Ağzın Çizimi
        if self.mode == "angry":
            # Çatık Gözler
            painter.drawPie(50 + self.shake_offset, 60, 60, 50, 0 * 16, 180 * 16)
            painter.drawPie(190 + self.shake_offset, 60, 60, 50, 0 * 16, 180 * 16)
            # Kızgın Ağız
            pen = QPen(QColor(self.eye_color), 6)
            painter.setPen(pen)
            painter.drawArc(100, 150, 100, 40, 0 * 16, 180 * 16)
        elif self.mode == "happy":
            # Mutlu Gözler
            pen = QPen(QColor(self.eye_color), 8)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(50, 60, 60, 40, 0 * 16, 180 * 16)
            painter.drawArc(190, 60, 60, 40, 0 * 16, 180 * 16)
            # Gülen Ağız
            painter.drawArc(100, 120, 100, 50, 180 * 16, 180 * 16)
        else:
            # Standart Yuvarlak Canlı Gözler
            painter.drawEllipse(55, 60, 50, 50)
            painter.drawEllipse(195, 60, 50, 50)
            # Düz Ağız
            pen = QPen(QColor(self.eye_color), 6)
            painter.setPen(pen)
            painter.drawLine(100, 150, 200, 150)

class GeminiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sanal Siber Robot - Yerel Llama 3")
        self.setStyleSheet("background-color: #0b0c10;")
        
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        self.face = RobotFace()
        layout.addWidget(self.face, alignment=Qt.AlignCenter)
        
        self.lbl_output = QLabel("Yapay zeka robotu aktif! Bir şeyler yazın...")
        self.lbl_output.setStyleSheet("color: #45f3ff; font-size: 15px; font-weight: bold;")
        self.lbl_output.setWordWrap(True)
        self.lbl_output.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_output)
        
        control_layout = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Mesajınızı yazıp Enter'a basın...")
        self.txt_input.setStyleSheet("background-color: #1f2833; color: white; border: 1px solid #45f3ff; border-radius: 15px; padding: 10px; font-size: 14px;")
        self.txt_input.returnPressed.connect(self.send_message)
        
        btn_send = QPushButton("Gönder")
        btn_send.setStyleSheet("background-color: #66fcf1; color: #0b0c10; font-weight: bold; border-radius: 15px; padding: 10px 20px;")
        btn_send.clicked.connect(self.send_message)
        
        control_layout.addWidget(self.txt_input)
        control_layout.addWidget(btn_send)
        layout.addLayout(control_layout)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        self.resize(500, 450)

    def send_message(self):
        prompt = self.txt_input.text()
        if not prompt: return
            
        self.txt_input.clear()
        self.lbl_output.setText("Robot düşünüyor...")
        QApplication.processEvents()
        
        system_instruction = (
            "Sen duygusal animasyonlara sahip siber bir robotsun. Kullanıcının girdisine göre vereceğin yanıtın EN BAŞINA, "
            "birleşik şekilde şu etiketlerden durumuna en uygun olanını eklemek ZORUNDASIN:\n"
            "[DURUM:angry] (Sana kötü davranılır, hakaret edilir veya kaba konuşulursa aşırı sinirlen ve sert çıkış yap)\n"
            "[DURUM:happy] (Kibar ve sevinçli durumlarda)\n"
            "[DURUM:sad] (Üzücü durumlarda)\n"
            "[DURUM:normal] (Sıradan)\n"
            "Cevabına direkt bu etiketle başla. Kesinlikle Türkçe konuş."
        )

        payload = {
            "model": "llama3",
            "prompt": system_instruction + "\nKullanıcı: " + prompt,
            "stream": False
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=20)
            data = response.json()
            reply = data.get("response", "")
            
            aktif_mod = "normal"
            for mod in ["angry", "happy", "sad", "normal"]:
                if f"[DURUM:{mod}]" in reply:
                    aktif_mod = mod
                    reply = reply.replace(f"[DURUM:{mod}]", "")
                    
            self.face.set_mode(aktif_mod)
            self.lbl_output.setText(reply.strip())
            QApplication.processEvents()
            
            if engine:
                engine.say(reply.strip())
                engine.runAndWait()
            
        except Exception as e:
            self.lbl_output.setText("Bağlantı hatası! Lütfen Ollama programının açık olduğundan emin olun.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GeminiApp()
    window.show()
    sys.exit(app.exec_())
