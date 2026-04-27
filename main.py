import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import os
import threading

# --- [0] 공유 저장소 설정 (안정화) ---
class GlobalState:
    def __init__(self):
        self.progress_text = "준비 중..."
        self.progress_perc = 0
        self.hit_list = []  
        self.is_running = False

    def add_hit(self, ticker, v_ratio, price):
        new_hit = {
            "시간": datetime.now().strftime('%H:%M:%S'),
            "티커": ticker,
            "거래량배수": round(v_ratio, 2),
            "현재가": round(price, 2)
        }
        self.hit_list.append(new_hit)
        # CSV 즉시 저장 (utf-8-sig로 한글 깨짐 방지)
        try:
            df_new = pd.DataFrame([new_hit])
            if not os.path.exists("captured_stocks.csv"):
                df_new.to_csv("captured_stocks.csv", index=False, encoding='utf-8-sig')
            else:
                df_new.to_csv("captured_stocks.csv", index=False, mode='a', header=False, encoding='utf-8-sig')
        except:
            pass

# 세션 상태 초기화
if "gs" not in st.session_state:
    st.session_state.gs = GlobalState()

# --- [1] 티커 가져오기 (캐싱 활용) ---
@st.cache_data(ttl=86400)
def get_top_2000_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        all_data = pd.read_csv(url, header=None)[0].tolist()
        valid_tickers = [str(t).strip().upper() for t in all_data if str(t).isalpha()]
        blue_chips = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "AVGO", "LLY"]
        final_list = blue_chips + [t for t in valid_tickers if t not in blue_chips]
        return final_list[:2000]
    except:
        return ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "AMZN", "META"]

ALL_TICKERS = get_top_2000_tickers()

# --- [2] 블랙리스트 및 텔레그램 함수 ---

# 이 부분을 추가하거나 확인해 주세요! (기존의 긴 리스트를 그대로 쓰셔도 됩니다)
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

def load_blacklist():
    blacklist = set(HARD_BLACKLIST) # 이제 에러 안 날 거예요!
    if os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "r") as f:
            blacklist.update(line.strip() for line in f if line.strip())
    return blacklist

def send_telegram_msg(message):
    token = st.secrets.get("TELEGRAM_TOKEN", "")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.get(url, params={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- [3] 전략 체크 함수 (최적화 완료) ---
def get_safe_val(data):
    if isinstance(data, (pd.Series, pd.DataFrame)):
        if data.empty: return 0.0
        val = data.iloc[-1]
        return float(val)
    return float(data)

def check_strategy(df):
    if df is None or len(df) < 30: return False, 0, 0
    try:
        curr_close = get_safe_val(df['Close'])
        curr_vol = get_safe_val(df['Volume'])
        
        # 거래량 평균 (최근 5봉)
        vol_avg = df['Volume'].iloc[-6:-1].mean()
        if vol_avg == 0: return False, 0, 0
        vol_ratio = curr_vol / vol_avg

        # 지표 계산 (get_safe_val로 안전하게 추출)
        ma5 = get_safe_val(df['Close'].rolling(window=5).mean())
        ma20 = get_safe_val(df['Close'].rolling(window=20).mean())
        std20 = get_safe_val(df['Close'].rolling(window=20).std())
        
        upper_band = ma20 + (std20 * 2) if std20 > 0 else ma20
        curr_value = (curr_close * curr_vol) / 10000
        
        # 포착 조건
        c1 = vol_ratio >= 2.0
        c2 = curr_close > upper_band
        c3 = curr_close > ma5
        c4 = curr_value >= 5 # 거래대금 필터 (단위 확인 필요)

        return (c1 and c2 and c3 and c4), vol_ratio, curr_close
    except: return False, 0, 0

# --- [4] 감시 엔진 (배치 처리 보강) ---
def monitor_engine(state_obj):
    already_sent_today = set()
    while True:
        blacklist = load_blacklist()
        scan_targets = [t for t in ALL_TICKERS if t not in blacklist]
        total = len(scan_targets)
        batch_size = 25

        for i in range(0, total, batch_size):
            batch = scan_targets[i:i+batch_size]
            state_obj.progress_perc = (i + len(batch)) / total
            state_obj.progress_text = f"스캔 중: {i+len(batch)} / {total}"

            try:
                # 데이터 일괄 다운로드
                df_all = yf.download(batch, period="5d", interval="30m", progress=False, group_by='ticker', prepost=True, timeout=20)
                
                for ticker in batch:
                    try:
                        # 멀티 인덱스 데이터 추출
                        if len(batch) > 1:
                            if ticker not in df_all.columns.get_level_values(0): continue
                            df = df_all.xs(ticker, axis=1, level=0).dropna()
                        else:
                            df = df_all.dropna()
                        
                        if df.empty or len(df) < 30: continue
                        if ticker in already_sent_today: continue
                        
                        is_hit, v_ratio, price = check_strategy(df)
                        if is_hit:
                            send_telegram_msg(f"🚀 [포착] {ticker}\n거래량: {v_ratio:.1f}배\n가격: ${price:.2f}")
                            state_obj.add_hit(ticker, v_ratio, price)
                            already_sent_today.add(ticker)
                    except: continue
                time.sleep(1) # 과부하 방지
            except: 
                time.sleep(10)
                continue
        
        state_obj.progress_text = f"✅ {datetime.now().strftime('%H:%M')} 완주! 90초 휴식"
        time.sleep(90)

# --- [5] UI 및 실행 제어 ---
st.set_page_config(page_title="자윤 Stock AI V3.5", layout="wide")
st.title("🚀 미국 주식 24H 전수조사 시스템")

# 엔진 시작 (중복 실행 방지)
if "engine_started" not in st.session_state:
    if not any(t.name == "StockEngine" for t in threading.enumerate()):
        thread = threading.Thread(target=monitor_engine, args=(st.session_state.gs,), name="StockEngine", daemon=True)
        thread.start()
    st.session_state.engine_started = True

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("🔄 스캔 현황")
    st.info(st.session_state.gs.progress_text)
    st.progress(st.session_state.gs.progress_perc)

with col2:
    st.subheader("🔥 포착 리스트")
    if st.session_state.gs.hit_list:
        st.table(pd.DataFrame(st.session_state.gs.hit_list).tail(10))
    else:
        st.write("조건에 맞는 종목을 찾는 중...")

# 자동 새로고침 (10초)
time.sleep(10)
st.rerun()
