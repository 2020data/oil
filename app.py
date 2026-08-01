import streamlit as st
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="油價紀錄小工具", page_icon="🚗")

# 初始化 session_state 來儲存歷史紀錄，這樣重整頁面時資料才不會不見
if 'gas_records' not in st.session_state:
    st.session_state.gas_records = pd.DataFrame(columns=['日期時間', '油價 (元/公升)', '公升數 (L)', '總價 (元)'])

st.title("🚗 個人油價紀錄")
st.write("輸入今日油價與公升數，系統會自動幫您帶入時間並計算總金額！")

# 建立輸入表單
with st.form("gas_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        price_per_liter = st.number_input("今日油價 (元/公升)", min_value=0.0, step=0.1, format="%.2f")
    with col2:
        liters = st.number_input("加油公升數 (L)", min_value=0.0, step=0.1, format="%.2f")
        
    submit_button = st.form_submit_button("新增紀錄")

# 當按下按鈕時的處理邏輯
if submit_button:
    if price_per_liter > 0 and liters > 0:
        # 自動取得現在的時間
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 計算總價
        total_price = price_per_liter * liters
        
        # 建立一筆新資料
        new_record = pd.DataFrame({
            '日期時間': [current_time],
            '油價 (元/公升)': [price_per_liter],
            '公升數 (L)': [liters],
            '總價 (元)': [round(total_price, 2)]
        })
        
        # 將新資料加入原本的 DataFrame 中
        st.session_state.gas_records = pd.concat([st.session_state.gas_records, new_record], ignore_index=True)
        st.success(f"✅ 紀錄成功！本次加油總花費為 **{total_price:.0f} 元**")
    else:
        st.error("⚠️ 油價與公升數請輸入大於 0 的數值")

st.divider()

# 顯示歷史紀錄表格
st.subheader("📋 歷史加油紀錄")

if not st.session_state.gas_records.empty:
    # 顯示 DataFrame 表格
    st.dataframe(st.session_state.gas_records, use_container_width=True)
    
    # 簡單的統計數據
    total_spent = st.session_state.gas_records['總價 (元)'].sum()
    total_liters = st.session_state.gas_records['公升數 (L)'].sum()
    
    st.info(f"💰 累積總花費： **{total_spent:.0f} 元** │ ⛽ 累積加油量： **{total_liters:.2f} 公升**")
    
    # 提供清除紀錄的按鈕
    if st.button("清除所有紀錄"):
        st.session_state.gas_records = pd.DataFrame(columns=['日期時間', '油價 (元/公升)', '公升數 (L)', '總價 (元)'])
        st.rerun()
else:
    st.write("目前尚未有任何紀錄。快在上方新增你的第一筆加油紀錄吧！")
