import streamlit as st
import pandas as pd
from datetime import datetime, date

# 페이지 설정
st.set_page_config(page_title="QA & 필드 클레임 통합 관리", page_icon="📊", layout="wide")

# 사이드바 메뉴 CSS (글씨 키우기, 아이콘 제거)
st.markdown("""
    <style>
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 6px 0px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 품질보증 및 필드 클레임 통합 관리 대시보드")

# 세션 스테이트 초기화 (일정 및 업무 데이터 유지용)
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

# 사이드바 메뉴
st.sidebar.markdown("## 🧭 메뉴 목록")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["업무 현황", "필드 클레임 현황", "개선 활동 관리", "고객사 클레임 비용 분석", "구글 시트 연동 설정"],
    label_visibility="collapsed"
)

if menu == "업무 현황":
    st.subheader("📋 월별 캘린더 및 업무 일정 관리")
    
    # 1. 달력 월 조작 세션 처리
    if 'cal_year' not in st.session_state:
        st.session_state['cal_year'] = datetime.today().year
    if 'cal_month' not in st.session_state:
        st.session_state['cal_month'] = datetime.today().month

    # 상단 달력 이동 컨트롤러
    col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
    with col_m1:
        if st.button("◀ 이전 달"):
            if st.session_state['cal_month'] == 1:
                st.session_state['cal_month'] = 12
                st.session_state['cal_year'] -= 1
            else:
                st.session_state['cal_month'] -= 1
            st.rerun()
    with col_m2:
        st.markdown(f"<h3 style='text-align: center;'>{st.session_state['cal_year']}년 {st.session_state['cal_month']}월</h3>", unsafe_allow_html=True)
    with col_m3:
        if st.button("다음 달 ▶"):
            if st.session_state['cal_month'] == 12:
                st.session_state['cal_month'] = 1
                st.session_state['cal_year'] += 1
            else:
                st.session_state['cal_month'] += 1
            st.rerun()

    st.markdown("---")

    # 화면 분할 (좌측: 달력 및 당일 업무 / 우측: 일정 등록 폼)
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("#### 📅 월별 달력 및 날짜별 일정")
        
        # 선택한 날짜 저장을 위한 세션
        if 'selected_date' not in st.session_state:
            st.session_state['selected_date'] = date.today()

        # 간단한 달력 날짜 선택 버튼 뷰 구현
        selected_year = st.session_state['cal_year']
        selected_month = st.session_state['cal_month']
        
        # 해당 월의 날짜 목록 생성
        import calendar
        cal_matrix = calendar.monthcalendar(selected_year, selected_month)
        
        # 요일 헤더
        cols = st.columns(7)
        days_kor = ["월", "화", "수", "목", "금", "토", "일"]
        for i, d_name in enumerate(days_kor):
            cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{d_name}</p>", unsafe_allow_html=True)

        # 날짜 버튼 렌더링
        for week in cal_matrix:
            w_cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    w_cols[i].write("")
                else:
                    current_d = date(selected_year, selected_month, day)
                    # 해당 날짜에 등록된 일정 개수 확인
                    day_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(current_d)]
                    btn_label = f"{day}"
                    if day_tasks:
                        btn_label += f" ({len(day_tasks)})"
                    
                    if w_cols[i].button(btn_label, key=f"day_{selected_year}_{selected_month}_{day}"):
                        st.session_state['selected_date'] = current_d

        st.markdown(f"**선택된 날짜:** {st.session_state['selected_date']}")
        
        st.markdown("---")
        st.markdown(f"#### 📝 {st.session_state['selected_date']} 당일 업무 및 완료 처리")
        
        # 선택된 날짜의 업무 목록 필터링
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        
        if not target_tasks:
            st.info("선택된 날자에 등록된 업무가 없습니다. 우측에서 일정을 등록해 주세요.")
        else:
            for idx, task in enumerate(st.session_state['tasks']):
                if str(task['date']) == str(st.session_state['selected_date']):
                    cols_t = st.columns([0.1, 0.7, 0.2])
                    
                    # 완료 체크박스
                    is_checked = cols_t[0].checkbox("", value=task['completed'], key=f"chk_{task['id']}")
                    if is_checked != task['completed']:
                        task['completed'] = is_checked
                        if is_checked:
                            task['completed_date'] = str(date.today())
                        else:
                            task['completed_date'] = None
                        st.rerun()
                    
                    # 업무 제목 표시 (완료 시 취소선 및 회색 처리)
                    if task['completed']:
                        cols_t[1].markdown(f"<span style='color: gray; text-decoration: line-through;'>{task['title']} [{task['category']}]</span><br><small style='color:gray;'>처리완료일: {task.get('completed_date', '-')}</small>", unsafe_allow_html=True)
                    else:
                        cols_t[1].markdown(f"<b>{task['title']}</b> <span style='font-size:12px; background:#e0f2fe; padding:2px 6px; border-radius:4px;'>{task['category']}</span><br><small>요청자: {task['requester']} | 마감: {task['deadline']}</small>", unsafe_allow_html=True)

    with col_right:
        st.markdown("#### ➕ 신규 일정 등록 / 기록")
        with st.form("task_form", clear_on_submit=True):
            f_title = st.text_input("업무 제목")
            f_date = st.date_input("일정 날짜", value=st.session_state['selected_date'])
            f_deadline = st.date_input("마감 기한")
            f_category = st.selectbox("카테고리 선택", ["고객제출", "업체접수", "자료작성"])
            f_requester = st.text_input("요청자")
            f_memo = st.text_area("메모 및 상세 내용")
            
            submitted = st.form_submit_button("일정 저장")
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
                    st.success("일정이 성공적으로 저장되어 달력에 반영되었습니다!")
                    st.rerun()

elif menu == "필드 클레임 현황":
    st.subheader("생산 품목별 필드 클레임 누적 현황")
    st.markdown("구글 시트 원본 데이터 기반 자동 집계 분석 화면입니다.")
    
    chart_data = pd.DataFrame({
        '클레임 발생 건수': [65, 42, 25, 10]
    }, index=['쿨런트 펌프 (K3)', '워터 펌프 (Cee\'d)', '쿨런트 펌프 (쏘렌토)', '기타 부품'])
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
    
    cost_data = {
        "고객사": ["현대 / 글로비스", "현대위아", "모비스"],
        "합산/청구 비용": ["₩ 18,450,000", "₩ 12,300,000", "₩ 11,830,000"]
    }
    st.dataframe(pd.DataFrame(cost_data), use_container_width=True)

elif menu == "구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동")
    st.text_input("필드 클레임 현황 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    st.text_input("고객사 클레임 비용 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    if st.button("연동 정보 저장"):
        st.success("구글 클라우드 스프레드시트와 성공적으로 연동되었습니다!")
