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

MAIN_SPREADSHEET_ID = "1lx_MZivY0Bzdevh3w86Xq8gB5R99b4R0niR0YySx734"

DATA_SPREADSHEET_ID = "12fr6cSz-oLIx7nm-32yeml2RSMhwEnfwLqgCKASiE9Q"

# =========================================
# スプレッドシートURL
# =========================================

MAIN_SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1lx_MZivY0Bzdevh3w86Xq8gB5R99b4R0niR0YySx734/edit#gid=0"
)

DATA_SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "12fr6cSz-oLIx7nm-32yeml2RSMhwEnfwLqgCKASiE9Q/edit#gid=0"
)

# =========================================
# シート名
# =========================================

MAIN_SHEET_NAME = "シート1"

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

    if sheet is not None:

        data = sheet.get_all_records()

        if data:
            return pd.DataFrame(data)

    return pd.DataFrame()

# =========================================
# 機種一覧取得
# =========================================

def get_machine_list():

    url = "https://www.p-world.co.jp/fukuoka/maruhan-hakozaki.htm"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "lxml")

    text = soup.get_text("\n")

    machines = []

    keywords = [
        "スマスロ",
        "パチスロ",
        "ジャグラー",
        "北斗",
        "番長",
        "バイオ",
        "カバネリ",
        "モンハン",
        "ハイパーラッシュ"
    ]

    ng_words = [
        "ぱちんこ",
        "P ",
        "e ",
        "LT"
    ]

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        skip = False

        for ng in ng_words:

            if ng in line:
                skip = True
                break

        if skip:
            continue

        for keyword in keywords:

            if keyword in line:
                machines.append(line)
                break

    return sorted(list(set(machines)))

# =========================================
# サイドバー
# =========================================

with st.sidebar:

    st.header("🎰 設定推測")

    target_model = st.selectbox(
        "機種を選択",
        ["選択なし"] + sorted(list(SPEC_DATA.keys()))
    )

    kaiten = st.number_input(
        "総回転数",
        min_value=1,
        value=1000
    )

    col1, col2 = st.columns(2)

    with col1:
        s_big = st.number_input("BIG回数", min_value=0)

    with col2:
        s_reg = st.number_input("REG回数", min_value=0)

    if (s_big + s_reg) > 0:

        gassan = kaiten / (s_big + s_reg)

        st.write(f"現在の合算: 1/{gassan:.1f}")

        if target_model != "選択なし":

            specs = SPEC_DATA[target_model]

            best_diff = 999
            likely_setting = 1

            for i, val in enumerate(specs):

                if val == 0:
                    continue

                diff = abs(gassan - val)

                if diff < best_diff:

                    best_diff = diff
                    likely_setting = i + 1

            st.success(f"推定設定: 設定{likely_setting}")

# =========================================
# タイトル
# =========================================

st.title("🎰 5.5スロ分析ツール")

# =========================================
# スプレッドシートリンク
# =========================================

st.markdown("### 📄 スプレッドシート")

col_link1, col_link2 = st.columns(2)

with col_link1:

    st.link_button(
        "📊 収支表を開く",
        MAIN_SPREADSHEET_URL,
        use_container_width=True
    )

with col_link2:

    st.link_button(
        "🗂️ データ集積シートを開く",
        DATA_SPREADSHEET_URL,
        use_container_width=True
    )

# =========================================
# 機種一覧取得
# =========================================

st.divider()

st.subheader("🏪 マルハン箱崎店 機種一覧")

if st.button("機種一覧取得"):

    try:

        machine_list = get_machine_list()

        if machine_list:

            st.success(f"{len(machine_list)}件取得")

            for machine in machine_list:
                st.write(machine)

        else:

            st.warning("取得失敗")

    except Exception as e:

        st.error(f"取得エラー: {e}")

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
        use_container_width=True,
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
                history_df["差枚"].cumsum()
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

            st.dataframe(
                result,
                use_container_width=True
            )

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

            st.dataframe(
                result,
                use_container_width=True
            )

except Exception as e:

    st.error(f"台別分析エラー: {e}")