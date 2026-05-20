import streamlit as st
import requests
import re
import time
import hashlib
from datetime import datetime

# إعدادات
REQUEST_TIMEOUT = 4
PAGES_PER_STEP = 2  # عدد الصفحات لكل خطوة (حتى لا يتجمد التطبيق)

st.set_page_config(page_title="IPTV Web Hunter", layout="wide", page_icon="📺")
st.title("🔥 IPTV WEB HUNTER - صيد حسابات + مشغل ويب")

# تهيئة session_state
if "step" not in st.session_state:
    st.session_state.step = 0          # خطوة البحث الحالية
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
if "tokens" not in st.session_state:
    st.session_state.tokens = []
if "proxy" not in st.session_state:
    st.session_state.proxy = ""
if "unique_set" not in st.session_state:
    st.session_state.unique_set = set()
if "dork_list" not in st.session_state:
    st.session_state.dork_list = [
        '"player_api.php?username="', '"get.php?username="', 'filename:m3u "xtream"',
        '"/player_api.php" password', 'xtreamcodes "username" "password"',
        'inurl:player_api.php?username=', 'inurl:get.php?username='
    ]
if "current_dork_idx" not in st.session_state:
    st.session_state.current_dork_idx = 0
if "current_token_idx" not in st.session_state:
    st.session_state.current_token_idx = 0
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# دوال مساعدة
def extract_xtream_accounts(content):
    pattern = r'(https?://[a-zA-Z0-9.-]+:\d+)/(?:player_api|get)\.php\?(?:username|user)=([^&\s]+)&(?:password|pass)=([^&\s]+)'
    return re.findall(pattern, content, re.IGNORECASE)

def check_account(host, user, pw, proxy):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(api, timeout=REQUEST_TIMEOUT, proxies=proxies)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("user_info", {}).get("status") == "Active":
            exp = data["user_info"].get('exp_date')
            exp_str = datetime.fromtimestamp(int(exp)).strftime('%Y-%m-%d') if exp else "دائم"
            return {"host": host, "user": user, "pass": pw, "exp": exp_str}
    except:
        return None
    return None

def search_github(dork, token, page, proxy):
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
        return extract_xtream_accounts(resp.text)
    except:
        return []

def load_channels(server, proxy):
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

# ========== الواجهة الجانبية ==========
with st.sidebar:
    st.header("⚙️ الإعدادات")
    tokens_input = st.text_area("GitHub Tokens (سطر لكل توكن)", placeholder="ghp_token1\nghp_token2")
    proxy_input = st.text_input("🚀 بروكسي (اختياري)", placeholder="http://user:pass@ip:port")
    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("🌪️ بدء الصيد", type="primary", use_container_width=True):
        if not tokens_input.strip():
            st.error("أدخل GitHub Tokens أولاً")
        else:
            st.session_state.searching = True
            st.session_state.step = 0
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

    st.metric("💎 الحسابات الشغالة", len(st.session_state.accounts))
    st.metric("🗄️ الخوادم النشطة", len(st.session_state.servers))
    st.markdown("---")
    st.subheader("📋 السجل")
    log_container = st.container(height=250)

# ========== تنفيذ البحث خطوة بخطوة (Polling) ==========
if st.session_state.searching:
    # عرض شريط تقدم متحرك
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    # ننفذ خطوة بحث واحدة فقط في كل مرة (حتى لا يتجمد)
    # إذا انتهت الخطوات نعيد ضبط المؤشرات لبدء دورة جديدة
    total_steps = len(st.session_state.tokens) * len(st.session_state.dork_list) * 100  # تقديري
    
    # متغيرات مساعدة
    tokens = st.session_state.tokens
    dorks = st.session_state.dork_list
    dork_idx = st.session_state.current_dork_idx
    token_idx = st.session_state.current_token_idx
    page = st.session_state.current_page
    proxy = st.session_state.proxy

    # نحدد متى نتوقف مؤقتاً
    if token_idx >= len(tokens):
        # بدأنا دورة جديدة
        token_idx = 0
        dork_idx += 1
        if dork_idx >= len(dorks):
            dork_idx = 0
            st.session_state.log.append("🔄 بدأ دورة بحث جديدة")
        st.session_state.current_token_idx = token_idx
        st.session_state.current_dork_idx = dork_idx
        st.session_state.current_page = 1
        # نعيد التشغيل
        st.rerun()
    
    token = tokens[token_idx % len(tokens)]
    dork = dorks[dork_idx % len(dorks)]
    
    # تحديث شريط التقدم
    progress_bar.progress(min(1.0, (token_idx + dork_idx * 0.1) / (len(tokens) * len(dorks))))
    progress_text.text(f"🔍 البحث: {dork[:25]} | صفحة {page} | توكن {token[:6]}...")
    
    # جلب صفحة واحدة
    items = search_github(dork, token, page, proxy)
    if items:
        progress_text.text(f"📄 معالجة {len(items)} ملف...")
        # معالجة كل ملف في هذه الصفحة
        for item in items:
            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            accounts_raw = process_raw(raw_url, proxy)
            for host, user, pw in accounts_raw:
                uid = hashlib.md5(f"{host}{user}{pw}".encode()).hexdigest()
                if uid in st.session_state.unique_set:
                    continue
                st.session_state.unique_set.add(uid)
                # فحص الحساب
                checked = check_account(host, user, pw, proxy)
                if checked:
                    st.session_state.accounts.append(checked)
                    if not any(s['host'] == checked['host'] for s in st.session_state.servers):
                        st.session_state.servers.append(checked)
                    st.session_state.log.insert(0, f"✅ شغال: {checked['host']} | {checked['user']}")
                    if len(st.session_state.log) > 50:
                        st.session_state.log = st.session_state.log[:50]
        # زيادة رقم الصفحة
        st.session_state.current_page += 1
        # إذا تجاوزنا الحد، ننتقل إلى التوكن التالي
        if st.session_state.current_page > 30:
            st.session_state.current_page = 1
            st.session_state.current_token_idx += 1
    else:
        # لا توجد نتائج في هذه الصفحة → ننتقل للتوكن التالي
        st.session_state.current_token_idx += 1
        st.session_state.current_page = 1
    
    # نضيف رسالة توضح أننا مازلنا نبحث
    st.session_state.log.insert(0, f"⏳ جارٍ البحث... (تم فحص {len(st.session_state.unique_set)} رابط فريد)")
    if len(st.session_state.log) > 50:
        st.session_state.log = st.session_state.log[:50]
    
    # نعيد تشغيل الصفحة بعد 0.5 ثانية لمواصلة البحث (تأثير الحركة)
    time.sleep(0.5)
    st.rerun()
else:
    # إذا لم يكن البحث نشطاً، نعرض رسالة
    st.info("اضغط 'بدء الصيد' لبدء البحث عن حسابات IPTV")

# ========== عرض السجل ==========
with log_container:
    for msg in st.session_state.log[:30]:
        st.text(msg)

# ========== الأعمدة الرئيسية ==========
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("🗄️ الخوادم النشطة")
    if st.session_state.servers:
        server_names = [f"{s['host']} | {s['user']}" for s in st.session_state.servers]
        selected_name = st.selectbox("اختر خادماً:", server_names)
        if selected_name:
            idx = server_names.index(selected_name)
            selected = st.session_state.servers[idx]
            if st.session_state.current_server != selected:
                st.session_state.current_server = selected
                key = f"{selected['host']}|{selected['user']}"
                if key in st.session_state.channels_cache:
                    st.session_state.current_channels = st.session_state.channels_cache[key]
                else:
                    with st.spinner("جاري تحميل القنوات..."):
                        channels = load_channels(selected, st.session_state.proxy)
                        st.session_state.channels_cache[key] = channels
                        st.session_state.current_channels = channels
                st.rerun()
    else:
        st.info("لا توجد خوادم بعد. انتظر نتائج البحث.")

    st.subheader("📡 قنوات السيرفر")
    if st.session_state.current_channels:
        search_ch = st.text_input("🔍 بحث في القنوات")
        filtered = [c for c in st.session_state.current_channels if search_ch.lower() in c['name'].lower()] if search_ch else st.session_state.current_channels
        ch_names = [f"{c['name']} (ID:{c['stream_id']})" for c in filtered]
        if ch_names:
            selected_ch_name = st.selectbox("اختر قناة:", ch_names)
            if selected_ch_name:
                ch_idx = ch_names.index(selected_ch_name)
                st.session_state.selected_channel_id = filtered[ch_idx]['stream_id']
    else:
        st.info("اختر خادماً لتحميل القنوات")

with col_right:
    st.subheader("📺 مشغل الفيديو")
    quality = st.selectbox("الجودة", ["M3U8 (HLS)", "TS (أصلي)", "720p", "480p", "360p", "240p", "144p", "96p"], index=0)
    use_external = st.checkbox("تشغيل خارجي (رابط فقط)")
    
    if st.button("▶️ تشغيل") and st.session_state.get("selected_channel_id") and st.session_state.current_server:
        server = st.session_state.current_server
        ext = "m3u8" if "M3U8" in quality else "ts"
        url = f"{server['host']}/live/{server['user']}/{server['pass']}/{st.session_state.selected_channel_id}.{ext}"
        bitrate = {"720p":"720","480p":"480","360p":"360","240p":"240","144p":"144","96p":"96"}
        if quality in bitrate:
            url += f"?bitrate={bitrate[quality]}"
        if use_external:
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
                    }}
                </script>
                """, height=400)
            else:
                st.video(url)
    elif not st.session_state.get("selected_channel_id"):
        st.warning("اختر قناة أولاً")
