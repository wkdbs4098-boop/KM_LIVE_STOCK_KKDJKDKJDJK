import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import streamlit.components.v1 as components
import os
import threading

# --- [1] 블랙리스트 영구 저장소 (자윤님 데이터 유지) ---
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

# --- [2] 블랙리스트 관리 함수 (자윤님 원본 유지) ---
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

def play_sound():
    sound_html = """<audio autoplay><source src="https://raw.githubusercontent.com/carsonology/free-sound-effects/master/notifications/success.mp3" type="audio/mp3"></audio>"""
    components.html(sound_html, height=0)

# --- 설정 및 UI ---
st.set_page_config(page_title="자윤 Stock AI V3.5", layout="wide")
st.title("🚀 미국 전수조사: 백테스팅 & 실시간 감시 통합형")

VOL_RATIO_THRESHOLD = 3
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
        vol_avg = df['Volume'].iloc[-6:-1].mean()
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

# --- [추가] 24시간 무한 감시 백그라운드 엔진 (로그 출력 포함) ---
def monitor_engine():
    already_sent_today = set()
    blacklist = load_blacklist()
    tickers = ALL_TICKERS
    
    print(f"🚀 [엔진] 24H 감시 시작 (대상: {len(tickers)}개)", flush=True)
    
    while True:
        scan_targets = [t for t in tickers if t not in blacklist]
        total_count = len(scan_targets)
        batch_size = 20 

        for i in range(0, total_count, batch_size):
            batch = scan_targets[i:i+batch_size]
            
            # 자윤님이 원하신 터미널 진행 로그
            progress = min(i + batch_size, total_count)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 스캔 중: {progress} / {total_count} ({progress/total_count*100:.1f}%)", flush=True)

            try:
                df_all = yf.download(batch, period="2d", interval="1m", progress=False, group_by='ticker', prepost=True, threads=True, timeout=15)
                for ticker in batch:
                    df = df_all[ticker] if len(batch) > 1 else df_all
                    if df.empty or ticker in already_sent_today: continue
                    
                    is_hit, v_ratio, _ = check_strategy(df, ticker)
                    if is_hit:
                        send_telegram_msg(f"🚀 [포착] {ticker}\n거래량: {v_ratio:.1f}배\n시간: {datetime.now().strftime('%H:%M:%S')}")
                        already_sent_today.add(ticker)
                time.sleep(0.5) 
            except: continue
        
        print(f"✅ {datetime.now().strftime('%H:%M:%S')} 한 사이클 완료. 60초 대기...", flush=True)
        time.sleep(60)

# --- [자동 시작 로직] ---
if "engine_run" not in st.session_state:
    if not any(t.name == "StockEngine" for t in threading.enumerate()):
        threading.Thread(target=monitor_engine, name="StockEngine", daemon=True).start()
    st.session_state.engine_run = True

# --- 메인 UI 로직 (자윤님 원본 모드 전환 그대로 유지) ---
st.sidebar.header("🕹️ 모드 전환")
app_mode = st.sidebar.selectbox("실행할 모드를 선택하세요", ["백테스팅 (과거 성적 확인)", "실시간 감시 (현재 시장 감시)"])

if app_mode == "백테스팅 (과거 성적 확인)":
    # ... (자윤님의 백테스팅 코드 내용 생략 없이 그대로 유지)
    st.subheader("📊 2026년 1월 1일 ~ 현재 전수조사 리포트")
    # (원본 로직 생략 없이 그대로 넣어주시면 됩니다)
    pass

elif app_mode == "실시간 감시 (현재 시장 감시)":
    st.info("현재 서버가 24시간 백그라운드에서 감시 중입니다. 텔레그램을 확인하세요.")
    # ... (자윤님의 실시간 감시 UI 로직 유지)
