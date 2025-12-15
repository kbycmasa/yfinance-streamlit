import pandas as pd 
import streamlit as st
import altair as alt
import yfinance as yf

st.set_page_config(
    page_title="株価可視化ダッシュボード",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

STOCK_TICKERS = {
    'apple':        {'symbol': 'AAPL',  'label': 'Apple'},
    'microsoft':    {'symbol': 'MSFT',  'label': 'Microsoft'},
    'amazon':       {'symbol': 'AMZN',  'label': 'Amazon'},
    'google':       {'symbol': 'GOOGL', 'label': 'Google'},
    'nvidia':       {'symbol': 'NVDA',  'label': 'NVIDIA'},
    'meta':         {'symbol': 'META',  'label': 'Meta'},
    'tesla':        {'symbol': 'TSLA',  'label': 'Tesla'},
    'micron':       {'symbol': 'MU',    'label': 'Micron'},
    'visa':         {'symbol': 'V',     'label': 'Visa'},
    'exxonmobil':   {'symbol': 'XOM',   'label': 'Exxon Mobil'},
    'disney':       {'symbol': 'DIS',   'label': 'Disney'},
    'comcast':      {'symbol': 'CMCSA','label': 'Comcast'},
    'bristolmyers': {'symbol': 'BMY',   'label': 'Bristol Myers Squibb'},
    'raytheon':     {'symbol': 'RTX',   'label': 'RTX'},
}
COMMODITY_TICKERS = {
    # 貴金属
    "gold":        {"symbol": "GC=F", "label": "Gold"},
    "silver":      {"symbol": "SI=F", "label": "Silver"},
    "platinum":    {"symbol": "PL=F", "label": "Platinum"},
    "palladium":   {"symbol": "PA=F", "label": "Palladium"},

    # エネルギー
    "crude_oil":   {"symbol": "CL=F", "label": "WTI Crude Oil"},
    "brent":       {"symbol": "BZ=F", "label": "Brent Crude"},
    "natural_gas": {"symbol": "NG=F", "label": "Natural Gas"},
    "gasoline":    {"symbol": "RB=F", "label": "Gasoline"},
    "heating_oil": {"symbol": "HO=F", "label": "Heating Oil"},

    # 農産物
    "corn":        {"symbol": "ZC=F", "label": "Corn"},
    "wheat":       {"symbol": "ZW=F", "label": "Wheat"},
    "soybeans":    {"symbol": "ZS=F", "label": "Soybeans"},
    "soy_oil":     {"symbol": "ZL=F", "label": "Soybean Oil"},
    "soy_meal":    {"symbol": "ZM=F", "label": "Soybean Meal"},

    # ソフトコモディティ
    "coffee":      {"symbol": "KC=F", "label": "Coffee"},
    "sugar":       {"symbol": "SB=F", "label": "Sugar"},
    "cotton":      {"symbol": "CT=F", "label": "Cotton"},
    "cocoa":       {"symbol": "CC=F", "label": "Cocoa"},
}

st.sidebar.header("🧭 表示モード")
view_mode = st.sidebar.radio(
    "表示対象",
    ["株式", "コモディティ"],
    horizontal=False
)
if view_mode == "株式":
    tickers = STOCK_TICKERS
    title_suffix = "米国株"

    days_min = 5
    days_max = 180
    days_default = 90
    relative_default = False 
else:
    tickers = COMMODITY_TICKERS
    title_suffix = "コモディティ"

    days_min = 5
    days_max = 900
    days_default = 180
    relative_default = True
    
st.title(f"📈 {title_suffix} 可視化ダッシュボード")
st.caption(
    f"主要{title_suffix}をインタラクティブに比較・分析できます。"
)

st.sidebar.header("📅 期間・表示設定")
days = st.sidebar.slider(
    "表示期間（日）",
    days_min,
    days_max,
    days_default
)

relative = st.sidebar.checkbox(
    "相対表示（開始日=100）",
    value=relative_default
)
if view_mode == "コモディティ":
    st.sidebar.caption("※ コモディティは相対表示が基本です")
    
st.sidebar.divider()

st.sidebar.header("📊 表示スケール")
auto_scale = st.sidebar.checkbox(
    "Y軸を自動調整",
    value=True
)

@st.cache_data(ttl=3600)
def fetch_close(symbol: str, days: int) -> pd.Series:
    tkr = yf.Ticker(symbol)
    hist = tkr.history(period=f"{days}d")[['Close']]
    return hist['Close']

def get_data(days, tickers):
    df = pd.DataFrame()
    for key, info in tickers.items():
        close = fetch_close(info['symbol'], days)
        df[key] = close
    return df

if auto_scale:
    y_scale = alt.Scale(zero=False, nice=False, padding=40)
else:
    st.sidebar.write("""
        ## 株価の範囲指定
    """)
    ymin, ymax = st.sidebar.slider(
        'Y軸の範囲',
        0.0, 1000.0, (80.0, 620.0)
    )
    y_scale = alt.Scale(domain=[ymin, ymax])

st.write(f"### 過去 **{days}** 日間の {title_suffix} の推移")
   
try:
    df = get_data(days, tickers)

    label_to_key = {v['label']: k for k, v in tickers.items()}

    selected_labels = st.multiselect(
        '銘柄を選択してください',
        options=label_to_key.keys(),
        default=list(label_to_key.keys())[:5]
    )
    selected_keys = [label_to_key[label] for label in selected_labels]

    if not selected_labels:
        st.error('少なくとも一社は選択してください。')
    else:
        data_chart = df[selected_keys].copy()
        data_table = df[selected_keys].reset_index().rename(columns={'index': 'Date'})
        st.write("#### 株価チャート")
        
        if relative:
            # 各銘柄ごとに最初の値を100に正規化
            base_date = data_chart.index.min()

            def normalize(s):
                if pd.notna(s.loc[base_date]):
                    base = s.loc[base_date]
                else:
                    base = s.dropna().iloc[0]
                return s / base * 100

            data_chart = data_chart.apply(normalize)
    
        if view_mode == "コモディティ":
            y_title = "相対価格（開始日=100）" if relative else "価格（単位は銘柄ごと）"
        else:
            y_title = "相対株価（開始日=100）" if relative else "株価（USD）"

        price_label = "価格" if view_mode == "コモディティ" else "株価"

        data_chart = data_chart.reset_index(names='Date')

        data_table['Date'] = pd.to_datetime(data_table['Date'])
        data_chart['Date'] = pd.to_datetime(data_chart['Date'])

        data_chart = pd.melt(
            data_chart,
            id_vars='Date',
            var_name='Name',
            value_name='price'
        )

        data_chart['Name'] = data_chart['Name'].map(
            {k: v['label'] for k, v in tickers.items()}
        )

        chart = (
            alt.Chart(data_chart)
            .mark_line(
                interpolate="monotone",
                strokeWidth=2,
                opacity=0.9,
                clip=True
            )
            .encode(
                x=alt.X(
                    "Date:T",
                    title="日付",
                    axis=alt.Axis(format="%Y-%m-%d", labelAngle=-45)
                ),
                y=alt.Y(
                    "price:Q", 
                    title=y_title,
                    stack=None,
                    scale=y_scale
                ),                
                color=alt.Color(
                    "Name:N",
                    legend=alt.Legend(title="企業名")
                ),
                tooltip=[
                    alt.Tooltip("Date:T", title="日付"),
                    alt.Tooltip("Name:N", title="企業"),
                    alt.Tooltip("price:Q", title=price_label, format=".2f"),
                ]
            )
            .properties(height=420)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True) 

        st.write("#### 終値データ")
        st.dataframe(
            data_table
                .sort_values('Date')
                .assign(Date=lambda df: df['Date'].dt.strftime('%Y-%m-%d')),
            height=280,
            use_container_width=True
        )
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    