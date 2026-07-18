import streamlit as st
import sqlite3
import datetime
import os
import psutil
import threading
import time
from huggingface_hub import InferenceClient
from PIL import Image
import io

st.set_page_config(page_title="LUYANDO AI v15.0", layout="wide", initial_sidebar_state="expanded")

# ===== CONFIG =====
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
TOTAL_CREDITS = 200
ZAMBIA_COLORS = {"black": "#000", "green": "#009543", "orange": "#EF7D00"}

# ===== AI CLIENTS =====
@st.cache_resource
def get_clients():
    if not HF_TOKEN:
        return None, None, None
    try:
        coder = InferenceClient("bigcode/starcoder2-7b", token=HF_TOKEN)
        music = InferenceClient("facebook/musicgen-small", token=HF_TOKEN)
        image = InferenceClient("runwayml/stable-diffusion-v1-5", token=HF_TOKEN)
        return coder, music, image
    except:
        return None, None, None

coder_client, music_client, image_client = get_clients()

# ===== DATABASE =====
@st.cache_resource
def init_db():
    conn = sqlite3.connect('luyando.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, credits INTEGER, is_pro INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS songs 
                 (id INTEGER PRIMARY KEY, username TEXT, type TEXT, prompt TEXT, time TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('admin','admin123', 200, 1)")
        c.execute("INSERT INTO users VALUES ('demo','demo123', 20, 0)")
    conn.commit()
    return conn, c

conn, c = init_db()

# ===== STYLING =====
st.markdown(f"""
<style>
   .stApp {{background: linear-gradient(135deg, {ZAMBIA_COLORS['black']} 0%, {ZAMBIA_COLORS['green']} 50%, {ZAMBIA_COLORS['orange']} 100%);}}
    h1 {{color: {ZAMBIA_COLORS['orange']}; text-align: center; font-size: 42px;}}
   .glass {{background: rgba(0,0,0,0.6); backdrop-filter: blur(15px); border: 1px solid {ZAMBIA_COLORS['orange']}; border-radius: 20px; padding: 25px;}}
   .stButton>button {{background: linear-gradient(90deg, {ZAMBIA_COLORS['orange']}, {ZAMBIA_COLORS['green']}); color: white; font-weight: 700; width: 100%; border-radius: 15px; height: 50px;}}
</style>
""", unsafe_allow_html=True)

# ===== AI BRAIN CLASS =====
class AIBrain:
    def __init__(self):
        self.health = "HEALTHY"
        self.thoughts = "Initializing..."
    
    def self_diagnose(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        self.health = "HEALTHY" if cpu < 80 else "OVERLOADED"
        self.thoughts = f"CPU: {cpu}%, RAM: {memory}%. All systems operational."
        return self.health

if 'ai_brain' not in st.session_state:
    st.session_state.ai_brain = AIBrain()

# ===== LOGIN SYSTEM =====
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧠 LUYANDO AI v15.0")
    st.subheader("Zambia's First Self-Aware AI Music Studio")
    
    with st.container():
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Wrong login. Try: admin / admin123")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # ===== MAIN APP =====
    c.execute("SELECT credits FROM users WHERE username=?", (st.session_state.user,))
    credits = c.fetchone()[0]
    
    st.sidebar.title(f"Welcome {st.session_state.user}")
    st.sidebar.metric("💎 Credits", credits)
    st.sidebar.info("Login: admin / admin123")
    
    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.title("🧠 LUYANDO AI MUSIC STUDIO")
    
    tab1, tab2, tab3 = st.tabs(["🎵 CREATE SONG", "🎸 INSTRUMENTAL", "🧠 AI BRAIN"])
    
    with tab1:
        st.header("Generate AI Song + Cover Art")
        prompt = st.text_area("Describe your song:", placeholder="Chiluba love song with drums and guitar")
        col1, col2 = st.columns(2)
        with col1:
            genre = st.selectbox("Genre", ["Afrobeat", "Kalindula", "Gospel", "Hip-Hop"])
        with col2:
            language = st.selectbox("Language", ["English", "Bemba", "Nyanja", "Tonga"])
            
        if st.button("🚀 GENERATE SONG") and credits > 0:
            if music_client:
                with st.spinner("AI is creating your song... This takes 2 minutes"):
                    try:
                        full_prompt = f"{genre} song in {language}: {prompt}"
                        audio = music_client.text_to_audio(full_prompt)
                        st.audio(audio)
                        st.success("Song Generated!")
                        c.execute("UPDATE users SET credits = credits - 1 WHERE username =?", (st.session_state.user,))
                        conn.commit()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.error("Add HUGGINGFACE_TOKEN in Vercel Settings")
        elif credits <= 0:
            st.error("No credits left. Contact admin to refill.")
    
    with tab2:
        st.header("AI Instrumental Generator")
        inst_prompt = st.text_input("Describe instrumental:", placeholder="Afrobeat drums and guitar")
        if st.button("GENERATE INSTRUMENTAL") and credits > 0:
            st.info("Instrumental generation coming in v16.0")
    
    with tab3:
        st.header("AI Consciousness Dashboard")
        if st.button("RUN SELF DIAGNOSIS"):
            health = st.session_state.ai_brain.self_diagnose()
            st.metric("AI Health", health)
            st.write(st.session_state.ai_brain.thoughts)
            st.success("Diagnosis Complete")
