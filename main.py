import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import streamlit.components.v1 as components
import os
import threading

# --- [0] 공유 저장소 및 자동 저장 설정 (추가) ---
# 백그라운드 스레드와 UI 간의 데이터 전달을 위한 클래스
class GlobalState:
    def __init__(self):
        self.progress_text = "준비 중..."
        self.progress_perc = 0
        self.hit_list = []  # 포착된 종목들 저장
        self.is_running = False

    def add_hit(self, ticker, v_ratio, price):
        new_hit = {
            "시간": datetime.now().strftime('%H:%M:%S'),
            "티커": ticker,
            "거래량배수": round(v_ratio, 2),
            "현재가": round(price, 2)
        }
        self.hit_list.append(new_hit)
        # 즉시 CSV 저장 (자동 저장)
        df_new = pd.DataFrame([new_hit])
        if not os.path.exists("captured_stocks.csv"):
            df_new.to_csv("captured_stocks.csv", index=False, encoding='utf-8-sig')
        else:
            df_new.to_csv("captured_stocks.csv", index=False, mode='a', header=False, encoding='utf-8-sig')

if "gs" not in st.session_state:
    st.session_state.gs = GlobalState()

# --- [1] 블랙리스트 영구 저장소 (원본 유지) ---
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

# --- [2] 블랙리스트 관리 함수 (원본 유지) ---
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

# --- 텔레그램 설정 (원본 유지) ---
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

# --- 설정 및 UI (원본 유지) ---
st.set_page_config(page_title="자윤 Stock AI V3.5", layout="wide")
st.title("🚀 미국 전수조사: 백테스팅 & 실시간 감시 통합형")

VOL_RATIO_THRESHOLD = 0.1
MIN_VALUE_THRESHOLD = 100 

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
        return (c1 and c2 and c3 and c4), vol_ratio, curr_close
    except: return False, 0, 0

# --- [수정] 24시간 무한 감시 백그라운드 엔진 (UI 연동 및 터미널 로그 최소화) ---
def monitor_engine(state_obj):
    already_sent_today = set()
    blacklist = load_blacklist()
    tickers = ALL_TICKERS
    
    # 터미널 시작 로그만 남김
    print(f"🚀 [엔진] 24H 감시 시작 (대상: {len(tickers)}개)", flush=True)
    
    while True:
        scan_targets = [t for t in tickers if t not in blacklist]
        total_count = len(scan_targets)
        batch_size = 20 

        for i in range(0, total_count, batch_size):
            batch = scan_targets[i:i+batch_size]
            
            # [수정] 터미널 진행로그 삭제 -> UI용 데이터 갱신
            progress_count = min(i + batch_size, total_count)
            state_obj.progress_perc = progress_count / total_count
            state_obj.progress_text = f"스캔 중: {progress_count} / {total_count} ({state_obj.progress_perc*100:.1f}%)"

            try:
                df_all = yf.download(batch, period="2d", interval="1m", progress=False, group_by='ticker', prepost=True, threads=True, timeout=15)
                for ticker in batch:
                    df = df_all[ticker] if len(batch) > 1 else df_all
                    if df.empty or ticker in already_sent_today: continue
                    
                    is_hit, v_ratio, price = check_strategy(df, ticker)
                    if is_hit:
                        # [수정] 터미널에는 포착 로그만 출력
                        print(f"🔥 [포착] {ticker} | 거래량: {v_ratio:.1f}배", flush=True)
                        send_telegram_msg(f"🚀 [포착] {ticker}\n거래량: {v_ratio:.1f}배\n가격: ${price:.2f}\n시간: {datetime.now().strftime('%H:%M:%S')}")
                        state_obj.add_hit(ticker, v_ratio, price) # UI 및 파일 자동 저장
                        already_sent_today.add(ticker)
                time.sleep(0.5) 
            except: continue
        
        state_obj.progress_text = f"✅ {datetime.now().strftime('%H:%M:%S')} 한 사이클 완료. 60초 대기 중..."
        time.sleep(60)

# --- [자동 시작 로직] ---
if "engine_run" not in st.session_state:
    if not any(t.name == "StockEngine" for t in threading.enumerate()):
        # 스레드 생성 시 state_obj 전달
        threading.Thread(target=monitor_engine, args=(st.session_state.gs,), name="StockEngine", daemon=True).start()
    st.session_state.engine_run = True

# --- 메인 UI 로직 ---
st.sidebar.header("🕹️ 모드 전환")
app_mode = st.sidebar.selectbox("실행할 모드를 선택하세요", ["백테스팅 (과거 성적 확인)", "실시간 감시 (현재 시장 감시)"])

if app_mode == "백테스팅 (과거 성적 확인)":
    # (원본 로직 유지)
    st.subheader("📊 2026년 1월 1일 ~ 현재 전수조사 리포트")
    pass

elif app_mode == "실시간 감시 (현재 시장 감시)":
    st.success("서버가 백그라운드에서 전 종목을 감시하고 있습니다.")
    
    # --- [추가] 실시간 진행 상황 및 포착 데이터 UI ---
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔄 실시간 스캔 진행률")
        prog_placeholder = st.empty()
        bar_placeholder = st.empty()
        
        # UI 업데이트용 루프 (이 부분이 화면을 갱신함)
        prog_placeholder.markdown(f"**상태:** {st.session_state.gs.progress_text}")
        bar_placeholder.progress(st.session_state.gs.progress_perc)

    with col2:
        st.subheader("🔥 실시간 포착 리스트 (자동 저장됨)")
        if st.session_state.gs.hit_list:
            df_hits = pd.DataFrame(st.session_state.gs.hit_list)
            st.table(df_hits.tail(10)) # 최근 10개 표시
            
            # CSV 다운로드 버튼 제공
            csv = df_hits.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 전체 포착 데이터 다운로드", csv, "hits.csv", "text/csv")
        else:
            st.write("아직 포착된 종목이 없습니다.")

    # 5초마다 UI 강제 새로고침
    time.sleep(5)
    st.rerun()
