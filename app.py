import streamlit as st
import requests
import re
import time
import hashlib
import json
import os
from datetime import datetime
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== إعدادات ==========
REQUEST_TIMEOUT = 10
MAX_WORKERS = 10
DATA_FILE = "iptv_data.json"
PASSWORD = "BEAST_V17_PRO"
GITHUB_API = "https://api.github.com"

# ========== حفظ وتحميل ==========
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

# ========== جلسة GitHub ==========
def get_gh_headers(token=None):
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "BEAST-V17-PRO",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

# ========== البحث في GitHub Code ==========
def search_github_code(query, token=None, per_page=30, page=1):
    """يبحث في كود GitHub عن الكويري"""
    url = f"{GITHUB_API}/search/code"
    params = {"q": query, "per_page": per_page, "page": page}
    try:
        r = requests.get(url, headers=get_gh_headers(token), params=params, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            return {"error": "توكن غير صالح أو منتهي", "status": 401}
        elif r.status_code == 403:
            return {"error": "تجاوزت حد الطلبات (Rate Limit)", "status": 403}
        elif r.status_code == 422:
            return {"error": "الكويري غير صالح", "status": 422}
        else:
            return {"error": f"HTTP {r.status_code}", "status": r.status_code}
    except Exception as e:
        return {"error": str(e)[:120]}

# ========== البحث في GitHub Repos ==========
def search_github_repos(query, token=None, per_page=30, page=1):
    url = f"{GITHUB_API}/search/repositories"
    params = {"q": query, "per_page": per_page, "page": page, "sort": "updated"}
    try:
        r = requests.get(url, headers=get_gh_headers(token), params=params, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}", "status": r.status_code}
    except Exception as e:
        return {"error": str(e)[:120]}

# ========== جلب محتوى ملف ==========
def fetch_file_content(repo_full_name, path, token=None):
    url = f"{GITHUB_API}/repos/{repo_full_name}/contents/{path}"
    try:
        r = requests.get(url, headers=get_gh_headers(token), timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data.get("encoding") == "base64":
                return b64decode(data["content"]).decode("utf-8", errors="ignore")
            return data.get("content", "")
    except Exception:
        pass
    return None

# ========== استخراج سيرفرات Xtream من نص ==========
def extract_xtream_servers(text):
    """يستخرج سيرفرات Xtream Codes من نص"""
    servers = set()

    # 1) get.php?username=..&password=..
    for m in re.finditer(
        r'(https?://[^\s"\'<>]+?)/get\.php\?username=([^\s"\'&<>]+)&password=([^\s"\'&<>]+)',
        text, re.IGNORECASE
    ):
        base = m.group(1).rstrip("/")
        user = m.group(2)
        pwd = m.group(3)
        servers.add(f"{base}|{user}|{pwd}")

    # 2) player_api.php?username=..&password=..
    for m in re.finditer(
        r'(https?://[^\s"\'<>]+?)/player_api\.php\?username=([^\s"\'&<>]+)&password=([^\s"\'&<>]+)',
        text, re.IGNORECASE
    ):
        base = m.group(1).rstrip("/")
        user = m.group(2)
        pwd = m.group(3)
        servers.add(f"{base}|{user}|{pwd}")

    # 3) panel_api.php
    for m in re.finditer(
        r'(https?://[^\s"\'<>]+?)/panel_api\.php\?username=([^\s"\'&<>]+)&password=([^\s"\'&<>]+)',
        text, re.IGNORECASE
    ):
        base = m.group(1).rstrip("/")
        user = m.group(2)
        pwd = m.group(3)
        servers.add(f"{base}|{user}|{pwd}")

    # 4) Xtream codes pairs في JSON
    for m in re.finditer(r'"host"\s*:\s*"(https?://[^"]+)"', text):
        servers.add(m.group(1).rstrip("/"))

    # 5) host:port
    for m in re.finditer(r'\b(https?://\d{1,3}(?:\.\d{1,3}){3}:\d{2,5})\b', text):
        servers.add(m.group(1).rstrip("/"))

    return sorted(servers)

# ========== استخراج m3u8 و روابط تشغيل ==========
def extract_streams(text):
    streams = set()
    for m in re.finditer(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', text):
        streams.add(m.group(0))
    for m in re.finditer(r'https?://[^\s"\'<>]+/live/[^\s"\'<>]+\.(ts|m3u8)', text):
        streams.add(m.group(0))
    return sorted(streams)

# ========== فحص سيرفر Xtream ==========
def check_xtream(entry, timeout=REQUEST_TIMEOUT):
    """يفحص سيرفر Xtream ويرجّع معلوماته"""
    result = {
        "entry": entry,
        "url": entry, "username": None, "password": None,
        "status": "❌", "exp_date": None, "max_conn": None,
        "active": None, "channels": 0, "movies": 0, "series": 0,
        "timezone": None, "error": None
    }

    # فك الـ entry
    if "|" in entry:
        parts = entry.split("|")
        base = parts[0].rstrip("/")
        user = parts[1] if len(parts) > 1 else None
        pwd = parts[2] if len(parts) > 2 else None
    else:
        base = entry.rstrip("/")
        user, pwd = None, None

    result["url"] = base
    result["username"] = user
    result["password"] = pwd

    try:
        if user and pwd:
            api = f"{base}/player_api.php?username={user}&password={pwd}"
        else:
            api = f"{base}/player_api.php"

        r = requests.get(api, timeout=timeout, verify=False,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result

        try:
            data = r.json()
        except Exception:
            result["error"] = "ليس JSON"
            return result

        user_info = data.get("user_info", {}) or {}
        server_info = data.get("server_info", {}) or {}

        if user_info:
            result["status"] = "✅ يعمل"
            result["exp_date"] = user_info.get("exp_date")
            result["max_conn"] = user_info.get("max_connections")
            result["active"] = user_info.get("active_cons")
            result["timezone"] = server_info.get("timezone")

            if result["exp_date"]:
                try:
                    ts = int(result["exp_date"])
                    result["exp_date_readable"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                except Exception:
                    result["exp_date_readable"] = str(result["exp_date"])

            # عد المحتوى
            try:
                ch = requests.get(f"{api}&action=get_live_streams", timeout=timeout, verify=False)
                if ch.status_code == 200:
                    result["channels"] = len(ch.json())
            except Exception:
                pass
            try:
                mv = requests.get(f"{api}&action=get_vod_streams", timeout=timeout, verify=False)
                if mv.status_code == 200:
                    result["movies"] = len(mv.json())
            except Exception:
                pass
            try:
                sr = requests.get(f"{api}&action=get_series", timeout=timeout, verify=False)
                if sr.status_code == 200:
                    result["series"] = len(sr.json())
            except Exception:
                pass
        else:
            result["status"] = "⚠️ بدون بيانات"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result

# ========== شاشة الدخول ==========
def login_screen():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg,#ff4b2b,#ff416c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size:3em; font-weight:bold; text-align:center;
    }
    .sub-header { text-align:center; color:#888; margin-bottom:2em; }
    .stButton > button {
        background: linear-gradient(90deg,#ff4b2b,#ff416c);
        color:white; border:none; border-radius:8px; font-weight:bold;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GitHub Xtream Codes Hunter</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("🔐 كلمة المرور", type="password")
        if st.button("🚀 دخول", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ كلمة مرور خاطئة")

# ========== الواجهة الرئيسية ==========
def main_app():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")
    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GitHub Xtream Codes Hunter</div>', unsafe_allow_html=True)

    # ===== Sidebar =====
    with st.sidebar:
        st.header("⚙️ الإعدادات")

        # ✅ إضافة التوكن
        st.markdown("### 🔑 GitHub Token")
        token = st.text_input(
            "أدخل التوكن (اختياري لكن يزود الحد)",
            type="password",
            value=st.session_state.get("gh_token", ""),
            help="بدون توكن = 10 طلبات/دقيقة | مع توكن = 30 طلب/دقيقة"
        )
        st.session_state["gh_token"] = token

        if token:
            st.success("✅ تم إضافة التوكن")
        else:
            st.warning("⚠️ بدون توكن (حدود قليلة)")

        st.divider()
        if st.button("🚪 تسجيل خروج", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()
        st.markdown("### 📊 إحصائيات")
        data = load_data()
        st.metric("النتائج المحفوظة", len(data))

    # ===== Tabs =====
    tabs = st.tabs([
        "🔍 بحث Xtream في GitHub",
        "📦 بحث Repos",
        "🎯 استخراج من نص",
        "💾 المحفوظات"
    ])

    # ===== Tab 1: بحث Xtream في GitHub Code =====
    with tab1:
        st.subheader("🔍 البحث عن سيرفرات Xtream Codes في GitHub")
        st.caption("يبحث في أكواد GitHub عن أنماط Xtream مثل `player_api.php?username=`")

        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input(
                "🔎 كلمة البحث",
                value='player_api.php?username=',
                help="جرّب: panel_api.php, get.php?username, Xtream Codes, etc."
            )
        with col2:
            pages = st.number_input("صفحات", 1, 10, 2)

        col1, col2, col3 = st.columns(3)
        with col1:
            per_page = st.slider("نتائج/صفحة", 10, 100, 30)
        with col2:
            auto_check = st.checkbox("فحص السيرفرات تلقائياً", value=True)
        with col3:
            max_check = st.number_input("حد الفحص", 5, 200, 30)

        if st.button("🚀 ابدأ البحث", use_container_width=True):
            token = st.session_state.get("gh_token", "") or None

            all_items = []
            progress = st.progress(0)
            status = st.empty()

            for p in range(1, int(pages) + 1):
                status.text(f"⏳ جلب صفحة {p}...")
                res = search_github_code(query, token=token, per_page=int(per_page), page=p)

                if "error" in res:
                    st.error(f"❌ {res['error']}")
                    break

                items = res.get("items", [])
                if not items:
                    break
                all_items.extend(items)
                progress.progress(p / int(pages))

                # GitHub search rate limit: 10 req/min بدون توكن
                if p < pages and not token:
                    time.sleep(6)

            progress.empty(); status.empty()

            if not all_items:
                st.warning("⚠️ لا توجد نتائج")
            else:
                st.success(f"✅ تم العثور على {len(all_items)} ملف")

                # جلب محتوى الملفات واستخراج السيرفرات
                all_servers = set()
                progress = st.progress(0)
                status = st.empty()

                for i, item in enumerate(all_items):
                    repo = item["repository"]["full_name"]
                    path = item["path"]
                    status.text(f"⏳ تحليل {i+1}/{len(all_items)}")

                    content = fetch_file_content(repo, path, token)
                    if content:
                        found = extract_xtream_servers(content)
                        all_servers.update(found)
                        # أضف أيضاً روابط m3u8
                        streams = extract_streams(content)
                        all_servers.update(streams)

                    progress.progress((i+1) / len(all_items))
                    time.sleep(0.3)

                progress.empty(); status.empty()

                servers = sorted(all_servers)
                st.info(f"🎯 تم استخراج {len(servers)} سيرفر/رابط")

                st.session_state["xtream_servers"] = servers

                # عرض
                if servers:
                    st.divider()
                    st.markdown("### 📋 السيرفرات المستخرجة")
                    with st.expander("👁️ عرض الكل"):
                        st.code("\n".join(servers), language="text")

                    st.download_button(
                        "📥 تحميل TXT",
                        "\n".join(servers),
                        file_name=f"xtream_{int(time.time())}.txt",
                        mime="text/plain"
                    )

                    # فحص
                    if auto_check:
                        st.divider()
                        st.markdown("### 🔬 فحص السيرفرات")
                        to_check = servers[:int(max_check)]
                        progress = st.progress(0)
                        status = st.empty()
                        results = []

                        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                            futures = {ex.submit(check_xtream, s): s for s in to_check}
                            done = 0
                            for fut in as_completed(futures):
                                try:
                                    results.append(fut.result())
                                except Exception as e:
                                    results.append({"entry": futures[fut], "status": "❌", "error": str(e)[:80]})
                                done += 1
                                progress.progress(done / len(to_check))
                                status.text(f"⏳ {done}/{len(to_check)}")

                        progress.empty(); status.empty()

                        # إحصائيات
                        ok = sum(1 for r in results if "✅" in r.get("status", ""))
                        c1, c2, c3 = st.columns(3)
                        c1.metric("✅ يعمل", ok)
                        c2.metric("❌ فاشل", len(results) - ok)
                        c3.metric("📊 الإجمالي", len(results))

                        # عرض
                        for r in results:
                            if "✅" in r.get("status", ""):
                                with st.expander(f"✅ {r['url']} — {r.get('channels',0)} قناة"):
                                    st.write(f"👤 User: `{r.get('username')}`")
                                    st.write(f"🔑 Pass: `{r.get('password')}`")
                                    st.write(f"📅 Exp: `{r.get('exp_date_readable','N/A')}`")
                                    st.write(f"🔗 Conn: `{r.get('active')}/{r.get('max_conn')}`")
                                    st.write(f"🌍 TZ: `{r.get('timezone','N/A')}`")
                                    st.write(f"📺 Channels: `{r.get('channels',0)}` | 🎬 Movies: `{r.get('movies',0)}` | 📼 Series: `{r.get('series',0)}`")

                        # حفظ
                        data = load_data()
                        for r in results:
                            if "✅" in r.get("status", ""):
                                key = hashlib.md5(r["entry"].encode()).hexdigest()[:12]
                                data[key] = r
                        save_data(data)

    # ===== Tab 2: بحث Repos =====
    with tab2:
        st.subheader("📦 البحث عن Repos تحتوي على Xtream Codes")
        query = st.text_input("🔎 كلمة البحث في الريبوهات", value="xtream codes playlist")
        pages = st.number_input("صفحات", 1, 5, 1, key="repo_pages")

        if st.button("🚀 ابحث في Repos", use_container_width=True):
            token = st.session_state.get("gh_token", "") or None
            all_repos = []
            for p in range(1, int(pages)+1):
                res = search_github_repos(query, token=token, page=p)
                if "error" in res:
                    st.error(res["error"]); break
                all_repos.extend(res.get("items", []))
                if not token: time.sleep(6)

            st.success(f"✅ {len(all_repos)} repo")
            for r in all_repos:
                with st.expander(f"📦 {r['full_name']} ⭐{r['stargazers_count']}"):
                    st.write(f"📝 {r.get('description','—')}")
                    st.write(f"🔗 {r['html_url']}")
                    st.write(f"🕒 آخر تحديث: {r['updated_at']}")

    # ===== Tab 3: استخراج من نص =====
    with tab3:
        st.subheader("🎯 استخراج سيرفرات من نص")
        text = st.text_area("الصق النص", height=250,
                            placeholder="http://server.com:8080/get.php?username=USER&password=PASS")
        if st.button("🔎 استخراج", use_container_width=True):
            servers = extract_xtream_servers(text)
            streams = extract_streams(text)
            if servers or streams:
                st.success(f"✅ {len(servers)} Xtream + {len(streams)} stream")
                if servers:
                    st.markdown("**Xtream Servers:**")
                    st.code("\n".join(servers), language="text")
                if streams:
                    st.markdown("**Streams:**")
                    st.code("\n".join(streams), language="text")
            else:
                st.warning("⚠️ لا يوجد")

    # ===== Tab 4: المحفوظات =====
    with tab4:
        st.subheader("💾 المحفوظات")
        data = load_data()
        if not data:
            st.info("📭 فاضي")
        else:
            st.write(f"**{len(data)} نتيجة**")
            for k, v in data.items():
                with st.expander(f"✅ {v.get('url','?')} — {v.get('channels',0)} قناة"):
                    st.json(v)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 تصدير JSON",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    file_name="export.json", mime="application/json")
            with col2:
                if st.button("🗑️ حذف الكل"):
                    save_data({}); st.rerun()

# ========== نقطة البداية ==========
def main():
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
