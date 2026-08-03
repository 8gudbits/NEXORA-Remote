import tkinter as tk
import threading
import random
import json
import qrcode
import io
import paho.mqtt.client as mqtt
import keyboard as kb

from tkinter import messagebox
from PIL import Image, ImageTk

# ---------- CONFIGURATION ----------
BASE_URL = "http://192.168.255.102:5500/remote.html?code="
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# Debug flag: set to True to simulate missing admin rights
SIMULATE_NO_ADMIN = False
# -----------------------------------


class NEXORA_App:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXORA Remote")
        self.root.configure(bg="#19191f")
        self.root.resizable(False, False)
        self.root.geometry("300x460")

        # Color scheme
        self.bg = "#19191f"
        self.fg = "#e0d5c2"
        self.accent = "#d4a860"
        self.btn_bg = "#262630"
        self.btn_active = "#1e1e26"
        self.btn_fg = "#8a8a90"

        self.base_url = BASE_URL
        self.room_code = self.generate_code()
        self.client = None
        self.mqtt_thread = None
        self.keyboard_available = False
        self.keyboard_warning_shown = False

        self.build_ui()
        self.update_qr()
        self.start_mqtt()

        # Test keyboard access after UI is fully drawn
        self.root.after(500, self.test_keyboard_access)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def generate_code(self):
        return str(random.randint(0, 999999)).zfill(6)

    def build_ui(self):
        frame = tk.Frame(self.root, bg=self.bg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = tk.Label(
            frame,
            text="NEXORA Remote",
            font=("Inter", 14, "bold"),
            bg=self.bg,
            fg=self.accent,
        )
        title.pack(pady=(0, 10))

        self.code_var = tk.StringVar(value=self.room_code)
        code_label = tk.Label(
            frame,
            textvariable=self.code_var,
            font=("Inter", 24, "bold"),
            bg=self.bg,
            fg=self.fg,
        )
        code_label.pack(pady=(0, 5))

        subtitle = tk.Label(
            frame, text="ROOM CODE", font=("Inter", 8, "bold"), bg=self.bg, fg="#5a5a5e"
        )
        subtitle.pack(pady=(0, 10))

        self.qr_label = tk.Label(frame, bg=self.bg)
        self.qr_label.pack(pady=(0, 10))

        btn_frame = tk.Frame(frame, bg=self.bg)
        btn_frame.pack()

        copy_btn = tk.Button(
            btn_frame,
            text="Copy Code",
            command=self.copy_code,
            font=("Inter", 9, "bold"),
            bg=self.btn_bg,
            fg=self.btn_fg,
            activebackground=self.btn_active,
            activeforeground=self.fg,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        copy_btn.pack(side="left", padx=5)

        new_btn = tk.Button(
            btn_frame,
            text="New Code",
            command=self.new_code,
            font=("Inter", 9, "bold"),
            bg=self.btn_bg,
            fg=self.btn_fg,
            activebackground=self.btn_active,
            activeforeground=self.fg,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        new_btn.pack(side="left", padx=5)

        self.status_var = tk.StringVar(value="Initialising…")
        status_label = tk.Label(
            frame,
            textvariable=self.status_var,
            font=("Inter", 8),
            bg=self.bg,
            fg="#6b6b78",
        )
        status_label.pack(pady=(12, 0))

    def update_qr(self):
        url = f"{self.base_url}{self.room_code}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#e0d5c2", back_color=self.bg)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        self.qr_img = ImageTk.PhotoImage(Image.open(img_bytes))
        self.qr_label.config(image=self.qr_img)

    def copy_code(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.room_code)
        self.code_var.set("Copied!")
        self.root.after(1500, lambda: self.code_var.set(self.room_code))

    def new_code(self):
        self.room_code = self.generate_code()
        self.code_var.set(self.room_code)
        self.update_qr()
        self.restart_mqtt()

    def test_keyboard_access(self):
        """Simulate a harmless key to check permissions. If SIMULATE_NO_ADMIN is True, force failure."""
        if SIMULATE_NO_ADMIN:
            self.keyboard_available = False
            self.status_var.set("Admin rights required")
            if not self.keyboard_warning_shown:
                self.keyboard_warning_shown = True
                messagebox.showwarning(
                    "Administrator Rights Required",
                    "This program cannot simulate keyboard keys without administrator privileges.\n\n"
                    "Please close and re-run the program as an administrator to control slides.\n\n"
                    "Right-click the file → 'Run as administrator'.",
                )
                self.root.after(0, self.root.destroy)
            return

        try:
            kb.press_and_release("f24")
            self.keyboard_available = True
            self.status_var.set("Connected – ready")
        except PermissionError:
            self.keyboard_available = False
            self.status_var.set("Admin rights required")
            if not self.keyboard_warning_shown:
                self.keyboard_warning_shown = True
                messagebox.showwarning(
                    "Administrator Rights Required",
                    "This program cannot simulate keyboard keys without administrator privileges.\n\n"
                    "Please close and re-run the program as an administrator to control slides.\n\n"
                    "Right-click the file → 'Run as administrator'.",
                )
                self.root.after(0, self.root.destroy)
        except Exception as e:
            self.keyboard_available = False
            self.status_var.set(f"Keyboard error: {e}")

    def start_mqtt(self):
        self.mqtt_thread = threading.Thread(target=self._mqtt_loop, daemon=True)
        self.mqtt_thread.start()

    def restart_mqtt(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.start_mqtt()

    def _mqtt_loop(self):
        topic = f"nexora/room/{self.room_code}/keys"

        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                client.subscribe(topic)
                self.root.after(0, self.status_var.set, "Connected")
            else:
                self.root.after(0, self.status_var.set, "Connection error")

        def on_message(client, userdata, msg):
            if not self.keyboard_available:
                return
            try:
                payload = json.loads(msg.payload.decode())
                key = payload.get("key", "").lower()
                # Handle all four direction keys
                if key in ("left", "right", "up", "down"):
                    try:
                        kb.press_and_release(key)
                    except PermissionError:
                        self.keyboard_available = False
                        self.root.after(0, self.status_var.set, "Admin rights required")
                        if not self.keyboard_warning_shown:
                            self.keyboard_warning_shown = True
                            self.root.after(
                                0,
                                lambda: messagebox.showwarning(
                                    "Administrator Rights Required",
                                    "Keyboard control lost. Please re‑run as administrator.",
                                ),
                            )
                    except Exception as ke:
                        self.root.after(0, self.status_var.set, f"Key error: {ke}")
            except Exception as e:
                print(f"MQTT msg error: {e}")

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except Exception as e:
            self.root.after(0, self.status_var.set, f"MQTT error: {e}")

    def on_close(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = NEXORA_App(root)
    root.mainloop()

