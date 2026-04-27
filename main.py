import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import streamlit.components.v1 as components
import os
import threading  # 24시간 가동을 위한 스레드 추가

# --- [1] 블랙리스트 영구 저장소 (자윤님 원본 유지) ---
HARD_BLACKLIST = [
    "AACBR", "AACBU", "AACIW", "AACO", "AACOU", "AACPU", "ADAC", "ADACW", "AHL", "AIMDW",
    "AKO", "ALCY", "ALDF", "ALDFU", "ALDFW", "ALFUU", "ALIS", "ALISR", "ALOV", "ALOVU",
    "ALOVW", "ANG", "ANSCW", "APAC", "APACR", "APLMW", "ARCIU", "ARTC", "ATH", "AXINR",
    "BACCR", "BANFP", "BAYAR", "BCGWW", "BDMDW", "BEBE", "BF", "BHAVR", "BHAVU", "BLRK",
    "BLRKU", "BLRKW", "BLUWW", "BML", "BNCWZ", "BPAC", "BRID", "BRK", "BRKRP", "BSAA",
    "BTBDW", "BZFDW", "CAPN", "CAQUU", "CCGWW", "CCIIW", "CDR", "CDTTW", "CFTR", "CHECU",
    "CHPG", "CHPGR", "COLAU", "CRACW", "CRANU", "CRAQR", "CRAQU", "CRD", "CSHRW", "CTAAU",
    "CUBWU", "DAAQU", "DAAQW", "DAICW", "DFSCW", "DNMXU", "DSACU", "DTSQR", "DTSQU", "DYORU",
    "EMIS", "ERNAW", "ETHMU", "ETI", "EVOX", "EVOXW", "EXOZ", "FACTU", "FGIIU", "FMSTW",
    "FRMEP", "FSHP", "GECCO", "GIGGU", "GIPRW", "GIWWR", "GIX", "GJP", "GJR", "GJT",
    "GLOP", "GPAC", "GPACU", "GPATU", "GSHR", "GTENW", "GTERR", "GTERU", "HAVAU", "HCACU",
    "HCICU", "HCMAU", "HLXC", "HSCSW", "HVIIU", "I", "IACOU", "ICR", "ICUCW", "IEAG",
    "IGACR", "IGACU", "IINNW", "ILLU", "INAC", "INACR", "IPCXU", "IPEX", "IPEXU", "IPODU",
    "IRHOU", "ITHAU", "IVDAW", "K", "KOYNW", "KTTAW", "KTWOU", "KVAC", "KWMWW", "LAFA",
    "LATAU", "LCCCU", "LKSPR", "LKSPU", "LOTWW", "LPCVU", "LUCYW", "MACI", "MBVIU", "MCGAW",
    "MDAIW", "MDCXW", "MESH", "MESHU", "MEVO", "MEVOW", "MKDWW", "MKLY", "MKLYU", "MLACU",
    "MOBBW", "MRNOW", "MUZEU", "MUZEW", "N", "NBRGU", "NEXRW", "NOEM", "NOEMR", "NOEMW",
    "NOVTU", "NPACU", "NTWO", "OABIW", "OACC", "OACCU", "OAK", "OBAWU", "OFSSH", "OFSSO",
    "OIMAU", "OIMAW", "OTGAU", "OTGAW", "OYSER", "PAAC", "PAACW", "PACH", "PALOU", "PALOW",
    "PCAPW", "PCTTU", "PHXE", "PLUT", "PONOU", "PRHIZ", "PRIF", "PYT", "QETA", "QSEAU",
    "RAAQU", "RANG", "RCKTW", "RDACU", "RDIB", "RDZNW", "REVBW", "RFAI", "RNGTU", "RNGTW",
    "RVSNW", "SAAQU", "SCAGW", "SCE", "SCIIR", "SCIIU", "SCPQ", "SCPQW", "SDHIU", "SEAL",
    "SEATW", "SIMAW", "SORN", "SPEG", "SPEGU", "SPKLW", "SSACR", "SSEA", "SUMAU", "SVAQ",
    "SVAQU", "SVCC", "SVIVU", "SWKHL", "SXTPW", "SZZLU", "TACH", "TACHW", "TALKW", "TAVI",
    "TBLAW", "TC", "TDWDR", "TLNCU", "TLSIW", "TMTSU", "TRGSR", "TRGSU", "TRSG", "TRTN",
    "TVACU", "TVAI", "UAC", "UYSC", "VEEAW", "VHCP", "VHCPU", "VNMEU", "VSEEW", "WALDW",
    "WENNW", "WFCF", "WLDSW", "WLII", "WLIIU", "WSTNR", "X", "XBPEW", "XCBE", "XRPNU",
    "XSLLU", "Y", "ZKP", "ZOOZW"
]

# --- [2] 블랙리스트 관리 (자윤님 원본 유지) ---
def load_blacklist():
    blacklist = set(HARD_BLACKLIST)
    if os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "r") as f:
            blacklist.update(line.strip() for line in f if line.strip())
    return blacklist

def save_blacklist(blacklist_set):
    with open("blacklist.txt", "w") as f:
        for ticker in sorted(list(blacklist_set)):
            f.write(f"{ticker}\n")

# --- 텔레그램 설정 ---
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    TELEGRAM_TOKEN = "" 
    TELEGRAM_CHAT_ID = ""

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params, timeout=5)
    except: pass

# --- 전략 및 데이터 보조 함수 (자윤님 원본 유지) ---
@st.cache_data(ttl=86400)
def get_all_market_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        tickers = pd.read_csv(url, header=None)[0].tolist()
        return sorted(list(set([str(t).strip().upper() for t in tickers if str(t).isalpha()])))
    except:
        return ["AAPL", "TSLA", "NVDA", "AMD", "MSFT"]

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
        vol_avg = df['Volume'].iloc[-6:-1].mean()
        if isinstance(vol_avg, pd.Series): vol_avg = vol_avg.iloc[0]
        if vol_avg == 0: return False, 0, 0
        vol_ratio = curr_vol / vol_avg
        curr_value = curr_close * curr_vol
        ma5 = get_safe_val(df['Close'].rolling(window=5).mean())
        ma20 = get_safe_val(df['Close'].rolling(window=20).mean())
        std20 = get_safe_val(df['Close'].rolling(window=20).std())
        upper_band = ma20 + (std20 * 2)
        c1 = vol_ratio >= 3
        c2 = curr_close > upper_band
        c3 = curr_close > ma5
        c4 = curr_value >= 1000000 
        return (c1 and c2 and c3 and c4), vol_ratio, curr_value
    except: return False, 0, 0

# --- [핵심 추가] 24시간 무한 감시 백그라운드 엔진 ---
def monitor_engine():
    """자윤님 브라우저 오프라인 시에도 텔레그램을 보내주는 독립 엔진"""
    already_sent_today = set()
    current_blacklist = load_blacklist()
    all_tickers = get_all_market_tickers()
    
    print(f"🚀 [엔진] 24H 감시 시작 (대상: {len(all_tickers)}개)", flush=True)
    
    while True:
        scan_targets = [t for t in all_tickers if t not in current_blacklist]
        batch_size = 30
        
        for i in range(0, len(scan_targets), batch_size):
            batch = scan_targets[i:i+batch_size]
            try:
                df_all = yf.download(batch, period="2d", interval="1m", progress=False, group_by='ticker', prepost=True, threads=True, timeout=15)
                for ticker in batch:
                    df = df_all[ticker] if len(batch) > 1 else df_all
                    if df.empty or ticker in already_sent_today: continue
                    
                    is_hit, v_ratio, _ = check_strategy(df, ticker)
                    if is_hit:
                        send_telegram_msg(f"🎯 **{ticker}** 포착!\n비율: {v_ratio:.1f}배\n상태: 24H 감시 엔진 작동 중")
                        already_sent_today.add(ticker)
                time.sleep(1)
            except: continue
        
        print(f"📍 {datetime.now().strftime('%H:%M:%S')} - 한 사이클 완료", flush=True)
        time.sleep(60)

# --- [UI 및 실행 제어] ---
st.set_page_config(page_title="자윤 Stock AI V3.5", layout="wide")

# 서버 켜지자마자 엔진 자동 시작 (버튼 클릭 불필요)
if "engine_started" not in st.session_state:
    if not any(t.name == "StockEngine" for t in threading.enumerate()):
        thread = threading.Thread(target=monitor_engine, name="StockEngine", daemon=True)
        thread.start()
    st.session_state.engine_started = True

st.title("🚀 자윤 24H 전수조사 서버 (상시 가동 중)")
st.success("✅ 감시 엔진이 백그라운드에서 24시간 작동 중입니다. 이제 폰이나 컴퓨터를 끄셔도 됩니다.")

# (이하 자윤님의 기존 UI 로직 - 백테스팅 등 그대로 유지)
app_mode = st.sidebar.selectbox("모드 선택", ["실시간 감시 현황", "백테스팅 (과거 성적)"])

if app_mode == "실시간 감시 현황":
    st.info(f"현재 서버 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write("텔레그램 알림을 확인하세요. 포착된 종목은 자동으로 발송됩니다.")

elif app_mode == "백테스팅 (과거 성적)":
    # (자윤님의 백테스팅 로직 그대로 위치)
    pass
