import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import os
import threading

print("🔥 서버 엔진 가동 테스트 시작!", flush=True)

# --- [1] 블랙리스트 (자윤님의 기존 데이터 100% 유지) ---
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

# --- [2] 텔레그램 보안 설정 ---
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("Secrets 설정(TOKEN, CHAT_ID)이 누락되었습니다!")
    st.stop()

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params, timeout=5)
    except: pass

def get_safe_val(data):
    if isinstance(data, (pd.Series, pd.DataFrame)):
        val = data.iloc[-1]
        return float(val.iloc[0]) if isinstance(val, (pd.Series, pd.DataFrame)) else float(val)
    return float(data)

# --- [3] 자윤님 원본 전략 조건 (100% 복구) ---
def check_strategy(df):
    if df is None or len(df) < 21: return False, 0
    try:
        curr_close = get_safe_val(df['Close'])
        curr_vol = get_safe_val(df['Volume'])
        vol_avg = df['Volume'].iloc[-6:-1].mean()
        if isinstance(vol_avg, pd.Series): vol_avg = vol_avg.iloc[0]
        if vol_avg == 0: return False, 0
        
        vol_ratio = curr_vol / vol_avg
        curr_value = curr_close * curr_vol
        
        # 보조지표
        ma5 = get_safe_val(df['Close'].rolling(window=5).mean())
        ma20 = get_safe_val(df['Close'].rolling(window=20).mean())
        std20 = get_safe_val(df['Close'].rolling(window=20).std())
        upper_band = ma20 + (std20 * 2)
        
        # 필터링
        c1 = vol_ratio >= 3             # 거래량 폭발
        c2 = curr_close > upper_band    # 볼밴 상단 돌파
        c3 = curr_close > ma5           # 5일선 위
        c4 = curr_value >= 1000000      # 100만불 이상
        
        if c1 and c2 and c3 and c4:
            return True, vol_ratio
        return False, 0
    except: return False, 0

# --- [4] 백그라운드 무한 엔진 ---
def monitor_engine():
    already_sent = set()
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        all_tickers = pd.read_csv(url, header=None)[0].tolist()
        all_tickers = sorted(list(set([str(t).strip().upper() for t in all_tickers if str(t).isalpha()])))
    except: all_tickers = ["AAPL", "TSLA", "NVDA"]

    send_telegram_msg("🚀 [알림] 자윤님 전략 24H 감시 엔진이 정상적으로 시작되었습니다.")
    
    while True:
        scan_targets = [t for t in all_tickers if t not in HARD_BLACKLIST]
        batch_size = 20
        for i in range(0, len(scan_targets), batch_size):
            batch = scan_targets[i:i+batch_size]
            try:
                df_all = yf.download(batch, period="2d", interval="1m", progress=False, group_by='ticker', prepost=True, threads=True, timeout=15)
                for ticker in batch:
                    df = df_all[ticker] if len(batch) > 1 else df_all
                    if df.empty or ticker in already_sent: continue
                    is_hit, v_ratio = check_strategy(df)
                    if is_hit:
                        send_telegram_msg(f"🎯 **{ticker}** 포착!\n거래량: {v_ratio:.1f}배\n상태: 24H 실시간 감시 중")
                        already_sent.add(ticker)
                time.sleep(1.2) # API 차단 방지용
            except: continue
        # 한 사이클 완료 후 60초 대기
        time.sleep(60)

# --- [5] 메인 실행부 ---
if "engine_run" not in st.session_state:
    if not any(t.name == "StockEngine" for t in threading.enumerate()):
        threading.Thread(target=monitor_engine, name="StockEngine", daemon=True).start()
    st.session_state.engine_run = True

st.set_page_config(page_title="자윤 Stock AI 24H", layout="wide")
st.title("📡 자윤 24시간 실시간 감시 시스템")
st.success("✅ 자윤님의 4대 전략 조건이 백그라운드에서 무한 가동 중입니다.")
st.write(f"서버 현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.info("이제 이 페이지를 닫으셔도 서버는 멈추지 않고 텔레그램을 보냅니다.")
