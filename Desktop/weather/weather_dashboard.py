import requests
import streamlit as st
import pandas as pd
from google import genai # <--- 新增
import datetime 

st.title("台灣氣象資料 Dashboard - LLM 解讀版")

# ----------------------------------------------------
# 📌 API Key 設置
# ----------------------------------------------------
try:
    # 讀取 CWA API Key
    CWA_API_KEY = st.secrets["cwa_api"]["key"]
    # 讀取 Gemini API Key
    GEMINI_API_KEY = st.secrets["gemini"]["key"]
except KeyError:
    # 如果任一個 Key 找不到，程式會在這裡停止
    st.error("找不到 API 授權碼。請檢查您的 Streamlit Secrets 設定！")
    st.stop() # <--- 這是中斷點！

# 初始化 Gemini 客戶端
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Gemini 客戶端初始化失敗: {e}")
    st.stop()

# 讓使用者選擇城市
LOCATION = st.selectbox("選擇城市", ["臺北市", "臺中市", "高雄市"]) 

# CWA API 抓取邏輯 (保持不變)
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={CWA_API_KEY}"

try:
    res = requests.get(url, verify=False, timeout=10) 
except requests.exceptions.RequestException as e:
    st.error(f"連線至 CWA API 失敗！錯誤：{e}")
    st.stop() # 確保程式在這裡停止，避免後續錯誤

# --- 關鍵除錯點：檢查狀態碼 ---
if res.status_code != 200:
    st.error(f"CWA API 請求失敗！HTTP 狀態碼：{res.status_code}")
    st.warning("請檢查您的 CWA 授權碼。程式即將停止。")
    st.stop() # <--- 這是 NameError 的主要來源

# ... 後續的 JSON 解析邏輯保持不變 ...

# 如果上面都沒有中斷，location 變數會被定義 (可能是 None 或物件)
location_list = data["records"]["location"]
location = next((loc for loc in location_list if loc['locationName'] == LOCATION), None)

# ----------------------------------------------------
# 📌 LLM 處理邏輯 (主要新增部分)
# ----------------------------------------------------

if location:
    st.subheader(f"✨ 來自 Gemini 的 {location['locationName']} 預報解讀")
    
    # 1. 準備 LLM 提示 (Prompt)
    # 我們只將單一城市的資料傳給 LLM
    location_data_for_llm = {
        "locationName": location['locationName'],
        "weatherElement": location["weatherElement"]
    }
    
    # 將 Python dict 轉換為 JSON 字串，方便 LLM 理解結構
    import json
    data_json_str = json.dumps(location_data_for_llm, ensure_ascii=False, indent=2)
    
    # 建立給 LLM 的指示
    llm_prompt = f"""
    您是一位專業且親切的天氣播報員。
    請根據以下臺灣氣象署提供的 {location['locationName']} 36 小時天氣預報 JSON 資料，
    
    1. 使用**溫和、親切並帶有問候的語氣**，為使用者總結最重要的天氣資訊。
    2. 內容必須包含：未來 12 小時的**天氣狀況 (Wx)**、**最低溫 (MinT)**、**最高溫 (MaxT)**、**降雨機率 (PoP)**、以及一個**穿衣建議 (CI)**。
    3. 您的回答應以中文呈現，請勿直接輸出原始 JSON 程式碼。

    原始 JSON 資料如下：
    {data_json_str}
    """
    
    # 2. 呼叫 Gemini API
    with st.spinner('Gemini 正在為您解讀天氣資料中...'):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', # 選擇一個快速的模型
                contents=llm_prompt
            )
            # 3. 使用介面呈現 LLM 處理的結果
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"呼叫 Gemini API 失敗: {e}")
            st.warning("請檢查您的 Gemini API Key 是否正確設定在 secrets 中。")
    
    # ----------------------------------------------------
    # 📌 (可選) 繪圖和原始資料顯示區域 (保留或移除)
    # ----------------------------------------------------
    # 您可以選擇保留溫度圖表或直接移除，因為 LLM 已經總結了所有資訊
    # 為了作業完整性，我們保留溫度趨勢圖
    # ... (將您繪製溫度圖表的程式碼貼在這裡) ...

else:
    st.warning(f"找不到城市 {LOCATION} 的資料。")