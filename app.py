import streamlit as st
import pandas as pd
import datetime
import numpy as np
import io

# --- 頁面配置 ---
st.set_page_config(page_title="SongMate Web", page_icon="🎧", layout="centered")

# 自定義 CSS 讓介面更像 WinUI
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { border-radius: 8px; height: 3em; background-color: #0078d4; color: white; border: none; }
    .stButton>button:hover { background-color: #005a9e; color: white; }
    div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎧 SongMate 點歌助手")

# 使用 Session State 模擬資料庫儲存 (注意：Render 重啟後會重置)
if 'library_df' not in st.session_state:
    st.session_state.library_df = None

tabs = st.tabs(["📁 更新歌庫", "🎲 抽歌工具"])

# --- Tab 1: 更新歌庫 ---
with tabs[0]:
    st.subheader("匯入點歌單")
    uploaded_file = st.file_uploader("選擇 Excel 檔案 (需包含: 姓名, 性別, 歌名)", type=['xlsx'])
    
    if uploaded_file:
        try:
            # 讀取上傳的檔案
            new_data = pd.read_excel(uploaded_file)
            # 統一欄位名稱 (對應你原本的邏輯)
            # 假設原始 Excel 欄位為: 姓名, 性別, 歌名
            new_data.columns = ['requester', 'gender', 'title'] 
            
            st.write("📋 預覽上傳內容：")
            st.dataframe(new_data, use_container_width=True)
            
            if st.button("確認更新至歌庫"):
                # 初始化播放次數與日期
                new_data['play_count'] = 0
                new_data['last_played'] = "從未播放"
                st.session_state.library_df = new_data
                st.success("✅ 歌庫已更新！(暫存於記憶體中)")
        except Exception as e:
            st.error(f"讀取失敗：{e}")

# --- Tab 2: 抽歌工具 ---
with tabs[1]:
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先前往「更新歌庫」上傳資料。")
    else:
        st.subheader("開始隨機抽歌")
        
        # 1. 判斷性別邏輯 (複用原本 draw_widget.py)
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        # 假設: 偶數日抽男, 奇數日抽女
        gender_today = "男" if tomorrow.day % 2 == 0 else "女"
        
        st.info(f"📅 明日日期：{tomorrow.strftime('%Y-%m-%d')} ({gender_today}日)")
        
        num_to_draw = st.number_input("預計抽出數量", min_value=1, max_value=20, value=3)
        
        if st.button("🔥 執行抽歌", type="primary"):
            df = st.session_state.library_df.copy()
            
            # 2. 篩選性別
            pool = df[df['gender'] == gender_today].copy()
            
            if pool.empty:
                st.error(f"❌ 歌庫中沒有 {gender_today} 性的歌曲！")
            else:
                # 3. 權重算法: 1 / (播放次數 + 1)
                pool['weight'] = 1 / (pool['play_count'] + 1)
                
                # 執行加權隨機抽樣
                sample_size = min(len(pool), int(num_to_draw))
                selected = pool.sample(n=sample_size, weights='weight')
                
                st.write("### 🎶 今日播放清單")
                for i, row in enumerate(selected.itertuples(), 1):
                    # 顯示結果
                    st.markdown(f"**{i}. {row.title}** — {row.requester}")
                
                # 4. 產生下載連結 (替代原本的自動存檔)
                output_text = f"🎶 播放清單（{gender_today}日）\n"
                for i, row in enumerate(selected.itertuples(), 1):
                    output_text += f"{i}. {row.title} — {row.requester}\n"
                
                st.download_button(
                    label="💾 下載播放清單 (.txt)",
                    data=output_text,
                    file_name=f"playlist_{tomorrow.strftime('%m%d')}.txt",
                    mime="text/plain"
                )
                st.balloons()
