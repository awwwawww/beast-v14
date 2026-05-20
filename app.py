import streamlit as st
import requests
import re
import threading
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# إعدادات
MAX_WORKERS = 8
REQUEST_TIMEOUT = 4
PAGES_PER_DORK = 15

# ================== دوال البحث الأساسية ==================
def extract_xtream_accounts(content):
    pattern = r'(https?://[a-zA-Z0-9.-]+:\d+)/(?:player_api|get)\.php\?(?:username|user)=([^&\s]+)&(?:password|pass)=([^&\s]+)'
    return re.findall(pattern, content, re.IGNORECASE)

def check_account(host, user, pw, proxy=None):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(api, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("user_info", {}).get("status") == "Active":
            info = data["user_info"]
            exp = info.get('exp_date')
            exp_str = datetime.fromtimestamp(int(exp)).strftime('%Y-%m-%d') if exp else "دائم"
            return {"host": host, "user": user, "pass": pw, "exp": exp_str}
    except:
        return None
    return None

def load_channels(server, proxy=None):
    try:
        url = f"{server['host']}/player_api.php?username={server['user']}&password={server['pass']}&action=get_live_streams"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(url, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            channels = resp.json()
            if isinstance(channels, list):
                return channels
    except:
        pass
    return []

def search_github(dork, token, page, proxy=None):
    url = f"https://api.github.com/search/code?q={dork}&per_page=100&page={page}"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if resp.status_code == 200:
            return resp.json().get('items', [])
    except:
        pass
    return []

def process_raw(raw_url, proxy):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(raw_url, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if resp.status_code != 200:
            return []
        content = resp.text
        matches = extract_xtream_accounts(content)
        return [{"host": h, "user": u, "pass": p} for h, u, p in matches]
    except:
        return []

# ================== واجهة Streamlit ==================
st.set_page_config(page_title="IPTV Web Hunter", layout="wide", page_icon="📺")
st.title("🔥 IPTV WEB HUNTER - صيد حسابات + مشغل ويب")
st.markdown("---")

# تهيئة session_state بشكل آمن
if "accounts" not in st.session_state:
    st.session_state.accounts = []
if "servers" not in st.session_state:
    st.session_state.servers = []
if "channels_cache" not in st.session_state:
    st.session_state.channels_cache = {}
if "current_server" not in st.session_state:
    st.session_state.current_server = None
if "current_channels" not in st.session_state:
    st.session_state.current_channels = []
if "searching" not in st.session_state:
    st.session_state.searching = False
if "log" not in st.session_state:
    st.session_state.log = []
if "pending_logs" not in st.session_state:
    st.session_state.pending_logs = []   # رسائل مؤقتة من الخيط
if "pending_accounts" not in st.session_state:
    st.session_state.pending_accounts = []  # حسابات جديدة من الخيط
if "last_rerun" not in st.session_state:
    st.session_state.last_rerun = time.time()

def add_log(msg):
    """إضافة رسالة إلى القائمة المؤقتة (يستدعيها الخيط)"""
    st.session_state.pending_logs.append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")

def flush_pending():
    """نقل الرسائل والحسابات من القوائم المؤقتة إلى القوائم الرئيسية"""
    if st.session_state.pending_logs:
        st.session_state.log = st.session_state.pending_logs + st.session_state.log
        st.session_state.log = st.session_state.log[:50]
        st.session_state.pending_logs.clear()
    if st.session_state.pending_accounts:
        for acc in st.session_state.pending_accounts:
            if not any(s['host'] == acc['host'] for s in st.session_state.servers):
                st.session_state.servers.append(acc)
        st.session_state.accounts.extend(st.session_state.pending_accounts)
        st.session_state.pending_accounts.clear()

# ================== خوارزمية البحث (تعمل في خيط منفصل ولا تلمس session_state مباشرة) ==================
def hunt_process(tokens, proxy):
    unique = set()
    dorks = [
        '"player_api.php?username="', '"get.php?username="', 'filename:m3u "xtream"',
        '"/player_api.php" password', 'xtreamcodes "username" "password"',
        'inurl:player_api.php?username=', 'inurl:get.php?username='
    ]
    token_idx = 0
    dork_idx = 0
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    while st.session_state.searching:
        token = tokens[token_idx % len(tokens)]
        token_idx += 1
        dork = dorks[dork_idx % len(dorks)]
        dork_idx += 1
        for page in range(1, PAGES_PER_DORK + 1):
            if not st.session_state.searching:
                break
            add_log(f"🔍 {dork[:20]} | صفحة {page} | توكن {token[:6]}...")
            items = search_github(dork, token, page, proxy)
            if not items:
                break
            futures = []
            for item in items:
                raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                futures.append(executor.submit(process_raw, raw_url, proxy))
            for future in as_completed(futures):
                if not st.session_state.searching:
                    break
                raw_accounts = future.result()
                for acc in raw_accounts:
                    uid = f"{acc['host']}{acc['user']}{acc['pass']}"
                    if uid in unique:
                        continue
                    unique.add(uid)
                    checked = check_account(acc['host'], acc['user'], acc['pass'], proxy)
                    if checked:
                        add_log(f"✅ شغال: {checked['host']}")
                        st.session_state.pending_accounts.append(checked)
            time.sleep(1)
        time.sleep(2)
    executor.shutdown(wait=False)

# ================== الشريط الجانبي ==================
with st.sidebar:
    st.header("⚙️ الإعدادات")
    tokens_input = st.text_area("GitHub Tokens (سطر لكل توكن)", placeholder="ghp_token1\nghp_token2")
    proxy_input = st.text_input("🚀 بروكسي (اختياري)", placeholder="http://user:pass@ip:port")
    st.markdown("---")
    col1, col2 = st.columns(2)
    start = col1.button("🌪️ بدء الصيد", type="primary", use_container_width=True)
    stop = col2.button("⏹️ إيقاف الصيد", use_container_width=True)
    st.markdown("---")
    st.metric("💎 الحسابات الشغالة", len(st.session_state.accounts))
    st.metric("🗄️ الخوادم النشطة", len(st.session_state.servers))
    st.markdown("---")
    st.subheader("📋 السجل")
    log_area = st.container(height=250)

# ================== معالجة الأزرار ==================
if start and not st.session_state.searching:
    if not tokens_input.strip():
        st.error("يرجى إدخال GitHub Token(s)")
    else:
        st.session_state.searching = True
        tokens = [t.strip() for t in tokens_input.splitlines() if t.strip()]
        proxy = proxy_input if proxy_input else None
        add_log("🚀 بدء البحث عن الحسابات...")
        # تشغيل الخيط
        threading.Thread(target=hunt_process, args=(tokens, proxy), daemon=True).start()
        st.rerun()  # إعادة تحميل الصفحة فوراً لبدء عرض السجل

if stop:
    st.session_state.searching = False
    add_log("⏸️ تم إيقاف البحث.")
    st.rerun()

# ================== عرض السجل ==================
flush_pending()  # تحديث القوائم الرئيسية
with log_area:
    for msg in st.session_state.log[:30]:
        st.text(msg)

# ================== الأعمدة الرئيسية ==================
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("🗄️ الخوادم النشطة")
    if st.session_state.servers:
        server_options = [f"{s['host']} | {s['user']}" for s in st.session_state.servers]
        selected_server_str = st.selectbox("اختر خادماً:", server_options, key="server_select")
        if selected_server_str:
            idx = server_options.index(selected_server_str)
            selected_server = st.session_state.servers[idx]
            if st.session_state.current_server != selected_server:
                st.session_state.current_server = selected_server
                # تحميل القنوات من الكاش أو من السيرفر
                key = f"{selected_server['host']}|{selected_server['user']}"
                if key in st.session_state.channels_cache:
                    st.session_state.current_channels = st.session_state.channels_cache[key]
                else:
                    with st.spinner("جاري تحميل القنوات..."):
                        ch = load_channels(selected_server, proxy_input if proxy_input else None)
                        st.session_state.channels_cache[key] = ch
                        st.session_state.current_channels = ch
                st.rerun()
    else:
        st.info("لا توجد خوادم بعد. ابدأ البحث.")

    st.subheader("📡 قنوات السيرفر")
    if st.session_state.current_channels:
        search_ch = st.text_input("🔍 بحث في القنوات")
        filtered = [c for c in st.session_state.current_channels if search_ch.lower() in c['name'].lower()] if search_ch else st.session_state.current_channels
        ch_names = [f"{c['name']} (ID:{c['stream_id']})" for c in filtered]
        if ch_names:
            selected_ch_name = st.selectbox("اختر قناة:", ch_names, key="channel_select")
            if selected_ch_name:
                idx = ch_names.index(selected_ch_name)
                st.session_state.selected_channel_id = filtered[idx]['stream_id']
        else:
            st.warning("لا توجد قنوات مطابقة")
    else:
        st.info("اختر خادماً أولاً")

with col_right:
    st.subheader("📺 مشغل الفيديو")
    quality = st.selectbox("الجودة", ["M3U8 (HLS)", "TS (أصلي)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
    use_ext = st.checkbox("تشغيل خارجي (رابط فقط)")

    if st.button("▶️ تشغيل", type="primary") and st.session_state.get("selected_channel_id") and st.session_state.current_server:
        server = st.session_state.current_server
        ext = "m3u8" if "M3U8" in quality else "ts"
        url = f"{server['host']}/live/{server['user']}/{server['pass']}/{st.session_state.selected_channel_id}.{ext}"
        bitrate = {"720p":"720","480p":"480","360p":"360","240p":"240","144p":"144","96p":"96"}
        if quality in bitrate:
            url += f"?bitrate={bitrate[quality]}"
        if use_ext:
            st.markdown(f"رابط البث: `{url}`")
        else:
            if ext == "m3u8":
                st.components.v1.html(f"""
                <video id="v" controls autoplay width="100%" height="auto"></video>
                <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                <script>
                    var vid = document.getElementById('v');
                    if (Hls.isSupported()) {{
                        var hls = new Hls();
                        hls.loadSource('{url}');
                        hls.attachMedia(vid);
                        hls.on(Hls.Events.MANIFEST_PARSED, function() {{ vid.play(); }});
                    }} else if (vid.canPlayType('application/vnd.apple.mpegurl')) {{
                        vid.src = '{url}';
                        vid.addEventListener('loadedmetadata', function() {{ vid.play(); }});
                    }}
                </script>
                """, height=400)
            else:
                st.video(url)  # تجربة بسيطة لـ TS
        add_log(f"تشغيل: {url[:80]}...")
    elif not st.session_state.get("selected_channel_id"):
        st.warning("اختر قناة أولاً")
    elif not st.session_state.current_server:
        st.warning("اختر خادماً أولاً")

# ================== التحديث التلقائي أثناء البحث ==================
if st.session_state.searching:
    # نتحقق من الوقت لئلا نُحدث بشكل متكرر جداً
    now = time.time()
    if now - st.session_state.last_rerun > 2.5:
        st.session_state.last_rerun = now
        st.rerun()
else:
    st.caption("يمكنك بدء البحث بالضغط على زر 'بدء الصيد'")
