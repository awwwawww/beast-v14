import streamlit as st
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- إعداد كلمة المرور ---
PASSWORD = "BEAST_2025"  # يمكنك تغيير كلمة المرور من هنا

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct:
        return True

    st.title("🔐 الدخول محمي")
    pwd = st.text_input("أدخل كلمة المرور للاستمرار:", type="password")
    if st.button("تسجيل الدخول"):
        if pwd == PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ كلمة المرور غير صحيحة")
    return False

if not check_password():
    st.stop()

# --- باقي الكود الأساسي بعد تعديل الـ Regex لتحسين النتائج ---

st.set_page_config(page_title="IPTV Ultra Beast V14", layout="wide")

# (ضع هنا دوال البحث والتحقق من الكود السابق مع التعديل التالي في Regex)

# تعديل صيغة البحث لتكون أقوى:
# matches = re.findall(r"(https?://[^\s'\"<>]+:\d+)/(?:(?:get\.php|player_api\.php)\?username=([^\s'\"&]+)&password=([^\s'\"&]+))", content)
