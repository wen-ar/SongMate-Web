import streamlit as st
import pandas as pd
import datetime
import numpy as np
import os

# --- 1. 網頁基礎配置 ---
st.set_page_config(page_title="SongMate Web", page_icon="🎧", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { border-radius: 8px; background-color: #0078d4; color: white; border: none; }
    .stButton>button:hover { background-color: #005a9e; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 檔案持久化邏輯 ---
DB_FILE = "song_library.xlsx"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_excel(DB_FILE)
    return None

def save_data(df):
    df.to_excel(DB_FILE, index=False)

# 初始化資料
if 'library_df' not in st.session_state:
    st.session_state.library_df = load_data()

# --- 3. 側邊導覽 ---
with st.sidebar:
    st.title("🎧 SongMate")
    menu = st.radio("功能選單", ["📁 更新歌庫", "🎲 抽歌工具", "🔍 查詢與修改"])
    if st.session_state.library_df is not None:
        st.success(f"歌庫內共有 {len(st.session_state.library_df)} 筆")

# --- 4. 功能：更新歌庫 ---
if menu == "📁 更新歌庫":
    st.header("更新歌庫")
    uploaded_file = st.file_uploader("請選擇 Excel", type=['xlsx'])
    if uploaded_file:
        try:
            df_raw = pd.read_excel(uploaded_file)
            target_cols = {"姓名": "requester", "性別": "gender", "歌名": "title", "歌曲連結": "link"}
            if all(col in df_raw.columns for col in target_cols.keys()):
                new_data = df_raw[list(target_cols.keys())].copy()
                new_data.rename(columns=target_cols, inplace=True)
                new_data['play_count'] = 0
                new_data['last_played'] = "從未播放"
                st.dataframe(new_data, use_container_width=True)
                if st.button("確認匯入並存入伺服器"):
                    save_data(new_data)
                    st.session_state.library_df = new_data
                    st.success("✅ 匯入成功！")
        except Exception as e:
            st.error(f"錯誤：{e}")

# --- 5. 功能：抽歌工具 (權重算法核心) ---
elif menu == "🎲 抽歌工具":
    st.header("抽歌工具")
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先上傳歌庫")
    else:
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        gender_today = "男" if tomorrow.day % 2 == 0 else "女"
        st.info(f"📅 明日 ({tomorrow.strftime('%m/%d')}) 是 **{gender_today}日**")
        num_to_draw = st.number_input("預計抽出數量", 1, 20, 3)

        if st.button("🔥 開始加權抽歌", type="primary"):
            df = st.session_state.library_df.copy()
            pool = df[df['gender'] == gender_today].copy()
            if pool.empty:
                st.error(f"❌ 沒有 {gender_today} 性的歌曲")
            else:
                # 權重算法：播放次數愈多，中獎率愈低
                pool['weight'] = 1 / (pool['play_count'] + 1)
                selected = pool.sample(n=min(len(pool), int(num_to_draw)), weights='weight')
                
                # 自動增加這幾首歌的播放次數
                for idx in selected.index:
                    st.session_state.library_df.at[idx, 'play_count'] += 1
                    st.session_state.library_df.at[idx, 'last_played'] = datetime.datetime.now().strftime("%Y-%m-%d")
                
                # 存檔以保存次數更新
                save_data(st.session_state.library_df)

                st.write("### 🎶 抽籤結果")
                for i, row in enumerate(selected.itertuples(), 1):
                    st.markdown(f"**{i}. {row.title}** — {row.requester} (已播放 {row.play_count} 次)")
                    if pd.notna(row.link): st.caption(f"🔗 [點我播放]({row.link})")
                
                st.success("✅ 抽歌完成，播放次數已自動 +1")

# --- 6. 功能：查詢與修改 (新增修改次數功能) ---
elif menu == "🔍 查詢與修改":
    st.header("查詢與手動修改")
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先上傳歌庫")
    else:
        search_name = st.text_input("搜尋姓名或歌名：")
        df = st.session_state.library_df
        
        if search_name:
            results = df[(df['requester'].str.contains(search_name, na=False)) | 
                        (df['title'].str.contains(search_name, na=False))]
            
            if not results.empty:
                st.write("請選擇要修改的歌曲：")
                for idx, row in results.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"🎵 {row['title']} ({row['requester']})")
                    # 使用 number_input 讓使用者修改次數
                    new_count = col2.number_input(f"次數", min_value=0, value=int(row['play_count']), key=f"n_{idx}")
                    if col3.button("更新", key=f"b_{idx}"):
                        st.session_state.library_df.at[idx, 'play_count'] = new_count
                        save_data(st.session_state.library_df)
                        st.success(f"已更新《{row['title']}》為 {new_count} 次")
                        st.rerun()
                st.divider()
                st.dataframe(results[['requester', 'gender', 'title', 'play_count']], use_container_width=True)
            else:
                st.write("找不到相關記錄")
