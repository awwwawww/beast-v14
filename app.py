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
REQUEST_TIMEOUT = 10
MAX_WORKERS = 15
DATA_FILE = "iptv_data.json"
PASSWORD = "BEAST_V17_PRO"

# ========== مصادر GitHub ==========
GITHUB_SOURCES = [
    # ملفات M3U شهيرة على GitHub (Raw)
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/eg.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sa.m3u",
    # مصادر إضافية
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/categories/news.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "https://iptv-org.github.io/iptv/categories/music.m3u",
]

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

# ========== جلسة ==========
def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    })
    return s

# ========== جلب ملف M3U من GitHub ==========
def fetch_m3u(url, timeout=REQUEST_TIMEOUT):
    """يجيب ملف M3U ويرجّع قائمة قنوات"""
    session = get_session()
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code != 200:
            return {"url": url, "error": f"HTTP {r.status_code}", "channels": []}
        text = r.text
        channels = parse_m3u(text)
        return {"url": url, "error": None, "channels": channels, "raw": text}
    except Exception as e:
        return {"url": url, "error": str(e)[:120], "channels": []}

# ========== تحليل M3U ==========
def parse_m3u(text):
    """تحليل ملف M3U ويرجّع قائمة قنوات"""
    channels = []
    lines = text.splitlines()
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            # استخراج الاسم
            name = ""
            if "," in line:
                name = line.split(",", 1)[1].strip()
            # استخراج logo
            logo = ""
            m = re.search(r'tvg-logo="([^"]*)"', line)
            if m:
                logo = m.group(1)
            # استخراج group
            group = ""
            m = re.search(r'group-title="([^"]*)"', line)
            if m:
                group = m.group(1)
            current = {"name": name, "logo": logo, "group": group}
        elif line.startswith("http"):
            if current:
                current["url"] = line
                channels.append(current)
                current = {}
            else:
                channels.append({"name": "Unknown", "url": line, "logo": "", "group": ""})
    return channels

# ========== جلب متوازي من كل المصادر ==========
def fetch_all_sources(sources, progress_cb=None):
    results = []
    total = len(sources)
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_m3u, s): s for s in sources}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"url": futures[fut], "error": str(e), "channels": []})
            done += 1
            if progress_cb:
                progress_cb(done, total)
    return results

# ========== استخراج سيرفرات IPTV من أي نص ==========
def extract_servers(text):
    servers = set()
    for m in re.finditer(r'https?://[^\s<>"\']+', text):
        u = m.group(0).rstrip("/")
        servers.add(u)
    for m in re.finditer(r'\b(\d{1,3}(?:\.\d{1,3}){3}:\d{2,5})\b', text):
        servers.add("http://" + m.group(1))
    return sorted(servers)

# ========== شاشة الدخول ==========
def login_screen():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg,#ff4b2b,#ff416c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3em; font-weight: bold; text-align:center;
        }
        .sub-header { text-align:center; color:#888; margin-bottom:2em; }
        .stButton > button {
            background: linear-gradient(90deg,#ff4b2b,#ff416c);
            color:white; border:none; border-radius:8px; font-weight:bold;
        }
        .stButton > button:hover { transform: scale(1.02); }
        .ch-card {
            background:#1e1e1e; padding:10px; border-radius:8px;
            margin:5px 0; border-left:4px solid #ff4b2b;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">IPTV Results Fetcher from GitHub</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("🔐 كلمة المرور", type="password")
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

    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">IPTV Results Fetcher from GitHub</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        if st.button("🚪 تسجيل خروج", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📊 إحصائيات")
        data = load_data()
        st.metric("القنوات المحفوظة", sum(len(v.get("channels", [])) for v in data.values()))

    tabs = st.tabs(["📡 جلب من GitHub", "🔗 روابط مخصصة", "🎯 استخراج سيرفرات", "💾 المحفوظات"])

    # ===== Tab 1: جلب من GitHub =====
    with tab1:
        st.subheader("📡 جلب قوائم IPTV جاهزة من GitHub")
        st.caption("اضغط الزر لجلب القوائم من مصادر GitHub الشهيرة")

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("🚀 جلب الآن", use_container_width=True):
                progress = st.progress(0)
                status = st.empty()

                def cb(done, total):
                    progress.progress(done/total)
                    status.text(f"⏳ {done}/{total}")

                results = fetch_all_sources(GITHUB_SOURCES, cb)
                progress.empty(); status.empty()

                # تجميع
                total_channels = 0
                all_channels = []
                for r in results:
                    if r.get("channels"):
                        total_channels += len(r["channels"])
                        all_channels.extend(r["channels"])

                c1, c2, c3 = st.columns(3)
                c1.metric("📦 المصادر", len(GITHUB_SOURCES))
                c2.metric("✅ نجح", sum(1 for r in results if not r.get("error")))
                c3.metric("📺 القنوات", total_channels)

                st.session_state["gh_results"] = results
                st.session_state["gh_all"] = all_channels

                # حفظ
                data = load_data()
                for r in results:
                    if r.get("channels"):
                        key = hashlib.md5(r["url"].encode()).hexdigest()[:12]
                        data[key] = {"url": r["url"], "channels": r["channels"], "ts": datetime.now().isoformat()}
                save_data(data)
                st.success("✅ تم الجلب والحفظ")

        with col2:
            if st.button("🗑️ مسح النتائج", use_container_width=True):
                st.session_state.pop("gh_results", None)
                st.session_state.pop("gh_all", None)
                st.rerun()

        # عرض
        results = st.session_state.get("gh_results", [])
        if results:
            st.divider()
            st.markdown("### 📋 النتائج")

            # فلترة
            search = st.text_input("🔎 بحث في القنوات", placeholder="اسم قناة...")
            all_channels = st.session_state.get("gh_all", [])

            if search:
                filtered = [c for c in all_channels if search.lower() in c.get("name","").lower()]
                st.write(f"**{len(filtered)} نتيجة**")
                for c in filtered[:500]:
                    st.markdown(
                        f'<div class="ch-card">📺 <b>{c["name"]}</b><br>'
                        f'<small>{c.get("group","")} — {c["url"][:80]}...</small></div>',
                        unsafe_allow_html=True
                    )
            else:
                for r in results:
                    if r.get("error"):
                        st.error(f"❌ {r['url']} — {r['error']}")
                    else:
                        with st.expander(f"✅ {r['url'].split('/')[-1]} — {len(r['channels'])} قناة"):
                            for c in r["channels"][:100]:
                                st.markdown(f"📺 **{c['name']}** — `{c.get('group','')}`")
                            if len(r["channels"]) > 100:
                                st.caption(f"... و {len(r['channels'])-100} قناة أخرى")

    # ===== Tab 2: روابط مخصصة =====
    with tab2:
        st.subheader("🔗 جلب من روابط M3U مخصصة")
        urls_text = st.text_area("الصق روابط M3U (سطر لكل رابط)", height=150,
                                  placeholder="https://example.com/list.m3u")
        if st.button("🚀 جلب الروابط", use_container_width=True):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            if urls:
                progress = st.progress(0); status = st.empty()
                def cb(done, total):
                    progress.progress(done/total)
                    status.text(f"⏳ {done}/{total}")
                results = fetch_all_sources(urls, cb)
                progress.empty(); status.empty()
                st.session_state["custom_results"] = results
            else:
                st.warning("⚠️ أدخل روابط أولاً")

        for r in st.session_state.get("custom_results", []):
            if r.get("error"):
                st.error(f"❌ {r['url']} — {r['error']}")
            else:
                with st.expander(f"✅ {r['url']} — {len(r['channels'])} قناة"):
                    for c in r["channels"][:200]:
                        st.markdown(f"📺 **{c['name']}** — `{c.get('group','')}`")

    # ===== Tab 3: استخراج سيرفرات =====
    with tab3:
        st.subheader("🎯 استخراج سيرفرات IPTV من أي نص")
        text = st.text_area("الصق النص هنا", height=200,
                            placeholder="http://server.com:8080\n1.2.3.4:8080")
        if st.button("🔎 استخراج", use_container_width=True):
            servers = extract_servers(text)
            if servers:
                st.success(f"✅ تم العثور على {len(servers)} سيرفر")
                st.code("\n".join(servers), language="text")
                st.download_button("📥 تحميل", "\n".join(servers),
                                   file_name="servers.txt", mime="text/plain")
            else:
                st.warning("⚠️ لم يتم العثور على سيرفرات")

    # ===== Tab 4: المحفوظات =====
    with tab4:
        st.subheader("💾 النتائج المحفوظة")
        data = load_data()
        if not data:
            st.info("📭 لا توجد بيانات")
        else:
            st.write(f"**{len(data)} مصدر محفوظ**")
            for k, v in data.items():
                with st.expander(f"📦 {v['url']} — {len(v.get('channels',[]))} قناة"):
                    st.caption(f"🕒 {v.get('ts','')}")
                    for c in v.get("channels", [])[:50]:
                        st.markdown(f"📺 **{c['name']}** — `{c.get('group','')}`")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 تصدير JSON",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    file_name="iptv_export.json", mime="application/json")
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
