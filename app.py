import streamlit as st
import pandas as pd
import datetime
import numpy as np

# --- 1. 網頁基礎配置 ---
st.set_page_config(
    page_title="SongMate Web - 點歌助手",
    page_icon="🎧",
    layout="wide"
)

# 自定義 CSS 美化 (WinUI 風格)
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { 
        border-radius: 8px; 
        background-color: #0078d4; 
        color: white; 
        width: 100%;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #005a9e; border: none; }
    .song-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        background-color: white;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 狀態管理 ---
if 'library_df' not in st.session_state:
    st.session_state.library_df = None

# --- 3. 側邊導覽列 ---
with st.sidebar:
    st.title("🎧 SongMate")
    st.write("版本：Web 1.0 (Render)")
    menu = st.radio("功能選單", ["📁 更新歌庫", "🎲 抽歌工具", "🔍 查詢記錄"])
    st.divider()
    st.caption("提示：Render 免費版若重啟，資料需重新上傳。")

# --- 4. 功能邏輯：更新歌庫 ---
if menu == "📁 更新歌庫":
    st.header("更新歌庫")
    uploaded_file = st.file_uploader("請選擇『線上點歌.xlsx』", type=['xlsx'])
    
    if uploaded_file:
        try:
            df_raw = pd.read_excel(uploaded_file)
            
            # 定義需要的欄位，排除「填寫時間」、「Email」與「ID」
            target_cols = {
                "姓名": "requester",
                "性別": "gender",
                "歌名": "title",
                "歌曲連結": "link"
            }
            
            if all(col in df_raw.columns for col in target_cols.keys()):
                # 提取並重命名
                new_data = df_raw[list(target_cols.keys())].copy()
                new_data.rename(columns=target_cols, inplace=True)
                
                # 初始化播放次數
                new_data['play_count'] = 0
                new_data['last_played'] = "從未播放"
                
                st.write("✅ **偵測成功！預覽資料如下：**")
                st.dataframe(new_data, use_container_width=True)
                
                if st.button("確認匯入歌庫"):
                    st.session_state.library_df = new_data
                    st.success(f"成功匯入 {len(new_data)} 筆點歌資料！")
            else:
                st.error(f"❌ 檔案欄位不匹配。請確保包含：{', '.join(target_cols.keys())}")
        except Exception as e:
            st.error(f"讀取出錯：{e}")

# --- 5. 功能邏輯：抽歌工具 ---
elif menu == "🎲 抽歌工具":
    st.header("抽歌工具")
    
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先前往『更新歌庫』上傳 Excel 檔案。")
    else:
        # 性別判斷邏輯
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        gender_today = "男" if tomorrow.day % 2 == 0 else "女"
        
        st.info(f"📅 明日 ({tomorrow.strftime('%m/%d')}) 是 **{gender_today}日**")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            num_to_draw = st.number_input("預計抽出數量", 1, 20, 3)
        
        if st.button("🔥 開始加權抽歌", type="primary"):
            df = st.session_state.library_df.copy()
            
            # 篩選性別
            pool = df[df['gender'] == gender_today].copy()
            
            if pool.empty:
                st.error(f"❌ 歌庫中目前沒有 {gender_today} 性的歌曲。")
            else:
                # 權重算法: 次數愈少機率愈高
                pool['weight'] = 1 / (pool['play_count'] + 1)
                
                sample_size = min(len(pool), int(num_to_draw))
                selected = pool.sample(n=sample_size, weights='weight')
                
                st.write("### 🎶 抽籤結果")
                
                output_text = f"🎶 播放清單（{gender_today}日）\n"
                
                for i, row in enumerate(selected.itertuples(), 1):
                    with st.container():
                        st.markdown(f"**{i}. {row.title}** — {row.requester}")
                        if pd.notna(row.link) and str(row.link).startswith('http'):
                            st.caption(f"🔗 [點我播放歌曲]({row.link})")
                        else:
                            st.caption("🔗 (無有效連結)")
                        st.divider()
                    output_text += f"{i}. {row.title} — {row.requester}\n"
                
                st.download_button(
                    label="💾 下載播放清單 (.txt)",
                    data=output_text,
                    file_name=f"playlist_{tomorrow.strftime('%m%d')}.txt",
                    mime="text/plain"
                )
                st.balloons()

# --- 6. 功能邏輯：查詢記錄 ---
elif menu == "🔍 查詢記錄":
    st.header("查詢點歌記錄")
    if st.session_state.library_df is None:
        st.warning("⚠️ 請先上傳歌庫。")
    else:
        search_name = st.text_input("輸入姓名搜尋：")
        if search_name:
            df = st.session_state.library_df
            results = df[df['requester'].str.contains(search_name, na=False)]
            if not results.empty:
                st.write(f"🎤 {search_name} 點過的歌曲：")
                st.table(results[['title', 'gender', 'play_count']])
            else:
                st.write("😅 找不到相關記錄。")
