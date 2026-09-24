import streamlit as st
import requests
import re
import time
import hashlib
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== إعدادات ==========
REQUEST_TIMEOUT = 8
MAX_PAGES = 100
DATA_FILE = "iptv_data.json"
PASSWORD = "BEAST_V17_PRO"
MAX_WORKERS = 20  # عدد الثريدات للتوازي

# ========== دوال حفظ وتحميل البيانات ==========
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ========== جلسة requests محسّنة ==========
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Connection": "keep-alive",
    })
    return s

# ========== دوال مساعدة ==========
def normalize_url(url):
    """تطبيع الرابط"""
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")

def extract_host_port(url):
    """استخراج الهوست والبورت"""
    try:
        url = normalize_url(url)
        m = re.match(r'https?://([^/:]+)(?::(\d+))?', url)
        if m:
            return m.group(1), m.group(2) or "80"
    except Exception:
        pass
    return None, None

def hash_url(url):
    """توليد هاش للرابط"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

# ========== فحص سيرفر IPTV ==========
def check_server(url, username=None, password=None, timeout=REQUEST_TIMEOUT):
    """فحص شامل لسيرفر IPTV"""
    result = {
        "url": url,
        "status": "unknown",
        "http_code": None,
        "server_info": None,
        "exp_date": None,
        "max_connections": None,
        "active_connections": None,
        "timezone": None,
        "channels": 0,
        "movies": 0,
        "series": 0,
        "response_time": None,
        "error": None,
    }

    session = get_session()
    start = time.time()

    try:
        # فحص player_api.php
        if username and password:
            api_url = f"{url}/player_api.php?username={username}&password={password}"
        else:
            api_url = f"{url}/player_api.php"

        r = session.get(api_url, timeout=timeout, verify=False)
        result["http_code"] = r.status_code
        result["response_time"] = round(time.time() - start, 2)

        if r.status_code == 200:
            try:
                data = r.json()
                result["server_info"] = data.get("server_info", {})
                user_info = data.get("user_info", {})

                if user_info:
                    result["exp_date"] = user_info.get("exp_date")
                    result["max_connections"] = user_info.get("max_connections")
                    result["active_connections"] = user_info.get("active_cons")
                    result["status"] = user_info.get("status", "Active")
                    result["timezone"] = result["server_info"].get("timezone")

                    # تحويل تاريخ الانتهاء
                    if result["exp_date"]:
                        try:
                            exp_ts = int(result["exp_date"])
                            result["exp_date_readable"] = datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            result["exp_date_readable"] = str(result["exp_date"])

                # جلب القنوات والأفلام والمسلسلات
                try:
                    ch = session.get(f"{url}/player_api.php?username={username}&password={password}&action=get_live_categories",
                                     timeout=timeout, verify=False)
                    if ch.status_code == 200:
                        result["channels"] = len(ch.json())
                except Exception:
                    pass

                try:
                    mv = session.get(f"{url}/player_api.php?username={username}&password={password}&action=get_vod_categories",
                                     timeout=timeout, verify=False)
                    if mv.status_code == 200:
                        result["movies"] = len(mv.json())
                except Exception:
                    pass

                try:
                    sr = session.get(f"{url}/player_api.php?username={username}&password={password}&action=get_series_categories",
                                     timeout=timeout, verify=False)
                    if sr.status_code == 200:
                        result["series"] = len(sr.json())
                except Exception:
                    pass

                result["status"] = "✅ يعمل" if result["status"] == "Active" else f"⚠️ {result['status']}"
            except ValueError:
                # ليس JSON - ممكن يكون m3u
                if "#EXTM3U" in r.text[:500]:
                    result["status"] = "✅ M3U Playlist"
                    result["channels"] = r.text.count("#EXTINF")
                else:
                    result["status"] = "❌ غير صالح"
        else:
            result["status"] = f"❌ HTTP {r.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "⏱️ Timeout"
        result["error"] = "انتهت المهلة"
    except requests.exceptions.ConnectionError:
        result["status"] = "🔌 فشل الاتصال"
        result["error"] = "تعذر الاتصال"
    except Exception as e:
        result["status"] = "❌ خطأ"
        result["error"] = str(e)[:100]

    return result

# ========== فحص متوازي ==========
def check_servers_parallel(servers, username=None, password=None, progress_cb=None):
    """فحص عدة سيرفرات بشكل متوازي"""
    results = []
    total = len(servers)
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_server, url, username, password): url
            for url in servers
        }
        for fut in as_completed(futures):
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                results.append({
                    "url": futures[fut],
                    "status": "❌ خطأ",
                    "error": str(e)[:100]
                })
            done += 1
            if progress_cb:
                progress_cb(done, total)

    return results

# ========== استخراج السيرفرات من نص ==========
def extract_servers_from_text(text):
    """استخراج جميع السيرفرات من نص"""
    servers = set()

    # نمط http/https
    for m in re.finditer(r'https?://[^\s<>"\']+', text):
        url = normalize_url(m.group(0))
        if url:
            servers.add(url)

    # نمط host:port
    for m in re.finditer(r'\b(\d{1,3}(?:\.\d{1,3}){3}:\d{2,5})\b', text):
        servers.add(normalize_url(m.group(1)))

    return sorted(servers)

# ========== شاشة الدخول ==========
def login_screen():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")

    # CSS محسّن
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #ff4b2b, #ff416c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.2em;
        }
        .sub-header {
            text-align: center;
            color: #888;
            margin-bottom: 2em;
        }
        .stButton > button {
            background: linear-gradient(90deg, #ff4b2b, #ff416c);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            transition: 0.3s;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 15px rgba(255,75,43,0.4);
        }
        .server-card {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            margin: 8px 0;
            border-left: 4px solid #ff4b2b;
        }
        .success { color: #00ff88; font-weight: bold; }
        .error { color: #ff4b2b; font-weight: bold; }
        .warning { color: #ffaa00; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced IPTV Checker & Scanner</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("🔐 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        if st.button("🚀 دخول", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ كلمة مرور خاطئة")

    return False

# ========== الواجهة الرئيسية ==========
def main_app():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")

    # Header
    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced IPTV Checker & Scanner</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        if st.button("🚪 تسجيل خروج", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()
        st.markdown("### 📊 إحصائيات")
        data = load_data()
        st.metric("إجمالي السيرفرات المحفوظة", len(data))

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 فحص سيرفر", "📋 فحص قائمة", "💾 المحفوظات", "📖 معلومات"])

    # ===== Tab 1: فحص سيرفر واحد =====
    with tab1:
        st.subheader("🔍 فحص سيرفر واحد")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            url = st.text_input("🌐 رابط السيرفر", placeholder="http://example.com:8080")
        with col2:
            username = st.text_input("👤 اسم المستخدم", placeholder="اختياري")
        with col3:
            password = st.text_input("🔑 كلمة المرور", type="password", placeholder="اختياري")

        if st.button("🚀 فحص الآن", use_container_width=True, key="check_single"):
            if url:
                with st.spinner("⏳ جاري الفحص..."):
                    result = check_server(normalize_url(url), username or None, password or None)
                    display_result(result)

                # حفظ
                if st.button("💾 حفظ النتيجة"):
                    data = load_data()
                    data[hash_url(result["url"])] = result
                    save_data(data)
                    st.success("✅ تم الحفظ")
            else:
                st.warning("⚠️ أدخل رابط السيرفر")

    # ===== Tab 2: فحص قائمة =====
    with tab2:
        st.subheader("📋 فحص قائمة سيرفرات")
        text_input = st.text_area(
            "📝 الصق السيرفرات (سطر لكل سيرفر أو في نص)",
            height=200,
            placeholder="http://server1.com:8080\nhttp://server2.com:8080"
        )

        col1, col2 = st.columns(2)
        with col1:
            bulk_user = st.text_input("👤 اسم المستخدم (اختياري)", key="bulk_user")
        with col2:
            bulk_pass = st.text_input("🔑 كلمة المرور (اختياري)", type="password", key="bulk_pass")

        if st.button("🚀 فحص الكل", use_container_width=True, key="check_bulk"):
            if text_input:
                servers = extract_servers_from_text(text_input)
                if not servers:
                    st.warning("⚠️ لم يتم العثور على سيرفرات")
                else:
                    st.info(f"🔎 تم العثور على {len(servers)} سيرفر")

                    progress = st.progress(0)
                    status = st.empty()

                    def cb(done, total):
                        progress.progress(done / total)
                        status.text(f"⏳ {done}/{total}")

                    results = check_servers_parallel(
                        servers,
                        bulk_user or None,
                        bulk_pass or None,
                        progress_cb=cb
                    )

                    progress.empty()
                    status.empty()

                    # إحصائيات
                    success = sum(1 for r in results if "✅" in r.get("status", ""))
                    failed = len(results) - success

                    c1, c2, c3 = st.columns(3)
                    c1.metric("✅ ناجح", success)
                    c2.metric("❌ فاشل", failed)
                    c3.metric("📊 الإجمالي", len(results))

                    # عرض النتائج
                    st.divider()
                    for r in results:
                        display_result(r)

                    # حفظ الكل
                    data = load_data()
                    for r in results:
                        data[hash_url(r["url"])] = r
                    save_data(data)
                    st.success(f"✅ تم حفظ {len(results)} نتيجة")
            else:
                st.warning("⚠️ الصق السيرفرات أولاً")

    # ===== Tab 3: المحفوظات =====
    with tab3:
        st.subheader("💾 السيرفرات المحفوظة")
        data = load_data()
        if not data:
            st.info("📭 لا توجد بيانات محفوظة")
        else:
            # بحث
            search = st.text_input("🔎 بحث", placeholder="ابحث عن سيرفر...")

            filtered = list(data.values())
            if search:
                filtered = [r for r in filtered if search.lower() in r["url"].lower()]

            st.write(f"**النتائج: {len(filtered)}**")

            # تصدير
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 تصدير JSON"):
                    st.download_button(
                        "⬇️ تحميل",
                        json.dumps(filtered, ensure_ascii=False, indent=2),
                        file_name=f"iptv_export_{int(time.time())}.json",
                        mime="application/json"
                    )
            with col2:
                if st.button("🗑️ حذف الكل"):
                    save_data({})
                    st.rerun()

            st.divider()
            for r in filtered:
                display_result(r, show_delete=True)

    # ===== Tab 4: معلومات =====
    with tab4:
        st.subheader("📖 معلومات")
        st.markdown("""
        ### 🔥 BEAST V17 PRO
        
        **المميزات:**
        - ✅ فحص سيرفرات IPTV بشكل متوازي (20 ثريد)
        - ✅ استخراج تلقائي للسيرفرات من نص
        - ✅ عرض معلومات الاشتراك (تاريخ الانتهاء، الاتصالات)
        - ✅ عد القنوات والأفلام والمسلسلات
        - ✅ حفظ واسترجاع النتائج
        - ✅ تصدير JSON
        
        **الإصدار:** 17.0 PRO
        **آخر تحديث:** 2024
        """)

# ========== عرض النتيجة ==========
def display_result(r, show_delete=False):
    """عرض نتيجة فحص بشكل منسق"""
    status = r.get("status", "unknown")

    # تحديد اللون
    if "✅" in status:
        color = "#00ff88"
    elif "⚠️" in status:
        color = "#ffaa00"
    else:
        color = "#ff4b2b"

    with st.expander(f"🌐 {r['url']}  —  {status}"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📡 معلومات الاتصال**")
            st.write(f"HTTP: `{r.get('http_code', 'N/A')}`")
            st.write(f"⏱️ الوقت: `{r.get('response_time', 'N/A')}s`")
            st.write(f"🌍 المنطقة: `{r.get('timezone', 'N/A')}`")

        with col2:
            st.markdown("**👤 معلومات الاشتراك**")
            st.write(f"الحالة: `{r.get('status', 'N/A')}`")
            st.write(f"📅 الانتهاء: `{r.get('exp_date_readable', r.get('exp_date', 'N/A'))}`")
            st.write(f"🔗 الاتصالات: `{r.get('active_connections', 'N/A')}/{r.get('max_connections', 'N/A')}`")

        with col3:
            st.markdown("**📺 المحتوى**")
            st.write(f"📺 قنوات: `{r.get('channels', 0)}`")
            st.write(f"🎬 أفلام: `{r.get('movies', 0)}`")
            st.write(f"📼 مسلسلات: `{r.get('series', 0)}`")

        if r.get("error"):
            st.error(f"⚠️ {r['error']}")

        if show_delete:
            if st.button("🗑️ حذف", key=f"del_{r['url']}"):
                data = load_data()
                data.pop(hash_url(r["url"]), None)
                save_data(data)
                st.rerun()

# ========== نقطة البداية ==========
def main():
    # تعطيل تحذيرات SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main()
