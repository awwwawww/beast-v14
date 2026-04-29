# === مكتبة وسائل التواصل الاجتماعي والتطبيقات السحابية ===
import sys
sys.modules['streamlit'] = __import__('fake_streamlit')
print("تم تحميل بيئة Streamlit بنجاح.")

import streamlit as st
import requests
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# === إعدادات الواجهة ===
st.set_page_config(page_title="BEAST V23 - MASSIVE & DIVERSE", layout="wide")

# === نظام الدخول ===
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - MASSIVE SCAN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# === التنسيقات والألوان ===
st.markdown("""
<style>
    .stApp { background-color: #000; }
    .scan-log { color: #00d4ff; font-family: monospace; font-size: 13px; margin: 0; padding: 2px; }
    .active-hit {
        background: #0d1117; border: 1px solid #00ff41;
        padding: 10px; border-radius: 5px; margin-bottom: 5px;
    }
    .text-green { color: #00ff41; font-weight: bold; }
    .text-yellow { color: #fbbf24; }
    .text-white { color: #fff; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# === الشريط الجانبي للإعدادات ===
with st.sidebar:
    st.title("⚡ BEAST V23 - INFINITE SCAN")
    token = st.text_input("GitHub Token (اختياري للجلب التلقائي):", type="password")
    max_workers = st.slider("عدد الخيوط المتوازية 🚀", 5, 100, 30)
    start = st.button("🚀 ابدأ الهجوم الضخم")
    st.info("سيتم جلب آلاف السيرفرات من عدة مصادر ضخمة")
    st.warning("ملاحظة: هذه العملية قد تستغرق عدة دقائق لجلب الآلاف من السيرفرات")

st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

st.subheader("🏆 النتائج الشغالة (Active Hits)")
hits_area = st.container()

# === دوال لجلب مصادر متعددة ===
def fetch_servers_from_github_repos():
    """جلب سيرفرات من مستودعات GitHub الضخمة"""
    servers = []
    github_urls = [
        "https://raw.githubusercontent.com/IPTV-RU/IPTV/main/playlist.m3u",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.csv",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/Countries/master/World.m3u",
        "https://raw.githubusercontent.com/akshatmittal/m3u8-proxy/master/proxy.html",
        "https://raw.githubusercontent.com/SilentCipher/iptv_links/master/iptv.m3u",
        "https://raw.githubusercontent.com/MrBazou/IPTV/master/Playlist.m3u",
        "https://raw.githubusercontent.com/azrite/IPTV/master/playlist.m3u",
        "https://raw.githubusercontent.com/iptvtools/iptv/master/iptv.m3u",
    ]
    
    radar_area.info("🌐 جاري جلب السيرفرات من مستودعات GitHub الضخمة...")
    
    for url in github_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                # استخراج روابط السيرفرات من ملفات m3u
                links = re.findall(r'(?:https?://)([a-zA-Z0-9\.-]+(?::\d+)?)/[^\s"\']*', content)
                servers.extend(links)
            else:
                radar_area.warning(f"⚠️ فشل جلب {url}")
        except Exception as e:
            continue
    
    return list(set(servers))  # إزالة التكرارات

def extract_servers_from_m3u(content):
    """استخراج السيرفرات من محتوى ملف m3u"""
    servers = []
    # استخراج روابط السيرفرات من ملفات m3u
    links = re.findall(r'(?:https?://)([a-zA-Z0-9\.-]+(?::\d+)?)/[^\s"\']*', content)
    servers.extend(links)
    return servers

def fetch_servers_from_public_apis():
    """جلب سيرفرات من APIs وملفات JSON عامة"""
    servers = []
    radar_area.info("📡 جاري جلب السيرفرات من APIs وملفات JSON...")
    
    # جلب من iptv-org API
    try:
        response = requests.get("https://iptv-org.github.io/iptv/channels.json", timeout=10)
        if response.status_code == 200:
            channels = response.json()
            for channel in channels:
                url = channel.get('url', '')
                if url:
                    server_match = re.search(r'https?://([^/]+)', url)
                    if server_match:
                        servers.append(server_match.group(1))
    except:
        pass
    
    # جلب من قوائم القنوات المدعومة
    try:
        response = requests.get("https://iptv-org.github.io/iptv/index.m3u", timeout=10)
        if response.status_code == 200:
            servers.extend(extract_servers_from_m3u(response.text))
    except:
        pass
    
    # قوائم أخرى
    m3u_urls = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/Countries/master/USA.m3u"
    ]
    
    for url in m3u_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                servers.extend(extract_servers_from_m3u(response.text))
        except:
            continue
    
    return list(set(servers))

def search_github_dorks(token):
    """البحث باستخدام الدروكس في GitHub API"""
    if not token:
        return []
    
    all_results = []
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # 1. قائمة الدروكس الموسعة (أكثر من 40 دروك)
    dorks = [
        'extension:txt "http://" "username" "password" iptv',
        'extension:txt "https://" "user" "pass" "server"',
        'extension:json "server" "port" "username" "password"',
        'extension:cfg "xtream" "user" "pass"',
        'extension:conf "enigma2" "http" "user"',
        'extension:xml "streaming" "auth"',
        'extension:log "login" "password" iptv',
        'extension:sql username password iptv',
        'extension:php "player_api.php"',
        'extension:txt "get.php?username="',
        'extension:txt "cpanel" "host" "user" "pass"',
        'extension:ini "portal" "username"',
        'extension:txt "8080" "username" "password"',
        'extension:txt "25461" "username" "password"',
        'extension:php "panel_api.php?username="',
        '"player_api.php?username=" extension:php',
        '"xtream" "port" "user" "pass" extension:txt',
        '"stream" "server" "login" extension:conf',
        '"iptv" "username" "password" extension:json',
        '"m3u" "username" "password" extension:txt',
        '"http://" "8080" "iptv" extension:txt',
        '"portal" "username" "password" extension:php',
        '"server" "port" "iptv" extension:txt',
        '"url" "port" "iptv" filetype:json',
        '"host" "port" "user" "pass" filetype:txt',
        '"api" "stream" "port" filetype:php',
        '"live" "stream" "http" filetype:m3u',
        '"xtream" "api" "key" filetype:json',
        '"playlist" "m3u" "iptv" filetype:txt',
        '"stalker" "portal" "mac" filetype:txt',
        '"streaming" "server" "login" filetype:conf',
        '"iptv" "login" "password" filetype:log',
        '"vod" "server" "port" filetype:txt',
        '"xtream" "panel" "admin" filetype:php',
        '"iptv" "api" "stream" filetype:json',
        '"live" "tv" "stream" "http" filetype:m3u8',
        '"iptv" "server" "port" filetype:cfg',
        '"stream" "live" "port" filetype:xml',
        '"iptv" "auth" "login" filetype:conf',
        '"xtream" "client" "api" filetype:php',
        '"iptv" "reseller" "panel" filetype:txt',
        '"stb" "emulator" "portal" filetype:cfg',
        '"iptv" "subscription" "url" filetype:json',
        '"xtream" "stream" "proxy" filetype:go',
        '"iptv" "m3u" "playlist" "url" filetype:txt',
        '"stream" "proxy" "iptv" filetype:js',
        '"xtream" "ui" "admin" filetype:php',
        '"iptv" "portal" "address" filetype:txt',
        '"live" "streaming" "server" filetype:cfg',
        '"iptv" "epg" "xmltv" filetype:xml',
        '"stream" "source" "iptv" filetype:json',
        '"iptv" "panel" "admin" filetype:php',
    ]
    
    radar_area.info(f"🔍 بدء البحث باستخدام {len(dorks)} دروك في GitHub...")
    
    for dork_index, dork in enumerate(dorks):
        radar_area.info(f"🔎 Dork {dork_index+1}/{len(dorks)}: {dork[:70]}...")
        
        for page in range(1, 4):  # 3 صفحات لكل دروك
            try:
                if page > 1:
                    time.sleep(0.5)
                
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(search_url, headers=headers)
                
                if res.status_code == 403 and 'rate limit' in res.text.lower():
                    reset_time = int(res.headers.get('x-ratelimit-reset', time.time() + 60))
                    wait_seconds = reset_time - time.time() + 5
                    if wait_seconds > 60:
                        radar_area.warning(f"⏳ انتظار {int(wait_seconds)} ثانية بسبب حد معدل الطلبات...")
                        time.sleep(wait_seconds)
                    continue
                
                data = res.json()
                if "items" not in data:
                    continue
                
                items = data.get("items", [])
                if not items:
                    break
                
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # استخراج سيرفرات Xtream
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)", content)
                        all_results.extend(matches)
                    except:
                        continue
                        
            except Exception as e:
                continue
        
        # تأخير بين الدروكس لتجنب الوصول السريع للحد
        time.sleep(2)
    
    return all_results

# === الوظيفة الرئيسية للجلب الضخم ===
if start:
    all_servers = []
    
    # 1. جلب من مستودعات GitHub الضخمة
    radar_area.info("📦 جلب آلاف السيرفرات من مستودعات GitHub...")
    repo_servers = fetch_servers_from_github_repos()
    if repo_servers:
        all_servers.extend(repo_servers)
        radar_area.info(f"✅ تم جلب {len(repo_servers)} سيرفر من مستودعات GitHub")
    
    # 2. جلب من واجهات برمجة التطبيقات العامة
    api_servers = fetch_servers_from_public_apis()
    if api_servers:
        all_servers.extend(api_servers)
        radar_area.info(f"✅ تم جلب {len(api_servers)} سيرفر من واجهات برمجة التطبيقات العامة")
    
    # 3. جلب من GitHub عبر الدروكس (إذا توفر التوكن)
    if token:
        dork_servers = search_github_dorks(token)
        if dork_servers:
            all_servers.extend(dork_servers)
            radar_area.info(f"✅ تم جلب {len(dork_servers)} سيرفر من خلال الدروكس")
    
    # إزالة التكرارات
    unique_servers = list(set(all_servers))
    radar_area.success(f"🎯 تم جمع {len(unique_servers)} سيرفر فريد. بدء اختبارها الآن...")
    
    # عرض أول 100 سيرفر كمثال
    st.subheader("🗂️ السيرفرات التي تم جمعها")
    st.dataframe(pd.DataFrame(unique_servers[:100], columns=["السيرفر"]), use_container_width=True)
    
    # اختبار السيرفرات
    status_area = st.empty()
    found_count = 0
    hits_list = []
    
    def test_server(server):
        """اختبار إذا كان السيرفر يدعم IPTV"""
        try:
            # اختبار الطرق المختلفة
            test_urls = [
                f"http://{server}/player_api.php",
                f"http://{server}/api/get.php",
                f"http://{server}/get.php",
                f"http://{server}/panel_api.php",
            ]
            for test_url in test_urls:
                try:
                    r = requests.get(test_url, timeout=2)
                    if r.status_code == 200:
                        return server, True
                except:
                    continue
            return server, False
        except:
            return server, False
    
    status_area.info("🔄 جاري اختبار السيرفرات... هذا قد يستغرق بضع دقائق")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_server, server): server for server in unique_servers}
        for future in as_completed(futures):
            server, active = future.result()
            if active:
                found_count += 1
                with hits_area:
                    st.markdown(f"""
                    <div class="active-hit">
                        <span class="text-green">✅ Active Server #{found_count}</span><br>
                        <span class="text-white">Server: {server}</span><br>
                        <span class="text-yellow">🔴 Link: http://{server}</span>
                    </div>
                    """, unsafe_allow_html=True)
                hits_list.append(server)
            status_area.info(f"📊 نسبة اكتمال الاختبار: {len(unique_servers)-sum(1 for _ in futures)}/{len(unique_servers)}")
    
    st.success(f"✅ اكتملت العملية! تم العثور على {found_count} سيرفر شغال من بين {len(unique_servers)} سيرفر تم جمعهم.")
    
    if hits_list:
        st.download_button("📥 تحميل السيرفرات الشغالة (TXT)", "\n".join([f"http://{s}" for s in hits_list]), "active_servers.txt")

else:
    st.info("👈 قم بإدخال GitHub Token (اختياري) ثم اضغط على زر '🚀 ابدأ الهجوم الضخم' لبدء عملية الجلب.")
