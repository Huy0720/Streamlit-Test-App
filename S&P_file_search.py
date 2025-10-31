import streamlit as st
import datetime
from collections import defaultdict
from utils.sp_auth import get_access_token, refresh_access_token
import requests
import time
import builtins
import json

FILETYPE_MAPPING = {
    142: "10-K",
    143: "10-K/A",
    144: "10-K405",
    145: "10-K405/A",
    146: "10-KT",
    147: "10-KT/A",
    160: "10-Q",
    161: "10-Q/A",
    162: "10-QT",
    163: "10-QT/A",
    169: "20-F",
    170: "20-F/A",
    259: "8-K",
    260: "8-K/A",
    261: "8-K12B",
    262: "8-K12B/A",
    263: "8-K12G3",
    264: "8-K12G3/A",
    265: "8-K15D5",
    266: "8-K15D5/A",
    25: "40-F",
    171: "40-F",
    172: "40-F/A",
    257: "6-K",
    258: "6-K/A",
    174: "MEG - AR",
    177: "AR",
    178: "ARS",
    179: "ARS/A",
    192: "FIN SUPP",
    193: "Intierra SR",
    196: "SR",
    197: "Tanshin",
    199: "QR",
    200: "QR/A",
    968: "Other Financials",
    188: "Yuho",
    432: "Sustainability Report",
    1010: "Corporate Social Responsibility Report",
    1090: "Corporate Governance Report",
    1091: "Environmental Report",
    1105: "TCFD Report",
    127: "S-1",
    867: "S-1",
    868: "S-1/A"
}

# Run using 
# streamlit run streamlit_app.py \
#   --server.address 0.0.0.0 \
#   --server.port 8501 \
#   --server.fileWatcherType none

# streamlit run streamlit_app.py \
#     --server.address 0.0.0.0 \
#     --server.port 8501 \
#     --server.fileWatcherType=watchdog \
#     --server.fileWatcherWhitelist="streamlit_app.py"


access_token, refresh_token, expires_in_seconds = get_access_token()
headers = {
    "accept": "*/*",
    "Authorization": "Bearer " + access_token,  # Replace with your actual access token
    "Content-Type": "application/json"
}
url = "https://api-ciq.marketintelligence.spglobal.com/gds/documents/api/v1/search?docType=FILINGS_DOCUMENTS_API"

st.title("Streamlit Testing")

companyid = st.number_input("Company ID", min_value=1, step=1)

filetype_options = {name: fid for fid, name in FILETYPE_MAPPING.items()}

# Multi-select (shows names, returns IDs)
selected_filetypes = st.multiselect(
    "Select Filetype(s)",
    options=list(filetype_options.keys()),
    #default=[FILETYPE_MAPPING[1]]  
)

selected_ids = [filetype_mapping_id for name, filetype_mapping_id in filetype_options.items() if name in selected_filetypes]

start_year = st.number_input("Start Year", min_value=1990, max_value=datetime.datetime.now().year, value=2020, step=1)
end_year = st.number_input("End Year", min_value=start_year, max_value=datetime.datetime.now().year, value=2023, step=1)


min_filing_date = f"{start_year}-01-01"
min_date = datetime.datetime.strptime(min_filing_date, "%Y-%m-%d")

current_year = datetime.datetime.now().year

if end_year >= current_year:
    max_filing_date = datetime.datetime.now()
else:
    max_filing_date = f"{end_year}-12-31"
    max_filing_date = datetime.datetime.strptime(max_filing_date, "%Y-%m-%d")

result = defaultdict(list)

if st.button("🔍 Run Search"):
    while min_date <= max_filing_date:
        max_date = min_date + datetime.timedelta(days=89)

        max_filing_date_str = max_date.strftime("%Y-%m-%d")
        min_filing_date_str = min_date.strftime("%Y-%m-%d")

        data = {
            "properties": {
                "companyId": companyid if isinstance(companyid, list) else [companyid],
                "minPeriodDate": min_filing_date_str,
                "maxPeriodDate": max_filing_date_str,
                "fileSource": [
                    'ACQUIREMEDIA',
                    'CN_SEC_INFO',
                    'COMPANIES_HOUSE',
                    'EDGAR_SYSTEM',
                    'EGYPT_STOCK_EX',
                    'KLOOKS',
                    'KOLON_BENIT',
                    'NZX',
                    'PALESTINE_SEC_EX',
                    'PHILIPPINE_STOCK_EX',
                    'SINGAPORE_STOCK_EX',
                    'SP_GLOBAL',
                    'SP_GLOBAL_MEG',
                    'STOCK_EXCHANGE'
                ],
                "languageId": [0],
                "fileTypeId": selected_ids if isinstance(selected_ids, list) else [selected_ids]  #[177, 178,179,432]
            }
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            try:
                json_data = response.json()
                #print(json_data)
                if isinstance(json_data, builtins.dict) and "rows" in json_data:
                    rows = json_data["rows"]
                    if rows is not None:  # Check if rows is not None
                        for row in rows:
                            row_data = row.get("row", [])
                            if len(row_data) > 11:
                                company_id = row_data[0]
                                institution_id = row_data[1]
                                filing_date = row_data[2]
                                period_date = row_data[3]
                                processed_date = row_data[4]
                                file_type_id = row_data[5]
                                filing_version_id = row_data[11]  
                                #print(filing_version_id)
                                period_year = period_date[:4]
                                result[company_id].append((filing_version_id, period_year, file_type_id))

                else:
                    print(f"Unexpected response structure for {companyid}.")
            except json.JSONDecodeError:
                print(f"Error decoding JSON response for {companyid}.")
        elif response.status_code == 429:
            print(f"Rate Limiting for {companyid}.")
            print("Headers:", response.headers)
            try:
                error_data = response.json()
                print(error_data.get("message", "No message field"))
            except ValueError: 
                # response was not JSON
                print("429 Too Many Requests")
                print("Response text:", response.text)
        
        else:
            print(f"Error: Received status code {response.status_code} for folder ID {companyid}. Response: {response.text}")

        min_date += datetime.timedelta(days=90)
        time.sleep(0.1)

    if not result:
        print(f"Result is empty for {companyid}")
        st.write(f"Result is empty for {companyid}")
    else:
        print(result)
        st.write(f"Found result: {result}")