import streamlit as st
import pandas as pd
import gspread
import requests

from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# =========================================
# Streamlit設定
# =========================================

st.set_page_config(
    page_title="5.5スロ分析ツール",
    layout="wide"
)

# =========================================
# CSS
# =========================================

st.markdown("""
<style>

.stApp {
    background-color: black;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: black;
}

h1, h2, h3, p, label {
    color: white !important;
}

div.stButton > button {
    background-color: #0000ff !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
}

div[data-testid="stFormSubmitButton"] button {
    background-color: #0000ff !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================
# スプレッドシートID
# =========================================

DATA_SPREADSHEET_ID = "12fr6cSz-oLIx7nm-32yeml2RSMhwEnfwLqgCKASiE9Q"

# =========================================
# シート名
# =========================================

DATA_ALL_SHEET = "全履歴"

# =========================================
# 台別シートマッピング
# =========================================

SHEET_MAPPING = {

    ("ハイパーラッシュ", "622"): "ハイパーラッシュ622",
    ("ハイパーラッシュ", "623"): "ハイパーラッシュ623",

    ("カバネリ", "625"): "カバネリ625",
    ("カバネリ", "626"): "カバネリ626",
    ("カバネリ", "627"): "カバネリ627",
    ("カバネリ", "629"): "カバネリ629",
    ("カバネリ", "630"): "カバネリ630",
}

# =========================================
# 設定推測データ
# =========================================

SPEC_DATA = {

    "ミスタージャグラー": [163.8, 159.1, 153.8, 142.5, 131.6, 118.7],
    "アイムジャグラーEX": [168.5, 159.1, 150.3, 140.9, 135.4, 127.5],
    "マイジャグラーV": [163.8, 159.1, 155.3, 144.0, 135.4, 114.6],
    "ファンキージャグラー2": [165.1, 158.3, 145.3, 133.7, 126.3, 119.6],
    "ゴーゴージャグラー3": [149.6, 146.3, 140.3, 135.4, 126.8, 117.3],
    "ハイパーラッシュ": [173.8, 172.5, 170.2, 161.8, 151.7, 142.5],
    "新ハナビR": [156.0, 149.6, 0, 140.9, 134.8, 131.1],
    "ディスクアップ2": [182.0, 180.2, 0, 171.1, 161.0, 149.3],
    "ファミスタ回胴版！！": [182.0, 179.6, 0, 171.1, 161.8, 150.3],
    "北斗の拳": [383.4, 370.5, 347.1, 297.8, 258.7, 235.1],
    "押忍！番長4": [259.5, 256.3, 247.0, 227.0, 203.4, 198.8],
    "聖闘士星矢 海皇覚醒ED": [363.3, 353.5, 335.7, 303.4, 275.9, 244.6],
    "ToLOVEるダークネス": [355.3, 344.9, 321.7, 280.9, 255.4, 230.1],
    "革命機ヴァルヴレイヴD": [519.0, 516.0, 490.0, 434.0, 414.0, 401.0],
    "モンスターハンターライズ": [309.8, 297.4, 281.3, 253.9, 233.1, 212.0],
    "からくりサーカスG": [564.0, 543.0, 514.0, 469.0, 436.0, 409.0],
    "炎炎ノ消防隊": [243.2, 233.7, 223.5, 201.7, 188.0, 173.8],
    "ソードアート・オンラインB2": [412.2, 396.1, 375.0, 319.4, 286.0, 247.9],
    "エウレカセブンHIEVO": [195.4, 191.0, 182.2, 169.1, 158.4, 143.7],
    "ラブ嬢3M4": [252.3, 246.5, 235.1, 218.4, 198.8, 178.2],
    "バジリスク絆2～天膳～": [247.3, 239.9, 230.1, 206.8, 187.3, 170.3],
    "GI優駿倶楽部黄金KD": [336.8, 328.7, 313.1, 276.4, 252.1, 219.6],
    "キングパルサーSLCC": [151.0, 147.2, 144.5, 137.9, 131.7, 121.7],
    "ストライク・ザ・ブラッドZC": [199.1, 195.1, 186.2, 167.3, 150.3, 133.4],
    "戦姫絶唱シンフォギア 正義の歌": [295.0, 290.1, 281.4, 253.3, 234.3, 201.2],
    "防振り": [319.4, 307.7, 289.4, 244.6, 221.7, 199.0],
    "スマスロ真北斗無双": [381.1, 372.4, 355.6, 310.3, 279.1, 248.3],
    "ゾンビランドサガA1": [164.5, 161.4, 157.0, 145.4, 133.3, 118.5],
    "スマスロ頭文字D2nd": [317.0, 311.2, 294.6, 258.8, 235.2, 207.2],
    "バンドリS11": [332.3, 324.9, 311.6, 283.6, 257.7, 224.2],
    "鬼武者3XA": [319.3, 311.1, 298.5, 272.5, 244.1, 212.1],
    "スマスロ 聖戦士ダンバイン": [342.3, 335.7, 321.4, 288.6, 256.4, 219.3],
    "ありふれた職業で世界最強": [321.1, 310.5, 292.3, 256.4, 233.1, 201.9],
    "シン・エヴァンゲリオン": [345.5, 334.3, 312.2, 274.5, 253.1, 221.0],
    "SHAMAN KING": [182.0, 178.5, 172.3, 155.4, 140.1, 125.5],
    "スマスロカイジ 狂宴": [315.4, 308.2, 291.5, 266.4, 231.0, 199.5],
    "ヨシムネS": [250.6, 243.2, 222.1, 201.4, 185.3, 166.2],
    "麻雀物語S2": [255.4, 248.1, 231.5, 201.3, 182.1, 163.4],
    "東京リベンジャーズ": [342.0, 334.0, 321.0, 289.0, 254.0, 218.0],
    "咲-Saki-頂上決戦YR": [224.4, 215.1, 201.2, 188.4, 175.2, 160.1],
    "いろはに愛姫PA5": [158.3, 158.3, 158.3, 0, 0, 149.3],
    "HEY！エリートサラリーマン鏡PA4": [273.1, 263.5, 251.0, 222.8, 193.0, 183.0],
    "スマスロ押忍！番長ZERO": [245.4, 237.4, 224.2, 203.1, 183.5, 169.5],
    "バイオハザード5ZE": [310.0, 295.0, 281.0, 252.0, 226.0, 193.0],
    "ルパン三世大航海者の秘宝": [188.3, 183.1, 176.2, 163.8, 149.6, 131.6],
    "ドルアーガの塔": [209.0, 198.0, 181.0, 163.0, 150.0, 135.0],
}

# =========================================
# Google Sheets接続
# =========================================

@st.cache_resource
def get_gspread_client():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )

    client = gspread.authorize(creds)

    return client

# =========================================
# シート取得
# =========================================

@st.cache_resource
def get_spreadsheet(spreadsheet_id, sheet_name):

    try:

        client = get_gspread_client()

        spreadsheet = client.open_by_key(spreadsheet_id)

        worksheet = spreadsheet.worksheet(sheet_name)

        return worksheet

    except Exception as e:

        st.error(f"シート取得エラー: {e}")

        return None

# =========================================
# 収支読み込み
# =========================================

def load_shuushi():

    sheet = get_spreadsheet(
        DATA_SPREADSHEET_ID,
        DATA_ALL_SHEET
    )

    if sheet:

        data = sheet.get_all_records()

        if data:
            return pd.DataFrame(data)

    return pd.DataFrame()

# =========================================
# タイトル
# =========================================

st.title("🎰 5.5スロ分析ツール")

# =========================================
# 台データ入力
# =========================================

st.divider()

with st.form("slot_form", clear_on_submit=True):

    st.subheader("🎰 台データ入力")

    shop = st.selectbox(
        "店舗",
        [
            "マルハン箱崎店",
            "ワンダーランド",
            "EVO37"
        ]
    )

    col1, col2 = st.columns(2)

    with col1:

        machine = st.selectbox(
            "機種名",
            sorted(list(SPEC_DATA.keys()))
        )

    with col2:

        dai = st.number_input(
            "台番号",
            min_value=1,
            step=1
        )

    col3, col4, col5 = st.columns(3)

    with col3:

        game = st.number_input(
            "総回転",
            min_value=0
        )

    with col4:

        big = st.number_input(
            "BIG",
            min_value=0
        )

    with col5:

        reg = st.number_input(
            "REG",
            min_value=0
        )

    diff = st.number_input(
        "差枚",
        step=100
    )

    memo = st.text_area("メモ")

    submit = st.form_submit_button("記録する")

    if submit:

        total_bonus = big + reg

        if total_bonus > 0:
            gassan = round(game / total_bonus, 1)
        else:
            gassan = 0

        row = [
            datetime.now().strftime("%Y/%m/%d %H:%M"),
            shop,
            machine,
            str(dai),
            game,
            big,
            reg,
            diff,
            gassan,
            memo
        ]

        main_sheet = get_spreadsheet(
            DATA_SPREADSHEET_ID,
            DATA_ALL_SHEET
        )

        if main_sheet:

            main_sheet.append_row(row)

        key = (machine, str(dai))

        if key in SHEET_MAPPING:

            target_sheet_name = SHEET_MAPPING[key]

            target_sheet = get_spreadsheet(
                DATA_SPREADSHEET_ID,
                target_sheet_name
            )

            if target_sheet:

                target_sheet.append_row(row)

        st.success("保存しました！")

        st.rerun()

# =========================================
# 収支履歴
# =========================================

st.divider()

st.subheader("📊 収支履歴")

df = load_shuushi()

if not df.empty:

    st.dataframe(
        df.iloc[::-1],
        width="stretch",
        hide_index=True
    )

else:

    st.info("データなし")

# =========================================
# 累計差枚グラフ
# =========================================

st.divider()

st.subheader("📈 累計差枚グラフ")

try:

    history_sheet = get_spreadsheet(
        DATA_SPREADSHEET_ID,
        DATA_ALL_SHEET
    )

    if history_sheet is not None:

        history_data = history_sheet.get_all_records()

        history_df = pd.DataFrame(history_data)

        if not history_df.empty:

            history_df.columns = (
                history_df.columns.str.strip()
            )

            history_df["差枚"] = pd.to_numeric(
                history_df["差枚"],
                errors="coerce"
            ).fillna(0)

            history_df["累計差枚"] = (
                history_df["差枚"]
                .cumsum()
            )

            st.line_chart(
                history_df["累計差枚"]
            )

except Exception as e:

    st.error(f"グラフエラー: {e}")

# =========================================
# 機種別分析
# =========================================

st.divider()

st.subheader("🎰 機種別分析")

try:

    machine_sheet = get_spreadsheet(
        DATA_SPREADSHEET_ID,
        DATA_ALL_SHEET
    )

    if machine_sheet is not None:

        machine_data = machine_sheet.get_all_records()

        machine_df = pd.DataFrame(machine_data)

        if not machine_df.empty:

            machine_df.columns = (
                machine_df.columns.str.strip()
            )

            machine_df["差枚"] = pd.to_numeric(
                machine_df["差枚"],
                errors="coerce"
            ).fillna(0)

            result = (
                machine_df
                .groupby("機種")["差枚"]
                .sum()
                .sort_values(ascending=False)
            )

            st.dataframe(result)

except Exception as e:

    st.error(f"機種別分析エラー: {e}")

# =========================================
# 台番号別分析
# =========================================

st.divider()

st.subheader("🔢 台番号別分析")

try:

    dai_sheet = get_spreadsheet(
        DATA_SPREADSHEET_ID,
        DATA_ALL_SHEET
    )

    if dai_sheet is not None:

        dai_data = dai_sheet.get_all_records()

        dai_df = pd.DataFrame(dai_data)

        if not dai_df.empty:

            dai_df.columns = (
                dai_df.columns.str.strip()
            )

            dai_df["差枚"] = pd.to_numeric(
                dai_df["差枚"],
                errors="coerce"
            ).fillna(0)

            result = (
                dai_df
                .groupby("台番号")["差枚"]
                .sum()
                .sort_values(ascending=False)
            )

            st.dataframe(result)

except Exception as e:

    st.error(f"台別分析エラー: {e}")