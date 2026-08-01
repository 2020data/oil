import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="油價紀錄系統 (Google免權限版)", page_icon="🚗")

# ==========================================
# ✅ 1. Google 試算表 CSV 連結 (讀取用)
# ==========================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4PD1rG0HIskYwzdpMaBta0HIm6ntqOweItLFrf6E7bFqcCTarL_bvRQLrwz6QslOn_YtK2B2Ktw7q/pub?gid=1893679528&single=true&output=csv"

# ==========================================
# ✅ 2. Google 表單的提交網址 (寫入用)
# ==========================================
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfDrumdCr_o6EnYyhYZC0OMtiewvfXnTkEodigo5O_lTbJgyQ/formResponse"

# ==========================================
# ✅ 3. Google 表單的 entry ID
# ==========================================
FORM_ENTRIES = {
    "時間日期": "entry.2056955558", 
    "駕駛人": "entry.1235868062",   
    "車牌": "entry.2029113890",     
    "油價": "entry.1366975257",     
    "公升數": "entry.361410122",   
    "總價": "entry.371274649"      
}
# ==========================================

DRIVERS = ["駕駛 A (陳先生)", "駕駛 B (王小姐)", "駕駛 C"]
PLATES = ["ABC-1234", "DEF-5678", "GHI-9012"]

st.title("🚗 車輛油價紀錄系統")
st.write("資料將自動儲存於 Google 試算表 (透過表單免權限寫入)。")

@st.cache_data(ttl=5) # 快取 5 秒，避免一直重複請求
def load_data():
    try:
        # 直接讀取 Google CSV 連結
        df = pd.read_csv(SHEET_CSV_URL)
        # 去除全空的欄位與列
        df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# 新增資料區塊
with st.form("gas_form"):
    st.subheader("➕ 新增加油紀錄")
    col1, col2 = st.columns(2)
    
    with col1:
        driver = st.selectbox("選擇駕駛人", DRIVERS)
        plate = st.selectbox("選擇車牌", PLATES)
    with col2:
        price_per_liter = st.number_input("今日油價 (元/公升)", min_value=0.0, step=0.1, format="%.2f")
        liters = st.number_input("加油公升數 (L)", min_value=0.0, step=0.1, format="%.2f")
        
    submit_button = st.form_submit_button("新增並上傳至 Google 試算表")

# 新增資料邏輯 (透過發送 HTTP POST 給 Google 表單)
if submit_button:
    if price_per_liter > 0 and liters > 0:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_price = round(price_per_liter * liters, 2)
        
        # 準備要傳送給 Google 表單的資料字典
        form_data = {
            FORM_ENTRIES["時間日期"]: current_time,
            FORM_ENTRIES["駕駛人"]: driver,
            FORM_ENTRIES["車牌"]: plate,
            FORM_ENTRIES["油價"]: str(price_per_liter),
            FORM_ENTRIES["公升數"]: str(liters),
            FORM_ENTRIES["總價"]: str(total_price)
        }
        
        # 背景發送請求給 Google 表單
        try:
            response = requests.post(FORM_SUBMIT_URL, data=form_data)
            if response.status_code == 200:
                st.success(f"✅ 紀錄成功！駕駛 {driver} 本次加油總花費為 **{total_price} 元**")
                # 清除快取並重整，讓表格抓取最新資料
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("寫入失敗，請確認表單網址與 entry ID 是否正確。")
        except Exception as e:
            st.error(f"連線錯誤: {e}")
    else:
        st.error("⚠️ 油價與公升數請輸入大於 0 的數值")

st.divider()

# 檢視資料區塊
st.subheader("📋 歷史加油紀錄")
st.caption("備註：免權限模式無法直接從網頁刪除資料。如需刪除錯誤紀錄，請直接前往您的 Google 試算表操作。")

if not df.empty:
    try:
        # 反轉表格，讓最新的紀錄顯示在最上面
        df_display = df.iloc[::-1].reset_index(drop=True)
        st.dataframe(df_display, use_container_width=True)
        
        # 嘗試抓取最後兩欄來計算總公升數與總價 (確保資料為數值格式)
        total_liters = pd.to_numeric(df.iloc[:, -2], errors='coerce').sum()
        total_spent = pd.to_numeric(df.iloc[:, -1], errors='coerce').sum()
        st.info(f"💰 累積總花費： **{total_spent:.0f} 元** │ ⛽ 累積加油量： **{total_liters:.2f} 公升**")
    except Exception as e:
        st.dataframe(df, use_container_width=True)
        st.write("資料格式尚在建立中，目前無法顯示統計數字。")
else:
    st.write("目前尚未讀取到任何紀錄，或試算表為空。")
