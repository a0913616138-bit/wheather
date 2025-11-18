import requests
import streamlit as st
import pandas as pd
import datetime # 為了處理時間欄位

st.title("台灣氣象資料 Dashboard")

try:
    API_KEY = st.secrets["cwa_api"]["key"]
except KeyError:
    st.error("找不到 API 授權碼。請檢查您的 Streamlit Secrets 設定！")
    st.stop()

# 讓使用者選擇城市
LOCATION = st.selectbox("選擇城市", ["臺北市", "臺中市", "高雄市"]) 

# 完整 API 請求網址 (已移除 locationName 參數，改在 Python 中篩選)
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWA-CEA5FE0E-EF3C-472A-BC76-A1E67B6DADFE"

# 2. 發送 GET 請求抓取資料
res = requests.get(url, verify=False)

# 錯誤處理：檢查 HTTP 狀態碼
if res.status_code != 200:
    st.error(f"HTTP 請求失敗！狀態碼：{res.status_code}")
    st.warning("請檢查您的 API 授權碼是否正確。")
    st.stop()
    
# 錯誤處理：解析 JSON
try:
    data = res.json()
except requests.exceptions.JSONDecodeError:
    st.error("API 響應非 JSON 格式！")
    st.stop()

# 錯誤處理：檢查 API 是否返回錯誤訊息
if data.get('success') != 'true':
    st.error(f"API 請求失敗: {data.get('message', '未知錯誤')}")
    st.stop()

# 取得所有縣市的 location 列表
location_list = data["records"]["location"]

# 尋找使用者選擇的城市資料
location = next((loc for loc in location_list if loc['locationName'] == LOCATION), None)

if location:
    st.subheader(f"📌 {location['locationName']} 36小時預報")
    
    # ----------------------------------------------------
    # 📌 視覺化處理區域 (新增部分)
    # ----------------------------------------------------
    
    # 將所有天氣元素重新整理成 dictionary，方便查找
    elements = {}
    for element in location["weatherElement"]:
        elements[element["elementName"]] = element["time"]
        
    # 準備繪圖的數據
    plot_data = []

    # 確保 MinT 和 MaxT 數據存在
    if 'MinT' in elements and 'MaxT' in elements:
        # 遍歷 MinT 的時間段 (三個時段)
        for i in range(len(elements['MinT'])):
            
            # 使用結束時間作為該預報時段的代表時間點
            end_time_str = elements['MinT'][i]['endTime'] 
            
            # 獲取 MinT 和 MaxT 的數值
            # 注意：這裡假設 'parameter' 欄位存在，且值為 string 數字
            mint_value = elements['MinT'][i]['parameter']['parameterName']
            maxt_value = elements['MaxT'][i]['parameter']['parameterName']
            
            # 建立單一時間點的數據物件
            plot_data.append({
                '時間': end_time_str,
                '最低溫 (MinT)': int(mint_value),
                '最高溫 (MaxT)': int(maxt_value)
            })

        # 建立 Pandas DataFrame
        df = pd.DataFrame(plot_data)
        
        # 將時間欄位轉換為 datetime 物件，並設定為索引 (Streamlit Line Chart 繪圖要求)
        df['時間'] = pd.to_datetime(df['時間']).dt.tz_localize('Asia/Taipei')
        df = df.set_index('時間')
        
        # 繪製線圖
        st.subheader("🌡️ 36小時溫度趨勢")
        st.line_chart(df)
    
    # ----------------------------------------------------
    # 📌 文字資訊顯示區域 (原有部分，只顯示第一個時段)
    # ----------------------------------------------------
    st.subheader("當前及未來 12 小時主要預報資訊")
    
    # 迭代 weatherElement 顯示天氣資訊，但跳過已繪圖的 MinT/MaxT
    for element in location["weatherElement"]:
        name = element["elementName"]
        
        # 跳過已經繪圖的 MinT 和 MaxT
        if name in ['MinT', 'MaxT']:
            continue
            
        # 取得第一個時間點的參數值 (如果存在)
        if element["time"]:
            time_entry = element["time"][0]
            
            # 處理帶 'parameter' 的欄位 (如 Wx, PoP, CI)
            if "parameter" in time_entry:
                value = time_entry["parameter"]["parameterName"]
                st.write(f"**{name}**: {value}")
            
            # 處理帶 'elementValue' 的欄位 (如果 API 結構有變化)
            elif "elementValue" in time_entry:
                value = time_entry["elementValue"]["value"]
                unit = time_entry["elementValue"]["measures"]
                st.write(f"**{name}**: {value} {unit}")
                
        else:
            st.write(f"**{name}**: 資料暫缺")

else:
    st.warning(f"找不到城市 {LOCATION} 的資料。")