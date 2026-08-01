import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import os

st.set_page_config(page_title="油價紀錄系統 (SQLite 專業版)", page_icon="🚗", layout="centered")

# ==========================================
# 1. 資料庫設定與初始化
# ==========================================
DB_FILE = 'gas_records.db'

def init_db():
    """初始化 SQLite 資料庫，如果表格不存在就建立一個"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            時間日期 TEXT,
            駕駛人 TEXT,
            車牌 TEXT,
            油價 REAL,
            公升數 REAL,
            總價 REAL
        )
    ''')
    conn.commit()
    conn.close()

def load_data():
    """從 SQLite 讀取所有資料"""
    conn = sqlite3.connect(DB_FILE)
    # 讀取時按照時間反著排，讓最新的在最上面
    df = pd.read_sql_query("SELECT * FROM records ORDER BY id DESC", conn)
    conn.close()
    return df

def insert_data(time, driver, plate, price, liters, total):
    """新增單筆資料到 SQLite"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO records (時間日期, 駕駛人, 車牌, 油價, 公升數, 總價)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (time, driver, plate, price, liters, total))
    conn.commit()
    conn.close()

def delete_data(delete_ids):
    """根據 ID 刪除 SQLite 中的資料"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 將 list 的 ID 轉為 SQL 語法所需的格式
    c.executemany("DELETE FROM records WHERE id = ?", [(int(i),) for i in delete_ids])
    conn.commit()
    conn.close()

# 確保資料庫與資料表已建立
init_db()

# ==========================================
# 2. 介面與選項設定
# ==========================================
DRIVERS = ["駕駛 A (陳先生)", "駕駛 B (王小姐)", "駕駛 C"]
PLATES = ["ABC-1234", "DEF-5678", "GHI-9012"]

st.title("🚗 車輛油價紀錄系統 (SQLite 版)")
st.write("資料安全儲存在本機資料庫，支援匯出、匯入與刪除功能。")

# ==========================================
# 3. 新增資料區塊
# ==========================================
with st.form("gas_form"):
    st.subheader("➕ 新增加油紀錄")
    col1, col2 = st.columns(2)
    
    with col1:
        driver = st.selectbox("選擇駕駛人", DRIVERS)
        plate = st.selectbox("選擇車牌", PLATES)
    with col2:
        price_per_liter = st.number_input("今日油價 (元/公升)", min_value=0.0, step=0.1, format="%.2f")
        liters = st.number_input("加油公升數 (L)", min_value=0.0, step=0.1, format="%.2f")
        
    submit_button = st.form_submit_button("新增紀錄")

if submit_button:
    if price_per_liter > 0 and liters > 0:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_price = round(price_per_liter * liters, 2)
        
        # 寫入 SQLite
        insert_data(current_time, driver, plate, price_per_liter, liters, total_price)
        
        st.success(f"✅ 紀錄成功！駕駛 {driver} 本次加油總花費為 **{total_price} 元**")
        st.rerun() # 重整畫面載入最新資料
    else:
        st.error("⚠️ 油價與公升數請輸入大於 0 的數值")

st.divider()

# ==========================================
# 4. 歷史紀錄與刪除管理區塊
# ==========================================
st.subheader("📋 歷史加油紀錄與管理")

# 讀取最新資料
df = load_data()

if not df.empty:
    # 建立一個顯示用的 DataFrame，加入勾選刪除欄位
    df_display = df.copy()
    df_display.insert(0, "選取刪除", False)
    
    # 顯示可互動的資料表 (隱藏系統 ID，保護原始資料)
    st.caption("您可以勾選最左側的方塊，並點擊下方按鈕刪除不需要的紀錄。")
    edited_df = st.data_editor(
        df_display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": None, # 隱藏 SQLite 的 PK (主鍵) 欄位
            "選取刪除": st.column_config.CheckboxColumn("勾選刪除", default=False)
        },
        disabled=["時間日期", "駕駛人", "車牌", "油價", "公升數", "總價"] # 防止直接修改數值
    )
    
    # 刪除按鈕邏輯
    # 找出被勾選的資料列
    selected_rows = edited_df[edited_df["選取刪除"] == True]
    if not selected_rows.empty:
        if st.button("🗑️ 刪除已勾選資料", type="primary"):
            # 取得要刪除的 SQLite ID 列表
            ids_to_delete = selected_rows["id"].tolist()
            delete_data(ids_to_delete)
            st.success(f"✅ 已成功刪除 {len(ids_to_delete)} 筆資料！")
            st.rerun()
            
    # 計算統計數據
    total_liters = df['公升數'].sum()
    total_spent = df['總價'].sum()
    st.info(f"💰 累積總花費： **{total_spent:.0f} 元** │ ⛽ 累積加油量： **{total_liters:.2f} 公升**")
    
else:
    st.info("目前資料庫中尚無紀錄。")

st.divider()

# ==========================================
# 5. 匯出與匯入功能 (放進 Expander 保持版面整潔)
# ==========================================
with st.expander("📁 資料匯出與匯入 (CSV)", expanded=False):
    col_export, col_import = st.columns(2)
    
    # --- 匯出功能 ---
    with col_export:
        st.write("**匯出資料庫紀錄**")
        if not df.empty:
            # 準備匯出的資料 (移除 ID 欄位)
            export_df = df.drop(columns=["id"])
            csv_data = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            
            st.download_button(
                label="📥 下載為 CSV 檔案",
                data=csv_data,
                file_name=f"gas_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.write("沒有資料可供匯出。")
            
    # --- 匯入功能 ---
    with col_import:
        st.write("**匯入舊資料 (CSV)**")
        uploaded_file = st.file_uploader("選擇上傳 CSV 檔案", type=["csv"])
        
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                # 檢查必要欄位是否存在
                required_cols = ["時間日期", "駕駛人", "車牌", "油價", "公升數", "總價"]
                if all(col in import_df.columns for col in required_cols):
                    if st.button("🚀 確認匯入"):
                        conn = sqlite3.connect(DB_FILE)
                        # 將符合欄位的資料寫入 SQLite (過濾掉不需要的欄位如 ID)
                        import_df[required_cols].to_sql("records", conn, if_exists="append", index=False)
                        conn.close()
                        st.success(f"✅ 成功匯入 {len(import_df)} 筆資料！")
                        st.rerun()
                else:
                    st.error("匯入失敗：CSV 檔案缺少必要欄位。請確保包含：時間日期, 駕駛人, 車牌, 油價, 公升數, 總價")
            except Exception as e:
                st.error(f"讀取檔案發生錯誤：{e}")
