import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import platform
import io

# 플랫폼 확인 후 리눅스 클라우드 서버는 나눔고딕, 로컬은 맑은고딕 할당
if platform.system() == 'Linux':
    plt.rcParams['font.family'] = 'NanumGothic'
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="주식 손익 추적기", layout="wide", initial_sidebar_state="expanded")

if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv("stock_log.csv")
    except FileNotFoundError:
        st.session_state.df = pd.DataFrame(columns=["날짜", "목표금액", "입금총액", "현자산금액", "이익률(%)", "달성률(%)"])

def save_data(df):
    df.to_csv("stock_log.csv", index=False)
    st.session_state.df = df

df = st.session_state.df

with st.sidebar:
    st.header("📊 데이터 입력")
    
    default_target = 120000000
    default_deposit = 40000000
    if not df.empty:
        default_target = int(float(df.iloc[-1]["목표금액"]))
        default_deposit = int(float(df.iloc[-1]["입금총액"]))

    target_input = st.number_input("목표 금액 (원)", value=default_target, step=1000000)
    date_input = st.date_input("기록 날짜", datetime.today())
    deposit_input = st.number_input("입금 총액 (원)", value=default_deposit, step=1000000)
    asset_input = st.number_input("현재 자산 평가액 (원)", value=0, step=1000000)

    if st.button("데이터 기록 (EXECUTE)", use_container_width=True):
        if asset_input > 0:
            profit_rate = ((asset_input - deposit_input) / deposit_input) * 100 if deposit_input > 0 else 0
            achieve_rate = (asset_input / target_input) * 100 if target_input > 0 else 0
            
            new_data = pd.DataFrame({
                "날짜": [str(date_input)], "목표금액": [target_input], "입금총액": [deposit_input],
                "현자산금액": [asset_input], "이익률(%)": [round(profit_rate, 2)], "달성률(%)": [round(achieve_rate, 2)]
            })
            
            updated_df = pd.concat([df, new_data], ignore_index=True)
            updated_df = updated_df.drop_duplicates(subset=['날짜'], keep='last').sort_values(by="날짜")
            save_data(updated_df)
            st.rerun()
        else:
            st.error("현재 자산을 입력하십시오.")

    st.markdown("---")
    st.header("🗑️ 데이터 삭제")
    if not df.empty:
        delete_date = st.selectbox("삭제할 날짜 선택", df["날짜"].tolist()[::-1])
        if st.button("해당 기록 삭제", use_container_width=True):
            updated_df = df[df["날짜"] != delete_date]
            save_data(updated_df)
            st.rerun()

    st.markdown("---")
    st.header("💾 클라우드 데이터 관리")
    st.caption("서버 절전 모드 전환 시 데이터가 초기화될 수 있습니다. 주기적으로 백업하십시오.")
    
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="데이터 백업 (CSV 다운로드)",
            data=csv,
            file_name=f"stock_log_backup_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    uploaded_file = st.file_uploader("백업 파일 복구 (업로드)", type=["csv"])
    if uploaded_file is not None:
        if st.button("업로드한 파일로 데이터 덮어쓰기", use_container_width=True):
            restored_df = pd.read_csv(uploaded_file)
            save_data(restored_df)
            st.success("데이터가 성공적으로 복구되었습니다.")
            st.rerun()

st.title("📈 주식 손익 추적기 (Cloud Ver.)")

if df.empty:
    st.info("좌측 사이드바에서 초기 데이터를 입력하여 기록을 시작하거나, 기존 백업 파일을 업로드하십시오.")
else:
    latest = df.iloc[-1]
    net_profit = int(float(latest['현자산금액']) - float(latest['입금총액']))
    
    dod_amount = 0
    dod_rate = 0.0
    if len(df) > 1:
        prev = df.iloc[-2]
        dod_amount = int(float(latest['현자산금액']) - float(prev['현자산금액']))
        dod_rate = (dod_amount / float(prev['현자산금액'])) * 100 if float(prev['현자산금액']) > 0 else 0

    target_date_dt = datetime(2027, 3, 25)
    first_date_dt = datetime.strptime(str(df.iloc[0]['날짜']).split(' ')[0], "%Y-%m-%d")
    last_date_dt = datetime.strptime(str(latest['날짜']).split(' ')[0], "%Y-%m-%d")
    
    start_asset = float(df.iloc[0]['현자산금액']) if float(df.iloc[0]['현자산금액']) > 0 else float(df.iloc[0]['입금총액'])
    if start_asset <= 0: start_asset = 1.0
    target_asset = float(latest['목표금액'])
    latest_asset = float(latest['현자산금액'])
    
    days_elapsed = max(1, (last_date_dt - first_date_dt).days)
    days_rem = (target_date_dt - last_date_dt).days
    total_days = max(1, (target_date_dt - first_date_dt).days)

    if days_rem > 0:
        daily_profit = (latest_asset - float(latest['입금총액'])) / days_elapsed
        expected_asset = latest_asset + (daily_profit * days_rem)
    else:
        expected_asset = latest_asset

    req_rate = ((target_asset / latest_asset) - 1) * 100 if latest_asset > 0 else 0
    time_elapsed_pct = min(100.0, (days_elapsed / total_days) * 100)
    
    current_asset_int = int(latest_asset)
    next_milestone = ((current_asset_int // 10000000) + 1) * 10000000
    if next_milestone > target_asset: next_milestone = int(target_asset)
    rem_to_milestone = next_milestone - current_asset_int
    
    rem_months = days_rem / 30.416
    monthly_req_rate = ((target_asset / latest_asset) ** (1 / rem_months) - 1) * 100 if rem_months > 0 and latest_asset > 0 else 0.0
    cagr = ((latest_asset / float(latest['입금총액'])) ** (365 / days_elapsed) - 1) * 100 if days_elapsed > 0 and float(latest['입금총액']) > 0 else 0.0
    
    hwm_val = float(df.iloc[0]['현자산금액'])
    hwm_count = sum(1 for val in df['현자산금액'].astype(float) if val > (hwm_val := max(hwm_val, val)) or val == hwm_val and val > float(df.iloc[0]['현자산금액']))

    # 컬럼 비율 조정(1:1:1:1.3) 및 수치 축약(만 원) 적용
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.3])
    col1.metric("현재 총 이익률", f"{latest['이익률(%)']:.2f}%", f"{net_profit // 10000:,}만 원")
    col2.metric("전일 대비 증감", f"{dod_rate:.2f}%", f"{dod_amount // 10000:,}만 원")
    col3.metric("목표 달성률", f"{latest['달성률(%)']:.2f}%")
    if days_rem > 0:
        col4.metric("'27.03.25 예상 (추세선)", f"{int(max(0, expected_asset)) // 10000:,}만 원", f"필요: +{req_rate:.2f}%", delta_color="inverse")
    else:
        col4.metric("'27.03.25 예상", "기한 도달")

    st.markdown("---")

    sc1, sc2, sc3, sc4, sc5 = st.columns([1, 1, 1, 1.2, 1])
    sc1.metric("시간 진행률", f"{time_elapsed_pct:.1f}%")
    sc2.metric("연환산 기대수익률(CAGR)", f"{cagr:.2f}%")
    sc3.metric("월간 요구 수익률", f"{monthly_req_rate:.2f}%")
    sc4.metric(f"다음 마일스톤 ({next_milestone//10000}만)", f"잔여 {rem_to_milestone // 10000:,}만 원")
    sc5.metric("최고점 경신 횟수", f"{hwm_count} 회")

    st.markdown("---")

    fig, ax = plt.subplots(figsize=(10, 4))
    x_data = df['날짜']
    y_data = df['현자산금액'].astype(float)
    
    custom_blue_cmap = LinearSegmentedColormap.from_list('light_blue_grad', ['#85C1E9', '#2E86C1'], N=100)
    bar_width = 0.2 if len(x_data) == 1 else 0.4
    bars = ax.bar(x_data, y_data, width=bar_width, color='none', zorder=2)
    
    norm = plt.Normalize(0, y_data.max() if not y_data.empty else 1)
    for bar in bars:
        x, y, w, h = bar.get_bbox().bounds
        grad_rect = Rectangle((x, 0), w, h, linewidth=0, zorder=1)
        grad_color = custom_blue_cmap(norm(y))
        bar.set_facecolor(grad_color)
        bar.set_edgecolor('#1A5276')
    
    ideal_y = []
    for d_str in x_data:
        curr_d = datetime.strptime(str(d_str).split(' ')[0], "%Y-%m-%d")
        d_passed_val = max(0, (curr_d - first_date_dt).days)
        ideal_val = start_asset * ((target_asset / start_asset) ** (d_passed_val / total_days))
        ideal_y.append(ideal_val)
    
    ax.plot(x_data, ideal_y, color='#8e44ad', linestyle='--', marker='o', linewidth=2, label='목표 성장 궤도', zorder=3)
    
    if len(x_data) == 1: ax.set_xlim(-1, 1)
    ax.set_title("자산 증식 시뮬레이션", fontsize=14, pad=10, fontweight='bold')
    ax.tick_params(axis='x', rotation=45, labelsize=9) 
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: "{:,}".format(int(val))))
    ax.legend(loc='lower right', bbox_to_anchor=(1.0, 1.05), frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='y', linestyle=':', alpha=0.7)
    
    st.pyplot(fig)

    col_t1, col_t2 = st.columns([7, 3])
    
    with col_t1:
        st.subheader("상세 데이터 기록")
        display_df = df.copy()
        display_df['현자산금액'] = display_df['현자산금액'].astype(float)
        display_df['전일 증감액(원)'] = display_df['현자산금액'].diff().fillna(0).astype(int)
        display_df['전일 증감률(%)'] = (display_df['현자산금액'].pct_change() * 100).fillna(0).round(2)
        cols = ["날짜", "목표금액", "입금총액", "현자산금액", "전일 증감액(원)", "전일 증감률(%)", "이익률(%)", "달성률(%)"]
        display_df = display_df[cols].sort_values(by="날짜", ascending=False).reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col_t2:
        st.subheader("월별 목표 스케줄 가이드")
        try:
            schedule_dates = list(pd.date_range(start=first_date_dt, end=target_date_dt, freq='ME'))
        except: 
            schedule_dates = list(pd.date_range(start=first_date_dt, end=target_date_dt, freq='M'))
            
        if not schedule_dates or schedule_dates[-1].date() < target_date_dt.date():
            schedule_dates.append(pd.Timestamp(target_date_dt))
            
        sched_data = []
        for dt_obj in schedule_dates:
            d_passed_val = (dt_obj.date() - first_date_dt.date()).days
            expected_val = start_asset * ((target_asset / start_asset) ** (d_passed_val / total_days))
            rounded_target = round(expected_val, -6)
            req_amt = rounded_target - latest_asset
            
            sched_data.append({
                "기한": f"{dt_obj.strftime('%y')}.{dt_obj.month}",
                "목표 자산액": f"{int(rounded_target // 10000):,}만",
                "잔여 필요액": f"{int(req_amt // 10000):,}만" if req_amt > 0 else "목표 초과"
            })
            
        st.dataframe(pd.DataFrame(sched_data), use_container_width=True, hide_index=True)
