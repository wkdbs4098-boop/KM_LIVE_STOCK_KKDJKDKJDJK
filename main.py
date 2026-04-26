import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import streamlit.components.v1 as components

# --- 텔레그램 설정 (수정본: 내 PC & 클라우드 공용) ---
try:
    # 1. 클라우드(Streamlit Cloud) 보안 설정 확인
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    # 2. 내 PC에서 실행할 때 (에러 방지용 직접 입력)
    # 아래 따옴표 안에 자윤님의 실제 토큰과 ID를 적어주세요.
    TELEGRAM_TOKEN = "" 
    TELEGRAM_CHAT_ID = ""

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def play_sound():
    sound_html = """
    <audio autoplay>
      <source src="https://raw.githubusercontent.com/carsonology/free-sound-effects/master/notifications/success.mp3" type="audio/mp3">
    </audio>
    """
    components.html(sound_html, height=0)

# --- 1. 설정 및 UI ---
st.set_page_config(page_title="자윤 Stock AI V3.5", layout="wide")
st.title("🚀 미국 전수조사: 백테스팅 & 실시간 감시 통합형")

# 자윤님의 조건
VOL_RATIO_THRESHOLD = 3
TAKE_PROFIT = 0.1
STOP_LOSS = 0.05
MIN_VALUE_THRESHOLD = 1000000 

@st.cache_data(ttl=86400)
def get_all_market_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        tickers = pd.read_csv(url, header=None)[0].tolist()
        return sorted(list(set([str(t).strip().upper() for t in tickers if str(t).isalpha()])))
    except:
        return ["AAPL", "TSLA", "NVDA", "AMD", "MSFT"]

ALL_TICKERS = get_all_market_tickers()

def get_safe_val(data):
    if isinstance(data, (pd.Series, pd.DataFrame)):
        val = data.iloc[-1]
        if isinstance(val, (pd.Series, pd.DataFrame)):
            return float(val.iloc[0])
        return float(val)
    return float(data)

def check_strategy(df, ticker):
    if df is None or len(df) < 21: return False, 0, 0
    try:
        curr_close = get_safe_val(df['Close'])
        curr_vol = get_safe_val(df['Volume'])
        
        vol_hist = df['Volume'].iloc[-6:-1]
        vol_avg = vol_hist.mean()
        if isinstance(vol_avg, pd.Series): vol_avg = vol_avg.iloc[0]
        
        if vol_avg == 0: return False, 0, 0
        vol_ratio = curr_vol / vol_avg
        curr_value = curr_close * curr_vol
        
        ma5 = get_safe_val(df['Close'].rolling(window=5).mean())
        ma20 = get_safe_val(df['Close'].rolling(window=20).mean())
        std20 = get_safe_val(df['Close'].rolling(window=20).std())
        upper_band = ma20 + (std20 * 2)

        c1 = vol_ratio >= VOL_RATIO_THRESHOLD
        c2 = curr_close > upper_band
        c3 = curr_close > ma5
        c4 = curr_value >= MIN_VALUE_THRESHOLD

        return (c1 and c2 and c3 and c4), vol_ratio, curr_value
    except: return False, 0, 0

# --- 3. 메인 로직 ---
st.sidebar.header("🕹️ 모드 전환")
app_mode = st.sidebar.selectbox("실행할 모드를 선택하세요", ["백테스팅 (과거 성적 확인)", "실시간 감시 (현재 시장 감시)"])

if app_mode == "백테스팅 (과거 성적 확인)":
    st.subheader("📊 2026년 1월 1일 ~ 현재 전수조사 리포트")
    
    col1, col2, col3 = st.columns(3)
    stat_total = col1.metric("총 포착", "0")
    stat_wins = col2.metric("익절 ✅", "0")
    stat_losses = col3.metric("손절 ❌", "0")
    
    live_status = st.empty()
    result_area = st.empty() 
    
    if st.button("🚀 전수조사 및 결과 추적 시작"):
        wins, losses = 0, 0
        hit_data = []

        for i, ticker in enumerate(ALL_TICKERS):
            live_status.info(f"🔍 분석 중: {ticker} ({i+1}/{len(ALL_TICKERS)})")
            try:
                df = yf.download(ticker, start="2025-12-01", progress=False, auto_adjust=False)
                if df.empty or len(df) < 21: continue

                start_idx = 0
                for idx, date in enumerate(df.index):
                    if date >= pd.Timestamp('2026-01-01'):
                        start_idx = idx
                        break
                
                actual_start = max(20, start_idx)

                for j in range(actual_start, len(df)):
                    sub_df = df.iloc[:j+1]
                    is_hit, v_ratio, v_val = check_strategy(sub_df, ticker)
                    
                    if is_hit:
                        entry_p = get_safe_val(df['Close'].iloc[[j]])
                        target_p, stop_p = entry_p * (1+TAKE_PROFIT), entry_p * (1-STOP_LOSS)
                        
                        res = "진행중"
                        for k in range(j+1, len(df)):
                            high_p = get_safe_val(df['High'].iloc[[k]])
                            low_p = get_safe_val(df['Low'].iloc[[k]])
                            if high_p >= target_p: 
                                wins += 1; res = "✅익절"; break
                            elif low_p <= stop_p: 
                                losses += 1; res = "❌손절"; break
                        
                        hit_data.append({
                            "포착일": df.index[j].strftime('%Y-%m-%d'),
                            "티커": ticker,
                            "거래량": f"{v_ratio:.1f}배",
                            "매수가": f"${entry_p:.2f}",
                            "결과": res
                        })
                        
                        # [오류수정] stretch를 "stretch" 문자열로 수정
                        result_area.dataframe(pd.DataFrame(hit_data), width="stretch", height=500)
                        
                        stat_total.metric("총 포착", len(hit_data))
                        stat_wins.metric("익절 ✅", wins)
                        stat_losses.metric("손절 ❌", losses)
                        
            except: continue
            
        st.success("🏁 조사가 완료되었습니다!")

elif app_mode == "실시간 감시 (현재 시장 감시)":
    st.subheader("📡 현재 미국 시장 실시간 포착")
    
    if 'already_sent' not in st.session_state:
        st.session_state.already_sent = set()

    mon_status = st.empty()
    mon_results = st.container()

    if st.button("📡 실시간 무한 감시 시작"):
        batch_size = 50 
        total_count = len(ALL_TICKERS)
        
        while True:
            current_time = datetime.now().strftime('%H:%M:%S')
            mon_status.warning(f"⏱️ {total_count}개 전 종목 스캔 중... (업데이트: {current_time})")
            
            for i in range(0, total_count, batch_size):
                batch_tickers = ALL_TICKERS[i:i+batch_size]
                try:
                    df_all = yf.download(batch_tickers, period="1d", interval="1m", progress=False, group_by='ticker', prepost=True)
                    
                    for ticker in batch_tickers:
                        df_live = df_all[ticker] if len(batch_tickers) > 1 else df_all
                        if df_live.empty or len(df_live) < 21: continue
                        
                        is_hit, v_ratio, _ = check_strategy(df_live, ticker)
                        
                        if is_hit and ticker not in st.session_state.already_sent:
                            with mon_results:
                                st.success(f"🎯 **{ticker}** 포착! | 거래량: {v_ratio:.1f}배 | {current_time}")
                                st.toast(f"{ticker} 포착!", icon="🔥")
                            
                            play_sound()
                            msg = f"🚀 [포착] {ticker}\n거래량: {v_ratio:.1f}배\n시간: {current_time}"
                            send_telegram_msg(msg)
                            st.session_state.already_sent.add(ticker)
                            
                except: continue
            
            time.sleep(60)
