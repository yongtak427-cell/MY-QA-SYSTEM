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

# 메인 타이틀
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
if 'highlighted_task_id' not in st.session_state:
    st.session_state['highlighted_task_id'] = None

# 사이드바 메뉴 (Menu List)
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
                
                day_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(current_d)]
                
                with w_cols[i]:
                    # 날짜 선택 버튼 (클릭 시 해당 날짜로 이동 및 하이라이트 초기화)
                    btn_text = f"📌 {day}일" if day_tasks else f"{day}"
                    if st.button(btn_text, key=f"cal_btn_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        st.session_state['selected_date'] = current_d
                        st.rerun()
                    
                    # 달력 칸 안에 카테고리 배지 깔끔하게 2열로 표시 (중복 제거 완료)
                    badges_html = "<div style='display: flex; flex-wrap: wrap; gap: 2px; justify-content: flex-start;'>"
                    for t in day_tasks[:6]:
                        cat = t['category']
                        if cat == '고객제출':
                            bg, fg = "#fee2e2", "#991b1b"
                        elif cat == '자료작성':
                            bg, fg = "#dcfce7", "#166534"
                        else: # 업체접수
                            bg, fg = "#dbeafe", "#1e40af"
                            
                        if t['completed']:
                            bg, fg = "#334155", "#94a3b8"
                            t_style = "text-decoration: line-through; color: #94a3b8;"
                        else:
                            t_style = f"color: {fg};"

                        badges_html += f"<span style='font-size:10px; background:{bg}; color:{fg}; padding:1px 4px; border-radius:3px; white-space:nowrap;'><b style='{t_style}'>{cat}</b></span>"
                    badges_html += "</div>"
                    
                    if len(day_tasks) > 6:
                        badges_html += f"<div style='font-size:9px; color:gray; margin-top:2px;'>외 {len(day_tasks)-6}건</div>"
                        
                    st.markdown(f"<div style='min-height:60px;'>{badges_html}</div>", unsafe_allow_html=True)
                    
                    # 각 카테고리 배지별 클릭 버튼 (아래 업무 현황에서 해당 건 테두리 강조 토글)
                    for t in day_tasks[:6]:
                        if st.button(f"🔍 {t['category']} ({t['title'][:3]}..)", key=f"click_task_{t['id']}"):
                            st.session_state['selected_date'] = current_d
                            if st.session_state['highlighted_task_id'] == t['id']:
                                st.session_state['highlighted_task_id'] = None
                            else:
                                st.session_state['highlighted_task_id'] = t['id']
                            st.rerun()

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
                    # 선택된 항목일 경우 전체 카드 테두리를 빨간색 계열로 강조
                    is_highlighted = (st.session_state['highlighted_task_id'] == task['id'])
                    
                    if is_highlighted:
                        box_style = "border: 2.5px solid #ef4444; border-radius: 10px; padding: 15px; background-color: #1e293b; margin-bottom: 12px;"
                    else:
                        box_style = "border: 1px solid #334155; border-radius: 10px; padding: 15px; margin-bottom: 12px; background-color: #0e1117;"

                    # HTML 카드로 전체 내용을 감싸서 깔끔하게 렌더링
                    cat = task['category']
                    if cat == '고객제출':
                        c_bg, c_fg = "#fee2e2", "#991b1b"
                    elif cat == '자료작성':
                        c_bg, c_fg = "#dcfce7", "#166534"
                    else:
                        c_bg, c_fg = "#dbeafe", "#1e40af"

                    st.markdown(f"<div style='{box_style}'>", unsafe_allow_html=True)
                    
                    cols_t = st.columns([0.2, 0.8])
                    is_checked = cols_t[0].checkbox("완료", value=task['completed'], key=f"chk_{task['id']}")
                    
                    if is_checked != task['completed']:
                        task['completed'] = is_checked
                        task['completed_date'] = str(date.today()) if is_checked else None
                        if is_checked and st.session_state['highlighted_task_id'] == task['id']:
                            st.session_state['highlighted_task_id'] = None
                        st.rerun()

                    if task['completed']:
                        cols_t[1].markdown(f"""
                            <span style='color: #94a3b8; text-decoration: line-through; font-size: 18px; font-weight: bold;'>{task['title']}</span> 
                            <span style='font-size:12px; background:#334155; color:#94a3b8; padding:2px 6px; border-radius:4px;'>{cat}</span><br>
                            <div style='font-size: 14px; color: #94a3b8; margin-top: 6px;'>
                                <b>요청자:</b> {task['requester']}<br>
                                <b>마감기한:</b> {task['deadline']}<br>
                                <b>메모 및 상세 내용:</b> {task['memo']}
                            </div>
                            <small style='color:#22c55e;'><b>[처리완료일: {task.get('completed_date', '-')}]</b></small>
                        """, unsafe_allow_html=True)
                    else:
                        cols_t[1].markdown(f"""
                            <span style='font-size: 18px; font-weight: bold; color: white;'>{task['title']}</span> 
                            <span style='font-size:12px; background:{c_bg}; color:{c_fg}; padding:2px 6px; border-radius:4px; font-weight:bold;'>{cat}</span><br>
                            <div style='font-size: 14px; color: #e2e8f0; margin-top: 6px; line-height: 1.5;'>
                                <b>요청자:</b> {task['requester']}<br>
                                <b>마감기한:</b> {task['deadline']}<br>
                                <b>메모 및 상세 내용:</b> {task['memo']}
                            </div>
                        """, unsafe_allow_html=True)
                        
                    st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("### ✍️ 신규 일정 등록")
        with st.form("task_form_new", clear_on_submit=True):
            f_title = st.text_input("업무 제목")
            f_date = st.date_input("일정 날짜 (달력 반영일)", value=st.session_state['selected_date'])
            f_deadline = st.date_input("마감 기한")
            f_category = st.selectbox("카테고리 선택", ["고객제출", "업체접수", "자료작성"])
            f_requester = st.text_input("요청자")
            f_memo = st.text_area("메모 및 상세 내용")
            
            submitted = st.form_submit_button("일정 저장 및 달력 반영", use_container_width=True)
            if submitted:
                if f_title.strip() == "":
                    st.warning("업무 제목을 입력해주세요.")
                else:
                    new_id = len(st.session_state['tasks']) + 1
                    new_task = {
                        "id": new_id,
                        "title": f_title,
                        "date": f_date,
                        "deadline": f_deadline,
                        "memo": f_memo,
                        "requester": f_requester,
                        "category": f_category,
                        "completed": False,
                        "completed_date": None
                    }
                    st.session_state['tasks'].append(new_task)
                    st.success("일정이 성공적으로 저장되었습니다!")
                    st.rerun()

elif menu == "필드 클레임 현황":
    st.subheader("생산 품목별 필드 클레임 누적 현황")
    st.markdown("구글 시트 원본 데이터 기반 자동 집계 분석 화면입니다.")
    chart_data = pd.DataFrame({'클레임 발생 건수': [65, 42, 25, 10]}, index=['쿨런트 펌프 (K3)', '워터 펌프 (Cee\'d)', '쿨런트 펌프 (쏘렌토)', '기타 부품'])
    st.bar_chart(chart_data)

elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 타임라인")
    data = {
        "품번 / 부품명": ["251002B700 (쿨런트 펌프)", "251003CAC0 (PUMP ASSY)"],
        "주요 불량 현상": ["엔진 소음/이음", "성능 불량 / 누수"],
        "개선 조치 내용": ["임펠러 금형 수정 및 실링재 변경", "하우스 가스켓 조립 공정 치구 보완"],
        "적용 시점": ["2026-07-15 (Lot: 26G15)", "2026-11-01 (예정)"],
        "상태": ["적용 완료", "적용 대기"]
    }
    st.table(pd.DataFrame(data))

elif menu == "고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 2차 가공 및 분석")
    st.info("현대, 모비스, 현대위아, 글로비스 원본 시트 자동 취합 및 환율/분담율 계산 결과가 여기에 표시됩니다.")
    cost_data = {"고객사": ["현대 / 글로비스", "현대위아", "모비스"], "합산/청구 비용": ["₩ 18,450,000", "₩ 12,300,000", "₩ 11,830,000"]}
    st.dataframe(pd.DataFrame(cost_data), use_container_width=True)

elif menu == "구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동")
    st.text_input("필드 클레임 현황 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    st.text_input("고객사 클레임 비용 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    if st.button("연동 정보 저장"):
        st.success("구글 클라우드 스프레드시트와 성공적으로 연동되었습니다!")
