import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="油價紀錄系統", page_icon="🚗")

# 預設的駕駛人與車牌清單 (可自行修改)
DRIVERS = ["駕駛 A (陳先生)", "駕駛 B (王小姐)", "駕駛 C"]
PLATES = ["ABC-1234", "DEF-5678", "GHI-9012"]
CSV_FILE = "gas_records.csv" # 資料將會儲存在這個檔案中

st.title("🚗 車輛油價紀錄系統")
st.write("資料將自動儲存於本機的 CSV 檔案中，免設定權限，隨時可用 Excel 開啟。")

# 1. 讀取與儲存資料的函式
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        # 如果檔案不存在，建立一個空的 DataFrame
        return pd.DataFrame(columns=['時間日期', '駕駛人', '車牌', '油價(元/公升)', '公升數(L)', '總價(元)'])

def save_data(df_to_save):
    # 使用 utf-8-sig 編碼，確保用 Excel 打開時中文不會亂碼
    df_to_save.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# 載入資料
df = load_data()

# 2. 新增資料區塊
with st.form("gas_form"):
    st.subheader("➕ 新增加油紀錄")
    col1, col2 = st.columns(2)
    
    with col1:
        driver = st.selectbox("選擇駕駛人", DRIVERS)
        plate = st.selectbox("選擇車牌", PLATES)
    with col2:
        price_per_liter = st.number_input("今日油價 (元/公升)", min_value=0.0, step=0.1, format="%.2f")
        liters = st.number_input("加油公升數 (L)", min_value=0.0, step=0.1, format="%.2f")
        
    submit_button = st.form_submit_button("新增並儲存紀錄")

# 新增資料邏輯
if submit_button:
    if price_per_liter > 0 and liters > 0:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_price = round(price_per_liter * liters, 2)
        
        new_record = pd.DataFrame({
            '時間日期': [current_time],
            '駕駛人': [driver],
            '車牌': [plate],
            '油價(元/公升)': [price_per_liter],
            '公升數(L)': [liters],
            '總價(元)': [total_price]
        })
        
        # 將新資料合併到原本的 DataFrame 並儲存
        updated_df = pd.concat([df, new_record], ignore_index=True)
        save_data(updated_df)
        
        st.success(f"✅ 紀錄成功！駕駛 {driver} 本次加油總花費為 **{total_price} 元**")
        st.rerun() # 重整頁面以顯示最新資料
    else:
        st.error("⚠️ 油價與公升數請輸入大於 0 的數值")

st.divider()

# 3. 刪除與檢視資料區塊
st.subheader("📋 歷史加油紀錄與管理")
st.caption("您可以勾選下方表格最左側的核取方塊，並按下刪除按鈕來移除特定資料。")

if not df.empty:
    # 複製一份資料並加入「選取刪除」欄位
    df_display = df.copy()
    df_display.insert(0, "選取刪除", False)
    
    # 建立可互動的 DataFrame 表格
    edited_df = st.data_editor(
        df_display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "選取刪除": st.column_config.CheckboxColumn("勾選以刪除", default=False)
        },
        # 鎖定其他欄位，防止在此處意外修改到數值 (僅允許勾選)
        disabled=['時間日期', '駕駛人', '車牌', '油價(元/公升)', '公升數(L)', '總價(元)']
    )
    
    # 刪除資料邏輯
    if edited_df["選取刪除"].any():
        if st.button("🗑️ 刪除已勾選資料", type="primary"):
            # 篩選出「未被勾選」的資料保留下來
            df_to_keep = edited_df[edited_df["選取刪除"] == False].drop(columns=["選取刪除"])
            save_data(df_to_keep) # 覆寫存檔
            st.success("✅ 已成功刪除所選資料！")
            st.rerun()
            
    # 統計數據
    total_spent = df['總價(元)'].sum()
    total_liters = df['公升數(L)'].sum()
    st.info(f"💰 累積總花費： **{total_spent:.0f} 元** │ ⛽ 累積加油量： **{total_liters:.2f} 公升**")
else:
    st.write("目前尚未有任何紀錄。")
