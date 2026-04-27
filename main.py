import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import streamlit.components.v1 as components
import os

# --- [1] 블랙리스트 영구 저장소 (가장 상단에 위치) ---
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
# --- 텔레그램 설정 (수정본: 내 PC & 클라우드 공용) ---
# --- [2] 블랙리스트 관리 함수 ---
def load_blacklist():
    blacklist = set(HARD_BLACKLIST)
    if os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "r") as f:
            blacklist.update(line.strip() for line in f if line.strip())
    return blacklist

def save_blacklist(blacklist_set):
    with open("blacklist.txt", "w") as f:
        for ticker in sorted(list(blacklist_set)):


# --- 텔레그램 설정 ---
try:
    # 1. 클라우드(Streamlit Cloud) 보안 설정 확인
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
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
    if 'already_sent' not in st.session_state: st.session_state.already_sent = set()
    if 'black_list' not in st.session_state: st.session_state.black_list = load_blacklist()

    mon_status = st.empty()
    mon_results = st.container()

    if st.button("📡 실시간 무한 감시 시작"):
        batch_size = 30 # [최적화] 배치 크기를 조금 더 키워 통신 횟수 감소
        while True:
            scan_targets = [t for t in ALL_TICKERS if t not in st.session_state.black_list]
            total_count = len(scan_targets)
            current_time = datetime.now().strftime('%H:%M:%S')

            # --- 터미널 시작 알림 ---
            print(f"\n{'='*40}")
            print(f"▶ 스캔 시작: {current_time} (대상: {total_count}개)")
            print(f"{'='*40}")

            for i in range(0, total_count, batch_size):
                batch_tickers = scan_targets[i:i+batch_size]
                
                # 웹 UI 업데이트
                mon_status.warning(f"⏱️ 스캔 중: {i + len(batch_tickers)} / {total_count} (블랙리스트: {len(st.session_state.black_list)}개)")
                
                # [개선] 터미널 진행 상황 즉시 출력 (flush=True 추가)
                progress_percent = ((i + len(batch_tickers)) / total_count) * 100
                print(f"[{current_time}] 진행: {progress_percent:4.1f}% | {batch_tickers[0]}... 진행 중", flush=True)
                
                try:
                    # [최적화] threads=True로 변경하여 병렬 다운로드 활성화 (속도 대폭 향상)
                    df_all = yf.download(
                        batch_tickers, 
                        period="2d", 
                        interval="1m", 
                        progress=False, 
                        group_by='ticker', 
                        prepost=True, 
                        threads=True,  # 속도의 핵심
                        timeout=10     # 응답 없는 종목 무시
                    )
                    
                    for ticker in batch_tickers:
                        # 데이터 구조 처리
                        df_live = df_all[ticker] if len(batch_tickers) > 1 else df_all
                        
                        # 데이터 유무 체크
                        if df_live.empty or df_live['Close'].dropna().empty:
                            if ticker not in st.session_state.black_list:
                                print(f"  └ ❌ {ticker}: 데이터 없음 (블랙리스트 추가)", flush=True)
                                st.session_state.black_list.add(ticker)
                                save_blacklist(st.session_state.black_list)
                            continue 
                        
                        # 전략 체크
                        if len(df_live) < 21: continue
                        is_hit, v_ratio, _ = check_strategy(df_live, ticker)
                        
                        if is_hit and ticker not in st.session_state.already_sent:
                            with mon_results:
                                st.success(f"🎯 **{ticker}** 포착! | {v_ratio:.1f}배 | {current_time}")
                            play_sound()
                            send_telegram_msg(f"🚀 [포착] {ticker}\n거래량: {v_ratio:.1f}배\n시간: {current_time}")
                            st.session_state.already_sent.add(ticker)
                            print(f"  └ 🔥 {ticker} 포착 완료!", flush=True)

                except Exception as e:
                    print(f"  └ ⚠️ 에러 발생 ({batch_tickers[0]} 등): {e}", flush=True)
                    continue
            
            print(f"\n✅ 한 사이클 완료! 60초 대기 후 재시작...", flush=True)
            time.sleep(60)
