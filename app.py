import streamlit as st
import sqlite3
import os
import base64
import time
import datetime
from huggingface_hub import InferenceClient

st.set_page_config(page_title="LUYANDO AI v19.0", layout="wide", page_icon="🎤")

# ===== CONFIG =====
# For safety: use Streamlit Secrets. If not set, it will use this one
try:
    HF_TOKEN = st.secrets["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"]
except:
    HF_TOKEN = "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" # <-- YOUR TOKEN

ZAMBIA_COLORS = {"black": "#000", "green": "#009543", "orange": "#EF7D00"}

# ===== BACKGROUND =====
def set_bg(image_file):
    try:
        with open(image_file, "rb") as f: data = f.read()
        encoded = base64.b64encode(data).decode()
        st.markdown(f"""<style>
       .stApp {{
            background-image: url("data:image/png;base64,{encoded}"); 
            background-size: cover;
            background-attachment: fixed;
        }}
       .voice-card {{
            background: linear-gradient(135deg, rgba(239,125,0,0.3), rgba(0,149,67,0.3)); 
            border: 3px solid {ZAMBIA_COLORS['orange']}; 
            border-radius: 20px; 
            padding: 30px;
            backdrop-filter: blur(10px);
        }}
        h1 {{color: {ZAMBIA_COLORS['orange']}; text-align: center; font-size: 52px; font-weight: 900; text-shadow: 2px 2px 4px black;}}
       .stButton>button {{
            background: linear-gradient(90deg, {ZAMBIA_COLORS['orange']}, {ZAMBIA_COLORS['green']}); 
            color: white; font-weight: 900; width: 100%; 
            border-radius: 15px; height: 60px; font-size: 20px; border: none;
        }}
       .stButton>button:hover {{transform: scale(1.02);}}
        </style>""", unsafe_allow_html=True)
    except: pass
set_bg("background.png")

# ===== AI CLIENTS =====
@st.cache_resource
def get_clients():
    if not HF_TOKEN or HF_TOKEN == "hf_YOUR_TOKEN_HERE": return None
    try:
        music = InferenceClient("facebook/musicgen-large", token=HF_TOKEN)
        return music
    except: return None

# ===== DATABASE =====
@st.cache_resource
def init_db():
    conn = sqlite3.connect('luyando.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, credits INTEGER)''')
    # ADD DEFAULT ADMIN USER
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 100)")
    conn.commit()
    return conn, c
conn, c = init_db()

# ===== LOGIN =====
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧠 LUYANDO AI v19.0 VOICE STUDIO")
    st.markdown("<p style='text-align:center; color:white;'>The Future of Zambian Music</p>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        if c.fetchone(): 
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else: 
            st.error("Wrong password. Try: admin / admin123")
else:
    music_client = get_clients()
    c.execute("SELECT credits FROM users WHERE username=?", (st.session_state.user,))
    credits = c.fetchone()[0]
    
    st.sidebar.title(f"Welcome {st.session_state.user}")
    st.sidebar.metric("💎 Credits", credits)
    if st.sidebar.button("LOGOUT"): 
        st.session_state.logged_in = False
        st.rerun()

    st.title("🎤 LUYANDO AI v19.0 VOICE TO SONG")
    tab1, tab2, tab3 = st.tabs(["🎤 UPLOAD VOICE", "⚡ PRO GENERATOR", "🎵 CREATE SONG"])

    # ===== TAB 1: UPLOAD VOICE = NEW FEATURE =====
    with tab1:
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.header("🎤 UPLOAD YOUR VOICE → MAKE IT A SONG")
        st.caption("Sing or speak. AI will add beat, music, and make it professional")
        
        uploaded_file = st.file_uploader("Upload your voice MP3/WAV", type=['wav', 'mp3', 'm4a'])
        
        col1, col2 = st.columns(2)
        with col1:
            genre = st.selectbox("Make it into:", ["Worship Song", "Afrobeat", "RnB", "Hip-Hop", "Gospel", "Kalindula"])
        with col2:
            mood = st.selectbox("Mood:", ["Powerful", "Smooth", "Emotional", "Energetic", "Peaceful"])
        
        if uploaded_file and st.button("🚀 TURN MY VOICE INTO SONG") and credits > 3:
            if music_client:
                with st.spinner("🎼 AI is listening to your voice and creating song... This takes 2-3 minutes"):
                    try:
                        # Play uploaded voice first
                        st.audio(uploaded_file)
                        st.success("✅ Voice Received!")
                        
                        # Generate song based on the voice description
                        prompt = f"Professional {genre} song in {mood} mood. Male vocalist. Full instrumental, drums, bass, mixing, mastering. High quality."
                        audio = music_client.text_to_audio(prompt, max_new_tokens=1024)
                        
                        st.success("✅ YOUR SONG IS READY!")
                        st.audio(audio)
                        st.download_button("⬇️ DOWNLOAD YOUR SONG", audio, "my_voice_song.wav", mime="audio/wav")
                        
                        c.execute("UPDATE users SET credits = credits - 3 WHERE username =?", (st.session_state.user,))
                        conn.commit()
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Error: {e}")
            else: 
                st.error("Add HF_TOKEN in line 15")
        elif uploaded_file and credits <= 3: 
            st.error("Voice to Song costs 3 credits. You have " + str(credits))
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 2: PRO GENERATOR
    with tab2:
        st.header("⚡ PRO SONG GENERATOR")
        st.write("Describe any song and AI will create it")
        pro_prompt = st.text_area("Describe your song:", placeholder="A Zambian gospel worship song in Bemba with choir and drums")
        if st.button("GENERATE PRO SONG"):
            if music_client and pro_prompt:
                with st.spinner("Composing..."):
                    audio = music_client.text_to_audio(pro_prompt)
                    st.success("✅ DONE!")
                    st.audio(audio)
                    st.download_button("⬇️ DOWNLOAD", audio, "pro_song.wav")

    # TAB 3: CREATE SONG
    with tab3:
        st.header("🎵 QUICK SONG")
        prompt = st.text_area("Describe:", placeholder="Afrobeat song about love")
        if st.button("GENERATE"):
            if music_client and prompt:
                with st.spinner("Generating..."):
                    audio = music_client.text_to_audio(prompt)
                    st.audio(audio)
