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

tickers = {
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

st.title("📈 米国株価 可視化ダッシュボード")

st.caption(
    "主要米国企業の株価をインタラクティブに比較・分析できます。"
)

st.sidebar.header("⚙️ 表示設定")

st.sidebar.markdown("**📅 期間**")
days = st.sidebar.slider('日数', 5, 180, 90)

st.sidebar.divider()

relative = st.sidebar.checkbox(
    "相対表示",
    value=False
)
st.sidebar.caption(
    "共通開始日を100とし、欠損銘柄は初値を100とします"
)
st.sidebar.divider()

st.sidebar.subheader("📊 株価範囲")
auto_scale = st.sidebar.checkbox("Y軸を自動スケール", value=True)

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

st.write(f"""
    ### 過去 **{days}** 日間の米主要銘柄の株価
""")
   
try:
    df = get_data(days, tickers)

    label_to_key = {v['label']: k for k, v in tickers.items()}

    selected_labels = st.multiselect(
        '会社名を選択してください',
        options=label_to_key.keys(),
        default=['Apple', 'Amazon', 'Microsoft', 'Google', 'Meta']
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
    
        y_title = "相対株価（開始日=100）" if relative else "株価（USD）"

        data_chart = data_chart.reset_index(names='Date')

        data_table['Date'] = pd.to_datetime(data_table['Date'])
        data_chart['Date'] = pd.to_datetime(data_chart['Date'])

        data_chart = pd.melt(
            data_chart,
            id_vars='Date',
            var_name='Name',
            value_name='price_usd'
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
                    "price_usd:Q", 
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
                    alt.Tooltip("price_usd:Q", title="株価", format=".2f"),
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
    