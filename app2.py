import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image

st.set_page_config(page_title="油價紀錄系統 (本機 OCR 版)", page_icon="🚗", layout="centered")

# 如果在 Windows 本機測試，請解除下方註解並填入您安裝 tesseract 的路徑
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ==========================================
# 0. 初始化 Session State
# ==========================================
if 'ocr_price' not in st.session_state: st.session_state.ocr_price = 0.0
if 'ocr_liters' not in st.session_state: st.session_state.ocr_liters = 0.0
if 'ocr_invoice' not in st.session_state: st.session_state.ocr_invoice = ""
if 'ocr_tax_id' not in st.session_state: st.session_state.ocr_tax_id = ""

# ==========================================
# 1. 資料庫設定與初始化
# ==========================================
DB_FILE = 'gas_records.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            時間日期 TEXT,
            發票號碼 TEXT,
            統編 TEXT,
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
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM records ORDER BY id DESC", conn)
    conn.close()
    return df

def insert_data(time, invoice, tax_id, driver, plate, price, liters, total):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO records (時間日期, 發票號碼, 統編, 駕駛人, 車牌, 油價, 公升數, 總價)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (time, invoice, tax_id, driver, plate, price, liters, total))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. 本機 OCR 影像處理與解析邏輯
# ==========================================
def extract_receipt_data(image_file):
    # 讀取影像並轉為 OpenCV 格式
    image = Image.open(image_file)
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 預處理：灰階化與二值化 (提升黑白收據的文字對比度)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # 進行 OCR 辨識 (指定繁體中文與英文)
    # 若 Streamlit 找不到 chi_tra，可先用 eng 測試
    try:
        text = pytesseract.image_to_string(thresh, lang='chi_tra+eng')
    except Exception as e:
        st.error("Tesseract 引擎錯誤，請確認已正確安裝系統套件。")
        return {}

    # 使用正規表達式擷取資料
    data = {
        "invoice_number": "",
        "tax_id": "",
        "price": 0.0,
        "liters": 0.0
    }
    
    # 1. 找發票號碼 (格式: AB-12345678 或 AB12345678)
    inv_match = re.search(r'[A-Za-z]{2}[- ]?\d{8}', text)
    if inv_match:
        data["invoice_number"] = inv_match.group(0).replace(" ", "").upper()
        
    # 2. 找統編 (連續 8 個數字，且通常伴隨統編字眼)
    tax_match = re.search(r'(統編|統一編號|編號)[\s:：]*(\d{8})', text)
    if tax_match:
        data["tax_id"] = tax_match.group(2)
    else:
        # 退而求其次，找不在發票號碼內的連續 8 碼
        all_8_digits = re.findall(r'(?<!\d)\d{8}(?!\d)', text)
        for d in all_8_digits:
            if d not in data["invoice_number"]:
                data["tax_id"] = d
                break
                
    # 3. 找浮點數 (油價與公升數)
    floats = [float(x) for x in re.findall(r'\d+\.\d+', text)]
    if floats:
        # 經驗法則：台灣油價通常在 20.0 到 40.0 之間
        prices = [f for f in floats if 20.0 <= f <= 40.0]
        if prices:
            data["price"] = prices[0]
            floats.remove(prices[0])
            
        # 剩下的浮點數中最有可能是公升數
        if floats:
            data["liters"] = max(floats) # 通常公升數會是剩下的數字中較大的
            
    return data

# ==========================================
# 3. 介面設計
# ==========================================
DRIVERS = ["駕駛 A (陳先生)", "駕駛 B (王小姐)", "駕駛 C"]
PLATES = ["ABC-1234", "DEF-5678", "GHI-9012"]

st.title("🚗 車輛油價紀錄系統 (本機 OCR 版)")

with st.expander("📷 拍下發票自動辨識 (純本機處理)", expanded=True):
    col_cam, col_up = st.columns(2)
    with col_cam:
        camera_photo = st.camera_input("使用相機拍照")
    with col_up:
        uploaded_photo = st.file_uploader("或上傳照片檔案", type=["jpg", "jpeg", "png"])
    
    photo_to_process = camera_photo or uploaded_photo
    
    if photo_to_process is not None:
        if st.button("🔍 執行 OCR 解析", type="primary"):
            with st.spinner("正在進行影像處理與文字辨識..."):
                extracted_data = extract_receipt_data(photo_to_process)
                
                st.session_state.ocr_invoice = extracted_data.get("invoice_number", "")
                st.session_state.ocr_tax_id = extracted_data.get("tax_id", "")
                st.session_state.ocr_price = extracted_data.get("price", 0.0)
                st.session_state.ocr_liters = extracted_data.get("liters", 0.0)
                
                st.success("✅ 辨識完成！資料已自動帶入，若有誤差請手動微調。")

# ==========================================
# 4. 新增資料區塊
# ==========================================
with st.form("gas_form"):
    st.subheader("➕ 確認與新增加油紀錄")
    
    col1, col2 = st.columns(2)
    with col1:
        invoice = st.text_input("發票號碼", value=st.session_state.ocr_invoice)
        tax_id = st.text_input("統一編號", value=st.session_state.ocr_tax_id)
        driver = st.selectbox("選擇駕駛人", DRIVERS)
        plate = st.selectbox("選擇車牌", PLATES)
    with col2:
        price_per_liter = st.number_input("今日油價 (元/公升)", min_value=0.0, step=0.1, format="%.2f", value=st.session_state.ocr_price)
        liters = st.number_input("加油公升數 (L)", min_value=0.0, step=0.1, format="%.2f", value=st.session_state.ocr_liters)
        
    submit_button = st.form_submit_button("儲存紀錄")

if submit_button:
    if price_per_liter > 0 and liters > 0:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_price = round(price_per_liter * liters, 2)
        
        insert_data(current_time, invoice, tax_id, driver, plate, price_per_liter, liters, total_price)
        
        # 儲存後清空快取
        st.session_state.ocr_invoice = ""
        st.session_state.ocr_tax_id = ""
        st.session_state.ocr_price = 0.0
        st.session_state.ocr_liters = 0.0
        
        st.success(f"✅ 紀錄成功！本次加油總花費為 **{total_price} 元**")
        st.rerun()
    else:
        st.error("⚠️ 油價與公升數請輸入大於 0 的數值")

st.divider()

# ==========================================
# 5. 歷史紀錄與管理區塊
# ==========================================
st.subheader("📋 歷史加油紀錄")
df = load_data()

if not df.empty:
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)
    
    total_liters = df['公升數'].sum()
    total_spent = df['總價'].sum()
    st.info(f"💰 累積總花費： **{total_spent:.0f} 元** │ ⛽ 累積加油量： **{total_liters:.2f} 公升**")
else:
    st.info("目前資料庫中尚無紀錄。")
