import streamlit as st
import pandas as pd
import datetime
import numpy as np
import os

# --- 1. 網頁基礎配置 ---
st.set_page_config(page_title="SongMate Web - 點歌助手", page_icon="🎧", layout="wide")

# 自定義 CSS (極簡黑白灰色調)
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
        height: 3em;
    }
    .stButton>button:hover { 
        background-color: #404040; 
        border-color: #404040;
        color: #ffffff;
    }

    /* 數字與文字輸入框 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 4px;
        border: 1px solid #cccccc;
    }

    /* 連結顏色：深灰色 */
    a { color: #555555 !important; text-decoration: underline; }
    
    /* 下載按鈕樣式 */
    div[data-testid="stDownloadButton"] > button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 檔案持久化邏輯 ---
DB_FILE = "song_library.xlsx"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_excel(DB_FILE)
        except:
            return None
    return None

def save_data(df):
    df.to_excel(DB_FILE, index=False)

if 'library_df' not in st.session_state:
    st.session_state.library_df = load_data()

# --- 3. 側邊導覽 ---
with st.sidebar:
    st.title("SONGMATE")
    st.caption("極簡點歌管理系統")
    menu = st.radio("主選單", ["📁 更新歌庫", "🎲 抽歌工具", "🔍 查詢與修改"])
    st.divider()
    if st.session_state.library_df is not None:
        st.write(f"目前歌庫總量: **{len(st.session_state.library_df)}** 筆")

# --- 4. 功能：更新歌庫 ---
if menu == "📁 更新歌庫":
    st.header("匯入點歌清單")
    st.write("請上傳您的 Excel 檔案，系統將自動提取姓名、性別、歌名與連結。")
    uploaded_file = st.file_uploader("選擇 Excel 檔案 (.xlsx)", type=['xlsx'])
    
    if uploaded_file:
        try:
            df_raw = pd.read_excel(uploaded_file)
            # 對應中文欄位
            target_cols = {"姓名": "requester", "性別": "gender", "歌名": "title", "歌曲連結": "link"}
            
            if all(col in df_raw.columns for col in target_cols.keys()):
                new_data = df_raw[list(target_cols.keys())].copy()
                new_data.rename(columns=target_cols, inplace=True)
                # 初始化必要欄位
                new_data['play_count'] = 0
                new_data['last_played'] = "從未播放"
                
                st.write("📋 **預覽擷取資料：**")
                st.dataframe(new_data, use_container_width=True)
                
                if st.button("確認匯入並儲存"):
                    save_data(new_data)
                    st.session_state.library_df = new_data
                    st.success("✅ 歌庫更新成功！")
            else:
                st.error("❌ 檔案欄位不符，請確保包含：姓名、性別、歌名、歌曲連結")
        except Exception as e:
            st.error(f"讀取錯誤：{e}")

# --- 5. 功能：抽歌工具 ---
elif menu == "🎲 抽歌工具":
    st.header("隨機抽歌")
    if st.session_state.library_df is None:
        st.warning("⚠️ 尚未偵測到歌庫，請先前往「更新歌庫」上傳檔案。")
    else:
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        gender_today = "男" if tomorrow.day % 2 == 0 else "女"
        
        st.markdown(f"📅 明日日期：**{tomorrow.strftime('%Y/%m/%d')}**")
        st.markdown(f"👤 本日目標性別：**{gender_today} 性**")
        
        num_to_draw = st.number_input("預計抽出數量", min_value=1, max_value=20, value=3)

        if st.button("🔥 執行抽歌", type="primary"):
            df = st.session_state.library_df.copy()
            pool = df[df['gender'] == gender_today].copy()
            
            if pool.empty:
                st.error(f"❌ 歌庫中沒有 {gender_today} 性的歌曲，無法執行。")
            else:
                # 權重算法 (次數愈少，機率愈高)
                pool['weight'] = 1 / (pool['play_count'] + 1)
                selected = pool.sample(n=min(len(pool), int(num_to_draw)), weights='weight')
                
                # 自動更新播放次數
                for idx in selected.index:
                    st.session_state.library_df.at[idx, 'play_count'] += 1
                    st.session_state.library_df.at[idx, 'last_played'] = datetime.datetime.now().strftime("%Y-%m-%d")
                save_data(st.session_state.library_df)

                st.write("---")
                st.write("### 🎶 抽籤結果")
                
                output_text = f"🎶 播放清單（{gender_today}日）\n"
                for i, row in enumerate(selected.itertuples(), 1):
                    st.markdown(f"**{i}. {row.title}** — {row.requester} (累計播放 {row.play_count} 次)")
                    if pd.notna(row.link):
                        st.caption(f"🔗 [點我播放歌曲]({row.link})")
                    st.divider()
                    output_text += f"{i}. {row.title} — {row.requester}\n"
                
                st.download_button("💾 下載播放清單 (.txt)", output_text, f"playlist_{tomorrow.strftime('%m%d')}.txt")

# --- 6. 功能：查詢與修改 ---
elif menu == "🔍 查詢與修改":
    st.header("查詢與次數調整")
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先匯入歌庫資料。")
    else:
        search_name = st.text_input("輸入關鍵字搜尋 (姓名或歌名)：")
        df = st.session_state.library_df
        
        if search_name:
            results = df[(df['requester'].str.contains(search_name, na=False)) | 
                        (df['title'].str.contains(search_name, na=False))]
            
            if not results.empty:
                st.write(f"找到 {len(results)} 筆結果：")
                for idx, row in results.iterrows():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.write(f"🎵 **{row['title']}** — {row['requester']}")
                    new_count = col2.number_input(f"次數", min_value=0, value=int(row['play_count']), key=f"n_{idx}")
                    if col3.button("更新", key=f"b_{idx}"):
                        st.session_state.library_df.at[idx, 'play_count'] = new_count
                        save_data(st.session_state.library_df)
                        st.success(f"《{row['title']}》次數已更新。")
                        st.rerun()
                st.divider()
            else:
                st.info("查無此歌曲或點歌人。")
