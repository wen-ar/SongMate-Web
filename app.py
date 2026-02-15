import streamlit as st
import pandas as pd

# 網頁配置
st.set_page_config(page_title="SongMate", page_icon="🎵")

# 簡單的 CSS 讓它更有 WinUI 的感覺
st.markdown("""
    <style>
    .main { background-color: #f5f5f7; }
    .stButton>button { border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎧 SongMate 點歌助手 (Render 測試版)")

tab1, tab2 = st.tabs(["📁 更新歌庫", "🎲 抽歌工具"])

with tab1:
    st.subheader("上傳資料")
    file = st.file_uploader("選取點歌清單 (Excel)", type=['xlsx'])
    if file:
        df = pd.read_excel(file)
        st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("開始隨機抽歌")
    count = st.slider("抽幾首？", 1, 10, 3)
    if st.button("點我抽歌"):
        st.balloons()
        st.success(f"成功抽出了 {count} 首歌！")
