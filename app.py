import streamlit as st
import pandas as pd
import datetime
import numpy as np
import os

# --- 1. 網頁基礎配置 ---
st.set_page_config(page_title="SongMate Web", page_icon="🎧", layout="wide")

# 自定義 CSS (黑白灰色調)
st.markdown("""
    <style>
    /* 整體背景與字體 */
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    
    /* 側邊欄樣式 */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e0e0e0;
    }
    
    /* 按鈕樣式：黑色底、白色字 */
    .stButton>button { 
        border-radius: 4px; 
        background-color: #1a1a1a; 
        color: #ffffff; 
        width: 100%;
        border: 1px solid #1a1a1a;
        transition: 0.2s;
        font-weight: 500;
    }
    .stButton>button:hover { 
        background-color: #404040; 
        border-color: #404040;
        color: #ffffff;
    }
    .stButton>button:active {
        background-color: #000000;
        color: #ffffff;
    }

    /* 輸入框與選擇框樣式 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 4px;
        border: 1px solid #cccccc;
    }

    /* 卡片感容器 */
    .song-item {
        padding: 15px;
        border-bottom: 1px solid #eeeeee;
        margin-bottom: 5px;
    }

    /* 連結顏色：深灰色 */
    a { color: #555555 !important; text-decoration: underline; }
    
    /* 下載按鈕樣式（特殊處理） */
    div[data-testid="stDownloadButton"] > button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #1a1a1a !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #f0f0f0 !important;
    }
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

if 'library_df' not in st.session_state:
    st.session_state.library_df = load_data()

# --- 3. 側邊導覽 ---
with st.sidebar:
    st.title("SONGMATE")
    st.caption("Minimalist Music Tool")
    menu = st.radio("MENU", ["📁 更新歌庫", "🎲 抽歌工具", "🔍 查詢與修改"])
    st.divider()
    if st.session_state.library_df is not None:
        st.write(f"總計資料: {len(st.session_state.library_df)}")

# --- 4. 功能：更新歌庫 ---
if menu == "📁 更新歌庫":
    st.header("Upload Library")
    uploaded_file = st.file_uploader("Select Excel File", type=['xlsx'])
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
                if st.button("CONFIRM & SAVE"):
                    save_data(new_data)
                    st.session_state.library_df = new_data
                    st.success("Library updated.")
            else:
                st.error("Column mismatch.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- 5. 功能：抽歌工具 ---
elif menu == "🎲 抽歌工具":
    st.header("Draw Songs")
    if st.session_state.library_df is None:
        st.warning("Please upload library first.")
    else:
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        gender_today = "男" if tomorrow.day % 2 == 0 else "女"
        st.write(f"📅 明日：**{tomorrow.strftime('%Y/%m/%d')}** | 性別：**{gender_today}**")
        
        num_to_draw = st.number_input("Count", 1, 20, 3)

        if st.button("EXECUTE DRAW", type="primary"):
            df = st.session_state.library_df.copy()
            pool = df[df['gender'] == gender_today].copy()
            if pool.empty:
                st.error(f"No songs for gender: {gender_today}")
            else:
                pool['weight'] = 1 / (pool['play_count'] + 1)
                selected = pool.sample(n=min(len(pool), int(num_to_draw)), weights='weight')
                
                # 更新次數
                for idx in selected.index:
                    st.session_state.library_df.at[idx, 'play_count'] += 1
                    st.session_state.library_df.at[idx, 'last_played'] = datetime.datetime.now().strftime("%Y-%m-%d")
                save_data(st.session_state.library_df)

                st.write("### Result")
                output_text = f"🎶 Playlist ({tomorrow.strftime('%m/%d')})\n"
                for i, row in enumerate(selected.itertuples(), 1):
                    st.markdown(f"**{i}. {row.title}** — {row.requester}")
                    if pd.notna(row.link): st.caption(f"🔗 [Link]({row.link})")
                    st.divider()
                    output_text += f"{i}. {row.title} — {row.requester}\n"
                
                st.download_button("Download Playlist (.txt)", output_text, f"playlist_{tomorrow.strftime('%m%d')}.txt")

# --- 6. 功能：查詢與修改 ---
elif menu == "🔍 查詢與修改":
    st.header("Search & Modify")
    if st.session_state.library_df is None:
        st.warning("Please upload library.")
    else:
        search_name = st.text_input("Search by name or title:")
        df = st.session_state.library_df
        
        if search_name:
            results = df[(df['requester'].str.contains(search_name, na=False)) | 
                        (df['title'].str.contains(search_name, na=False))]
            
            if not results.empty:
                for idx, row in results.iterrows():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.write(f"**{row['title']}** ({row['requester']})")
                    new_count = col2.number_input(f"Times", min_value=0, value=int(row['play_count']), key=f"n_{idx}")
                    if col3.button("Update", key=f"b_{idx}"):
                        st.session_state.library_df.at[idx, 'play_count'] = new_count
                        save_data(st.session_state.library_df)
                        st.success("Updated.")
                        st.rerun()
                st.divider()
            else:
                st.write("No records found.")
