import streamlit as st
import requests
import re
import threading
import time
import json
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# إعدادات
MAX_WORKERS = 10
REQUEST_TIMEOUT = 4
PAGES_PER_DORK = 20

# دالة البحث عن حسابات xtream
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
        return []
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

# ---------- واجهة Streamlit ----------
st.set_page_config(page_title="IPTV Web Hunter", layout="wide", page_icon="📺")
st.title("🔥 IPTV WEB HUNTER - صيد حسابات + مشغل ويب")
st.markdown("---")

# تهيئة حالة الجلسة
if "accounts" not in st.session_state:
    st.session_state.accounts = []          # قائمة الحسابات النشطة
if "servers" not in st.session_state:
    st.session_state.servers = []           # الخوادم النشطة (مبسطة)
if "channels_cache" not in st.session_state:
    st.session_state.channels_cache = {}    # {server_key: channels}
if "current_server" not in st.session_state:
    st.session_state.current_server = None
if "current_channels" not in st.session_state:
    st.session_state.current_channels = []
if "searching" not in st.session_state:
    st.session_state.searching = False
if "log" not in st.session_state:
    st.session_state.log = []

def add_log(msg):
    st.session_state.log.insert(0, f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
    if len(st.session_state.log) > 50:
        st.session_state.log.pop()

# شريط جانبي للإعدادات
with st.sidebar:
    st.header("⚙️ الإعدادات")
    tokens_input = st.text_area("GitHub Tokens (سطر لكل توكن)", placeholder="ghp_yourtoken1\nghp_yourtoken2")
    proxy_input = st.text_input("🚀 بروكسي (اختياري)", placeholder="http://user:pass@ip:port")
    st.markdown("---")
    start_btn = st.button("🌪️ بدء الصيد", type="primary", use_container_width=True)
    stop_btn = st.button("⏹️ إيقاف الصيد", use_container_width=True)
    st.markdown("---")
    st.subheader("📊 النتائج")
    accounts_count = st.empty()
    servers_count = st.empty()
    st.markdown("---")
    st.subheader("📋 سجل العمليات")
    log_container = st.container(height=200)

# الأعمدة الرئيسية
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🗄️ الخوادم النشطة")
    server_list = st.empty()
    if st.session_state.servers:
        server_names = [f"{s['host']} | {s['user']}" for s in st.session_state.servers]
        selected_server_name = st.selectbox("اختر خادماً:", server_names, key="server_select")
        idx = server_names.index(selected_server_name) if selected_server_name else None
        if idx is not None and (st.session_state.current_server != st.session_state.servers[idx]):
            st.session_state.current_server = st.session_state.servers[idx]
            # تحميل القنوات
            server_key = f"{st.session_state.current_server['host']}|{st.session_state.current_server['user']}"
            if server_key in st.session_state.channels_cache:
                st.session_state.current_channels = st.session_state.channels_cache[server_key]
                add_log(f"تم تحميل {len(st.session_state.current_channels)} قناة من الذاكرة")
            else:
                with st.spinner("جاري تحميل القنوات..."):
                    channels = load_channels(st.session_state.current_server, proxy_input if proxy_input else None)
                    st.session_state.channels_cache[server_key] = channels
                    st.session_state.current_channels = channels
                    add_log(f"تم تحميل {len(channels)} قناة من السيرفر")
    else:
        st.info("لا توجد خوادم نشطة بعد. ابدأ البحث.")

    st.subheader("📡 قنوات السيرفر المختار")
    if st.session_state.current_channels:
        search_ch = st.text_input("🔍 بحث في القنوات")
        filtered = [ch for ch in st.session_state.current_channels if search_ch.lower() in ch['name'].lower()] if search_ch else st.session_state.current_channels
        channel_names = [f"{ch['name']} (ID:{ch['stream_id']})" for ch in filtered]
        if channel_names:
            selected_channel_name = st.selectbox("اختر قناة:", channel_names, key="channel_select")
            selected_channel = filtered[channel_names.index(selected_channel_name)] if selected_channel_name else None
            if selected_channel:
                st.session_state.selected_channel_id = selected_channel['stream_id']
        else:
            st.warning("لا توجد قنوات مطابقة")
    else:
        st.info("اختر خادماً أولاً لظهور القنوات")

with col2:
    st.subheader("📺 مشغل الفيديو")
    quality = st.selectbox("جودة البث", ["TS (أصلي)", "M3U8 (HLS)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
    use_external = st.checkbox("تشغيل في نافذة خارجية (للمتصفح فقط - سيفتح الرابط)", value=False)
    
    if st.button("▶️ تشغيل القناة", type="primary") and st.session_state.get("selected_channel_id") and st.session_state.current_server:
        server = st.session_state.current_server
        ext = "m3u8" if "M3U8" in quality else "ts"
        url = f"{server['host']}/live/{server['user']}/{server['pass']}/{st.session_state.selected_channel_id}.{ext}"
        # إضافة bitrate للجودة المنخفضة
        bitrate_map = {"720p": "720", "480p": "480", "360p": "360", "240p": "240", "144p": "144", "96p": "96"}
        if quality in bitrate_map:
            url += f"?bitrate={bitrate_map[quality]}"
        
        if use_external:
            st.markdown(f"رابط البث (افتحه في أي مشغل):  \n`{url}`")
            st.info("يمكنك نسخ الرابط وتشغيله في VLC أو أي مشغل خارجي")
        else:
            # مشغل HTML5 مع دعم HLS
            if ext == "m3u8":
                # استخدام hls.js
                html_code = f"""
                <video id="video" controls autoplay width="100%" height="auto"></video>
                <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                <script>
                    var video = document.getElementById('video');
                    if (Hls.isSupported()) {{
                        var hls = new Hls();
                        hls.loadSource('{url}');
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                            video.play();
                        }});
                    }}
                    else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                        video.src = '{url}';
                        video.addEventListener('loadedmetadata', function() {{
                            video.play();
                        }});
                    }}
                </script>
                """
            else:
                html_code = f"""
                <video controls autoplay width="100%" height="auto">
                    <source src="{url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                """
            st.components.v1.html(html_code, height=400)
        add_log(f"تشغيل: {url[:80]}...")
    elif not st.session_state.get("selected_channel_id"):
        st.warning("اختر قناة أولاً")
    elif not st.session_state.current_server:
        st.warning("اختر خادماً أولاً")

# زر بدء الصيد
if start_btn and not st.session_state.searching:
    if not tokens_input.strip():
        st.error("يرجى إدخال GitHub Tokens على الأقل سطر واحد")
    else:
        st.session_state.searching = True
        add_log("بدء البحث عن الحسابات...")
        tokens = [t.strip() for t in tokens_input.splitlines() if t.strip()]
        
        def hunt_process():
            new_accounts = []
            unique = set()
            dorks = [
                '"player_api.php?username="', '"get.php?username="', 'filename:m3u "xtream"',
                '"/player_api.php" password', 'xtreamcodes "username" "password"',
                'inurl:player_api.php?username=', 'inurl:get.php?username='
            ]
            token_idx = 0
            dork_idx = 0
            page = 1
            proxy = proxy_input if proxy_input else None
            executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
            while st.session_state.searching:
                token = tokens[token_idx % len(tokens)]
                token_idx += 1
                dork = dorks[dork_idx % len(dorks)]
                dork_idx += 1
                for p in range(1, PAGES_PER_DORK+1):
                    if not st.session_state.searching:
                        break
                    add_log(f"بحث: {dork[:20]} | صفحة {p} | توكن {token[:8]}...")
                    items = search_github(dork, token, p, proxy)
                    if not items:
                        break
                    futures = []
                    for item in items:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        futures.append(executor.submit(process_raw, raw_url, proxy))
                    for future in as_completed(futures):
                        if not st.session_state.searching:
                            break
                        accounts = future.result()
                        for acc in accounts:
                            uid = f"{acc['host']}{acc['user']}{acc['pass']}"
                            if uid not in unique:
                                unique.add(uid)
                                # فحص الحساب
                                checked = check_account(acc['host'], acc['user'], acc['pass'], proxy)
                                if checked:
                                    new_accounts.append(checked)
                                    # تحديث واجهة المستخدم عبر Streamlit (نستخدم session_state بشكل مباشر مع rerun)
                                    st.session_state.accounts = new_accounts
                                    # تحديث قائمة الخوادم
                                    server_exists = any(s['host'] == checked['host'] for s in st.session_state.servers)
                                    if not server_exists:
                                        st.session_state.servers.append(checked)
                                    add_log(f"✅ حساب شغال: {checked['host']}")
                    time.sleep(1)
                time.sleep(3)
            executor.shutdown(wait=False)
        
        def process_raw(raw_url, proxy):
            try:
                proxies = {"http": proxy, "https": proxy} if proxy else None
                resp = requests.get(raw_url, timeout=REQUEST_TIMEOUT, proxies=proxies)
                if resp.status_code != 200:
                    return []
                content = resp.text
                matches = extract_xtream_accounts(content)
                return [{"host": h, "user": u, "pass": p} for h,u,p in matches]
            except:
                return []
        
        thread = threading.Thread(target=hunt_process, daemon=True)
        thread.start()

if stop_btn:
    st.session_state.searching = False
    add_log("تم إيقاف البحث.")

# تحديث عدد الحسابات والخوادم
accounts_count.metric("عدد الحسابات الشغالة", len(st.session_state.accounts))
servers_count.metric("عدد الخوادم النشطة", len(st.session_state.servers))

# عرض السجل
with log_container:
    for msg in st.session_state.log[:30]:
        st.text(msg)

# عرض قائمة الخوادم والقنوات محدثة
if st.session_state.servers:
    server_list.write("\n".join([f"• {s['host']} | {s['user']}" for s in st.session_state.servers]))

# تشغيل التحديث التلقائي (لإعادة تحميل الواجهة عند اكتشاف حسابات جديدة)
if st.session_state.searching:
    st.rerun(interval=3000)  # كل 3 ثواني
else:
    # لمنع التكرار المستمر
    st.markdown("---")
    st.caption("يمكنك بدء البحث بالضغط على زر 'بدء الصيد'")
