import cv2
import threading
from deepface import DeepFace
import customtkinter as ctk
from PIL import Image, ImageTk
import vlc
import time
import os
import random
import tkinter as tk

# --- App Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("Offline Emotion Music Player")
app.geometry("1100x800")

# --- Global Variables ---
emotion_var = ctk.StringVar(value="Detecting Emotion...")
song_var = ctk.StringVar(value="Initializing Music...")
last_emotion = ""
player = None
instance = None
running = True
cap = None

# --- GUI Frames ---
bg_frame = ctk.CTkFrame(app, fg_color="#0d0f1e", corner_radius=0)
bg_frame.place(relwidth=1, relheight=1)

main_frame = ctk.CTkFrame(app, width=1000, height=700)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

video_frame = ctk.CTkFrame(main_frame, fg_color="#141c2f", corner_radius=20)
video_frame.pack(pady=20)

video_label = ctk.CTkLabel(video_frame, text="")
video_label.pack()

emotion_label = ctk.CTkLabel(main_frame, textvariable=emotion_var, 
                              font=ctk.CTkFont("Arial", 32, "bold"), text_color="#00ffff")
emotion_label.pack(pady=(20, 5))

song_title_label = ctk.CTkLabel(main_frame, textvariable=song_var,
                                font=ctk.CTkFont("Arial", 20, "bold"), text_color="#ff00ff")
song_title_label.pack(pady=(0, 15))

# --- Music Visualizer ---
visualizer_frame = ctk.CTkFrame(main_frame, fg_color="#0f0f1f", corner_radius=20, border_color="#8e44ad", border_width=2)
visualizer_frame.pack(pady=10)

visualizer_canvas = tk.Canvas(visualizer_frame, width=700, height=120, bg="#0f0f1f", highlightthickness=0)
visualizer_canvas.pack(pady=10)

bars = []
bar_width = 12
gap = 4
num_bars = 45

for i in range(num_bars):
    x = i * (bar_width + gap)
    bar = visualizer_canvas.create_rectangle(x, 120, x + bar_width, 120, fill="#00ffff", outline="")
    bars.append(bar)

# --- Functions ---
def animate_visualizer():
    if not running:
        return
    for bar in bars:
        height = random.randint(25, 110)
        x0, y0, x1, y1 = visualizer_canvas.coords(bar)
        visualizer_canvas.coords(bar, x0, 120 - height, x1, 120)
    visualizer_canvas.after(80, animate_visualizer)

def pulse_emotion():
    colors = ["#00ffff", "#ff00ff", "#8e44ad", "#00ffd5"]
    idx = 0
    def cycle():
        nonlocal idx
        emotion_label.configure(text_color=colors[idx % len(colors)])
        idx += 1
        if running:
            emotion_label.after(400, cycle)
    cycle()

def get_local_song(emotion):
    folder = f"songs/{emotion}"
    if not os.path.exists(folder):
        return None
    files = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.m4a'))]
    if not files:
        return None
    return os.path.join(folder, random.choice(files))

def play_local_song(path):
    global player, instance
    if not path:
        return
    if player:
        player.stop()
    if not instance:
        instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(path)
    player.set_media(media)
    player.play()

def start_camera():
    global last_emotion, cap, running
    cap = cv2.VideoCapture(0)

    def detect_emotion():
        global last_emotion
        while running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2)
                continue
            try:
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                emotion = str(result[0]['dominant_emotion']).capitalize()
                emotion_var.set(f"Emotion: {emotion}")

                if emotion != last_emotion:
                    last_emotion = emotion
                    song_path = get_local_song(emotion)
                    if song_path:
                        song_var.set(f"Now Playing: {os.path.basename(song_path)}")
                        threading.Thread(target=play_local_song, args=(song_path,), daemon=True).start()
            except:
                emotion_var.set("Emotion: Unknown")

            # Show webcam frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
            time.sleep(2)

    threading.Thread(target=detect_emotion, daemon=True).start()

def on_closing():
    global running, player, cap
    running = False
    if player:
        player.stop()
    if cap:
        cap.release()
    app.destroy()

# --- Start App ---
start_camera()
pulse_emotion()
animate_visualizer()
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
