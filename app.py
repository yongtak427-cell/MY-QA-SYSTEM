import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# 페이지 설정 (레이아웃 넓게 설정)
st.set_page_config(page_title="TIKITAK Task Management", page_icon="📊", layout="wide")

# CSS 스타일: 화면 여백 축소(100% 배율 최적화), 글씨 및 버튼 스타일 커스텀
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 6px 0px;
    }
    div.stCheckbox label p {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀 변경
st.title("Quality Assurance/Management")

# 세션 스테이트 초기화
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = [
        {
            "id": 1,
            "title": "[현대위아] 10월 클레임 비용 정산",
            "date": date.today(),
            "deadline": date.today(),
            "memo": "2차 검토 및 보고서 반영 필요",
            "requester": "현대위아 품질팀",
            "category": "고객제출",
            "completed": False,
            "completed_date": None
        },
        {
            "id": 2,
            "title": "워터 펌프 어셈블리 소음 이슈 분석",
            "date": date.today(),
            "deadline": date.today(),
            "memo": "원인 분석 결과 회신",
            "requester": "고객지원팀",
            "category": "자료작성",
            "completed": True,
            "completed_date": str(date.today())
        }
    ]

if 'cal_year' not in st.session_state:
    st.session_state['cal_year'] = datetime.today().year
if 'cal_month' not in st.session_state:
    st.session_state['cal_month'] = datetime.today().month
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = date.today()

# 사이드바 메뉴 (Menu List로 변경)
st.sidebar.markdown("## 🧭 Menu List")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["업무 현황", "필드 클레임 현황", "개선 활동 관리", "고객사 클레임 비용 분석", "구글 시트 연동 설정"],
    label_visibility="collapsed"
)

if menu == "업무 현황":
    st.subheader("📋 월별 캘린더 및 업무 일정 관리")
    
    # 상단 달력 이동 컨트롤러
    col_m1, col_m2, col_m3 = st.columns([1, 3, 1])
    with col_m1:
        if st.button("◀ 이전 달", use_container_width=True):
            if st.session_state['cal_month'] == 1:
                st.session_state['cal_month'] = 12
                st.session_state['cal_year'] -= 1
            else:
                st.session_state['cal_month'] -= 1
            st.rerun()
    with col_m2:
        st.markdown(f"<h2 style='text-align: center; margin: 0;'>{st.session_state['cal_year']}년 {st.session_state['cal_month']}월</h2>", unsafe_allow_html=True)
    with col_m3:
        if st.button("다음 달 ▶", use_container_width=True):
            if st.session_state['cal_month'] == 12:
                st.session_state['cal_month'] = 1
                st.session_state['cal_year'] += 1
            else:
                st.session_state['cal_month'] += 1
            st.rerun()

    st.markdown("---")

    # 법정 공휴일 정의 (월, 일)
    holidays = [(1, 1), (3, 1), (5, 5), (6, 6), (8, 15), (10, 3), (10, 9), (12, 25)]

    # 대형 달력 렌더링
    selected_year = st.session_state['cal_year']
    selected_month = st.session_state['cal_month']
    cal_matrix = calendar.monthcalendar(selected_year, selected_month)

    # 요일 헤더 (월~일) -> 요일 글씨 흰색, 일요일/토요일(공휴일) 빨간색
    days_kor = ["월", "화", "수", "목", "금", "토", "일"]
    h_cols = st.columns(7)
    for i, d_name in enumerate(days_kor):
        color = "red" if i == 6 else "white"
        h_cols[i].markdown(f"<p style='text-align: center; font-weight: bold; color: {color}; font-size: 16px;'>{d_name}</p>", unsafe_allow_html=True)

    # 날짜 그리드 출력
    for week in cal_matrix:
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                w_cols[i].markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)
            else:
                current_d = date(selected_year, selected_month, day)
                is_holiday = (selected_month, day) in holidays or i == 6  # 일요일 또는 법정 공휴일
                num_color = "red" if is_holiday else "white"
                
                day_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(current_d)]
                
                with w_cols[i]:
                    btn_text = f"📌 {day}일" if day_tasks else f"{day}"
                    if st.button(btn_text, key=f"cal_btn_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        st.session_state['selected_date'] = current_d
                    
                    # 달력 칸 안에 카테고리만 한 줄에 2개씩 배치 (최대 6개)
                    badges_html = "<div style='display: flex; flex-wrap: wrap; gap: 2px; justify-content: flex-start;'>"
                    for t in day_tasks[:6]:
                        cat = t['category']
                        # 카테고리별 색상 매칭 (고객제출: 빨강계열, 자료작성: 초록계열, 업체접수: 파랑계열)
                        if cat == '고객제출':
                            bg, fg = "#fee2e2", "#991b1b"
                        elif cat == '자료작성':
                            bg, fg = "#dcfce7", "#166534"
                        else: # 업체접수
                            bg, fg = "#dbeafe", "#1e40af"
                            
                        # 완료 여부에 따라 달력 내 카테고리도 회색 처리
                        if t['completed']:
                            bg, fg = "#334155", "#94a3b8"
                            t_style = "text-decoration: line-through; color: #94a3b8;"
                        else:
                            t_style = f"color: {fg};"

                        badges_html += f"<span style='font-size:10px; background:{bg}; color:{fg}; padding:1px 4px; border-radius:3px; white-space:nowrap;'><b style='{t_style}'>{cat}</b></span>"
                    badges_html += "</div>"
                    
                    if len(day_tasks) > 6:
                        badges_html += f"<div style='font-size:9px; color:gray; margin-top:2px;'>외 {len(day_tasks)-6}건</div>"
                        
                    st.markdown(f"<div style='min-height:70px;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 하단 분할: 좌측(당일 업무 및 완료 처리) / 우측(신규 일정 등록)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"### 📌 선택한 날짜: {st.session_state['selected_date']} 업무 현황")
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        
        if not target_tasks:
            st.info("선택된 날짜에 등록된 업무가 없습니다. 우측에서 일정을 등록해 보세요.")
        else:
            for task in st.session_state['tasks']:
                if str(task['date']) == str(st.session_state['selected_date']):
                    with st.container(border=True):
                        cols_t = st.columns([0.2, 0.8])
                        
                        # 완료 버튼
                        is_checked = cols_t[0].checkbox("완료", value=task['completed'], key=f"chk_{task['id']}")
                        
                        if is_checked != task['completed']:
                            task['completed'] = is_checked
                            task['completed_date'] = str(date.today()) if is_checked else None
                            st.rerun()
                        
                        # 카테고리별 색상 지정
                        cat = task['category']
                        if cat == '고객제출':
                            c_bg, c_fg = "#fee2e2", "#991b1b"
                        elif cat == '자료작성':
                            c_bg, c_fg = "#dcfce7", "#166534"
