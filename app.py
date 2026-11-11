import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import os

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

# 세션 스테이트 초기화 (업무 현황용)
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
            "completed_date": None,
            "updated_date": None
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
            "completed_date": str(date.today()),
            "updated_date": None
        }
    ]

if 'cal_year' not in st.session_state:
    st.session_state['cal_year'] = datetime.today().year
if 'cal_month' not in st.session_state:
    st.session_state['cal_month'] = datetime.today().month
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = date.today()
if 'editing_task_id' not in st.session_state:
    st.session_state['editing_task_id'] = None

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

    holidays = [(1, 1), (3, 1), (5, 5), (6, 6), (8, 15), (10, 3), (10, 9), (12, 25)]

    selected_year = st.session_state['cal_year']
    selected_month = st.session_state['cal_month']
    cal_matrix = calendar.monthcalendar(selected_year, selected_month)

    days_kor = ["월", "화", "수", "목", "금", "토", "일"]
    h_cols = st.columns(7)
    for i, d_name in enumerate(days_kor):
        color = "red" if i == 6 else "white"
        h_cols[i].markdown(f"<p style='text-align: center; font-weight: bold; color: {color}; font-size: 16px;'>{d_name}</p>", unsafe_allow_html=True)

    for week in cal_matrix:
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                w_cols[i].markdown("<div style='height: 130px;'></div>", unsafe_allow_html=True)
            else:
                current_d = date(selected_year, selected_month, day)
                day_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(current_d)]
                
                with w_cols[i]:
                    btn_text = f"📌 {day}일" if day_tasks else f"{day}"
                    if st.button(btn_text, key=f"cal_btn_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        st.session_state['selected_date'] = current_d
                        st.rerun()
                    
                    badges_html = "<div style='display: flex; flex-wrap: wrap; gap: 2px; justify-content: flex-start;'>"
                    for t in day_tasks[:6]:
                        cat = t['category']
                        if cat == '고객제출':
                            bg, fg = "#fee2e2", "#991b1b"
                        elif cat == '자료작성':
                            bg, fg = "#dbeafe", "#1e40af"
                        else:
                            bg, fg = "#fef08a", "#854d0e"
                            
                        if t['completed']:
                            bg, fg = "#334155", "#94a3b8"
                            t_style = "text-decoration: line-through; color: #94a3b8;"
                        else:
                            t_style = f"color: {fg}; font-weight: bold;"

                        badges_html += f"<span style='font-size:9px; background:{bg}; color:{fg}; padding:1px 3px; border-radius:3px; white-space:nowrap;'><b style='{t_style}'>{cat}</b></span>"
                    badges_html += "</div>"
                    
                    if len(day_tasks) > 6:
                        badges_html += f"<div style='font-size:8px; color:gray; margin-top:1px;'>외 {len(day_tasks)-6}건</div>"
                        
                    st.markdown(f"<div style='min-height:75px;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"### 📌 선택한 날짜: {st.session_state['selected_date']} 업무 현황")
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        
        if not target_tasks:
            st.info("선택된 날짜에 등록된 업무가 없습니다. 우측에서 일정을 등록해 보세요.")
        else:
            for task in target_tasks:
                box_style = "border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 14px; background-color: #0e1117;"

                cols_t = st.columns([0.15, 0.65, 0.2])
                is_checked = cols_t[0].checkbox("완료", value=task['completed'], key=f"chk_{task['id']}")
                
                if is_checked != task['completed']:
                    task['completed'] = is_checked
                    task['completed_date'] = str(date.today()) if is_checked else None
                    st.rerun()

                if cols_t[2].button("✏️ 수정", key=f"edit_btn_{task['id']}"):
                    st.session_state['editing_task_id'] = task['id']
                    st.rerun()

                cat = task['category']
                if cat == '고객제출':
                    c_bg, c_fg = "#fee2e2", "#991b1b"
                elif cat == '자료작성':
                    c_bg, c_fg = "#dbeafe", "#1e40af"
                else:
                    c_bg, c_fg = "#fef08a", "#854d0e"

                update_tag = f" | <span style='color: #f59e0b; font-size: 12px;'>수정일자 : {task['updated_date']}</span>" if task.get('updated_date') else ""

                if task['completed']:
                    card_html = f"""
                        <div style='{box_style}'>
                            <span style='color: #94a3b8; text-decoration: line-through; font-size: 18px; font-weight: bold;'>{task['title']}</span> 
                            <span style='font-size:12px; background:#334155; color:#94a3b8; padding:2px 6px; border-radius:4px;'>{cat}</span>{update_tag}<br>
                            <div style='font-size: 14px; color: #94a3b8; margin-top: 6px;'>
                                <b>요청자:</b> {task['requester']}<br>
                                <b>마감기한:</b> {task['deadline']}<br>
                                <b>메모 및 상세 내용:</b> {task['memo']}
                            </div>
                            <small style='color:#22c55e;'><b>[처리완료일: {task.get('completed_date', '-')}]</b></small>
                        </div>
                    """
                else:
                    card_html = f"""
                        <div style='{box_style}'>
                            <span style='font-size: 18px; font-weight: bold; color: white;'>{task['title']}</span> 
                            <span style='font-size:12px; background:{c_bg}; color:{c_fg}; padding:2px 6px; border-radius:4px; font-weight:bold;'>{cat}</span>{update_tag}<br>
                            <div style='font-size: 14px; color: #e2e8f0; margin-top: 6px; line-height: 1.5;'>
                                <b>요청자:</b> {task['requester']}<br>
                                <b>마감기한:</b> {task['deadline']}<br>
                                <b>메모 및 상세 내용:</b> {task['memo']}
                            </div>
                        </div>
                    """
                cols_t[1].markdown(card_html, unsafe_allow_html=True)

    with col_right:
        editing_task = None
        if st.session_state['editing_task_id'] is not None:
            for t in st.session_state['tasks']:
                if t['id'] == st.session_state['editing_task_id']:
                    editing_task = t
                    break

        if editing_task:
            st.markdown(f"### ✏️ 기존 업무 내용 수정 (ID: {editing_task['id']})")
            if st.button("❌ 수정 취소하기"):
                st.session_state['editing_task_id'] = None
                st.rerun()
        else:
            st.markdown("### ✍️ 신규 일정 등록")

        def_title = editing_task['title'] if editing_task else ""
        def_date = editing_task['date'] if editing_task else st.session_state['selected_date']
        def_deadline = editing_task['deadline'] if editing_task else date.today()
        
        categories = ["고객제출", "업체접수", "자료작성"]
        def_cat_idx = categories.index(editing_task['category']) if editing_task and editing_task['category'] in categories else 0
        
        def_requester = editing_task['requester'] if editing_task else ""
        def_memo = editing_task['memo'] if editing_task else ""

        with st.form("task_manage_form"):
            f_title = st.text_input("업무 제목", value=def_title)
            f_date = st.date_input("일정 날짜 (달력 반영일)", value=def_date)
            f_deadline = st.date_input("마감 기한", value=def_deadline)
            f_category = st.selectbox("카테고리 선택", categories, index=def_cat_idx)
            f_requester = st.text_input("요청자", value=def_requester)
            f_memo = st.text_area("메모 및 상세 내용", value=def_memo)
            
            col_f1, col_f2 = st.columns(2)
            submitted_new = col_f1.form_submit_button("일정 저장 및 달력 반영", use_container_width=True)
            submitted_update = col_f2.form_submit_button("내용 수정/등록", use_container_width=True)

            if submitted_new:
                if editing_task:
                    st.warning("현재 수정 모드입니다. 신규 등록은 '수정 취소하기' 후 진행해 주세요.")
                elif f_title.strip() == "":
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
                        "completed_date": None,
                        "updated_date": None
                    }
                    st.session_state['tasks'].append(new_task)
                    st.success("일정이 성공적으로 저장되었습니다!")
                    st.rerun()

            if submitted_update:
                if not editing_task:
                    st.warning("수정할 업무를 선택해주세요. (업무 카드 우측의 '수정' 버튼 클릭)")
                elif f_title.strip() == "":
                    st.warning("업무 제목을 입력해주세요.")
                else:
                    editing_task['title'] = f_title
                    editing_task['date'] = f_date
                    editing_task['deadline'] = f_deadline
                    editing_task['category'] = f_category
                    editing_task['requester'] = f_requester
                    editing_task['memo'] = f_memo
                    editing_task['updated_date'] = datetime.today().strftime('%y-%m-%d')
                    
                    st.session_state['editing_task_id'] = None
                    st.success("업무 내용이 성공적으로 수정되었습니다!")
                    st.rerun()

elif menu == "필드 클레임 현황":
    st.subheader("📈 클레임 RAW DATA 분석 및 시각화 대시보드")
    st.markdown("첨부된 엑셀 파일 또는 업로드된 데이터를 기반으로 품목별, 차종별, 현상별 필드 클레임 추이와 다각도 분석 그래프를 확인하세요.")

    # 1. 파일 자동 감지 또는 업로드
    default_files = [f for f in os.listdir('.') if f.endswith('.xlsx') or f.endswith('.csv')]
    uploaded_file = st.file_uploader("클레임 RAW DATA 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])

    @st.cache_data
    def load_claim_data(path_or_file):
        try:
            if isinstance(path_or_file, str):
                df = pd.read_excel(path_or_file, sheet_name=0)
            else:
                if path_or_file.name.endswith('.csv'):
                    df = pd.read_csv(path_or_file)
                else:
                    df = pd.read_excel(path_or_file)
            return df
        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()

    if uploaded_file is not None:
        df = load_claim_data(uploaded_file)
    elif default_files:
        # 현재 폴더에 있는 첨부 엑셀 파일 자동 로드
        target_file = [f for f in default_files if "RO LIST" in f or "생산" in f]
        df = load_claim_data(target_file[0] if target_file else default_files[0])
    else:
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("---")
        st.markdown("#### 🔍 조회 조건 필터 (차종, 품번, 부품명, 현상코드, 현상명, 생산월, 판매월, 수리월, 사용개월, 주행거리, 판매국가, VIN, 공장 등)")

        # 필터 UI 배치 (4열)
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            car_types = ["전체"] + sorted(list(df['차종'].dropna().unique())) if '차종' in df.columns else ["전체"]
            selected_car = st.selectbox("차종", car_types)

            part_nos = ["전체"] + sorted(list(df['품번'].dropna().unique())) if '품번' in df.columns else ["전체"]
            selected_part_no = st.selectbox("품번", part_nos)

            part_names = ["전체"] + sorted(list(df['부품명'].dropna().unique())) if '부품명' in df.columns else ["전체"]
            selected_part_name = st.selectbox("부품명", part_names)

        with f_col2:
            phen_codes = ["전체"] + sorted(list(df['현상코드'].dropna().unique())) if '현상코드' in df.columns else ["전체"]
            selected_phen_code = st.selectbox("현상코드", phen_codes)

            phen_names = ["전체"] + sorted(list(df['현상명'].dropna().unique())) if '현상명' in df.columns else ["전체"]
            selected_phen_name = st.selectbox("현상명", phen_names)

            countries = ["전체"] + sorted(list(df['판매국가'].dropna().unique())) if '판매국가' in df.columns else ["전체"]
            selected_country = st.selectbox("판매국가", countries)

        with f_col3:
            plants = ["전체"] + sorted(list(df['공장'].dropna().unique())) if '공장' in df.columns else ["전체"]
            selected_plant = st.selectbox("공장", plants)

            vins = ["전체"] + sorted(list(df['VIN'].dropna().unique())) if 'VIN' in df.columns else ["전체"]
            selected_vin = st.selectbox("VIN", vins)

            # AY~BL 추가 항목 필터 예시 (수리월 / 생산월 등)
            repair_months = ["전체"] + sorted(list(df['수리월'].dropna().unique())) if '수리월' in df.columns else ["전체"]
            selected_repair_month = st.selectbox("수리월", repair_months)

        with f_col4:
            prod_months = ["전체"] + sorted(list(df['생산월'].dropna().unique())) if '생산월' in df.columns else ["전체"]
            selected_prod_month = st.selectbox("생산월", prod_months)

            # 사용개월 / 주행거리 슬라이더 필터
            max_usage = int(df['사용개월'].max()) if '사용개월' in df.columns and not df['사용개월'].isnull().all() else 60
            selected_usage = st.slider("사용개월 최대값", 0, max_usage if max_usage > 0 else 60, max_usage if max_usage > 0 else 60)

            max_mile = int(df['주행거리Km'].max()) if '주행거리Km' in df.columns and not df['주행거리Km'].isnull().all() else 100000
            selected_mile = st.slider("주행거리(Km) 최대값", 0, max_mile if max_mile > 0 else 100000, max_mile if max_mile > 0 else 100000)

        # 필터링 적용
        filtered_df = df.copy()
        if selected_car != "전체":
            filtered_df = filtered_df[filtered_df['차종'] == selected_car]
        if selected_part_no != "전체":
            filtered_df = filtered_df[filtered_df['품번'] == selected_part_no]
        if selected_part_name != "전체":
            filtered_df = filtered_df[filtered_df['부품명'] == selected_part_name]
        if selected_phen_code != "전체":
            filtered_df = filtered_df[filtered_df['현상코드'] == selected_phen_code]
        if selected_phen_name != "전체":
            filtered_df = filtered_df[filtered_df['현상명'] == selected_phen_name]
        if selected_country != "전체":
            filtered_df = filtered_df[filtered_df['판매국가'] == selected_country]
        if selected_plant != "전체":
            filtered_df = filtered_df[filtered_df['공장'] == selected_plant]
        if selected_vin != "전체":
            filtered_df = filtered_df[filtered_df['VIN'] == selected_vin]
        if selected_repair_month != "전체":
            filtered_df = filtered_df[filtered_df['수리월'] == selected_repair_month]
        if selected_prod_month != "전체":
            filtered_df = filtered_df[filtered_df['생산월'] == selected_prod_month]
        if '사용개월' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['사용개월'] <= selected_usage]
        if '주행거리Km' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['주행거리Km'] <= selected_mile]

        st.markdown("---")

        # 3. 상단: 꺾은선 그래프 (수리월 / 생산월 기준 추이 분석)
        st.markdown("### 1. 차종/기간별 클레임 추이 분석 (꺾은선 그래프)")
        if not filtered_df.empty and '수리월' in filtered_df.columns:
            trend_data = filtered_df.groupby('수리월').size().reset_index(name='클레임 건수')
            st.line_chart(trend_data.set_index('수리월'))
        else:
            st.info("표시할 트렌드 데이터가 없습니다.")

        st.markdown("---")

        # 4. 하단: 현상, 사용개월, 주행거리, 차종별 막대 그래프 분석
        st.markdown("### 2. 다각도 클레임 현황 분석 (막대 그래프)")
        
        b_col1, b_col2 = st.columns(2)

        with b_col1:
            st.markdown("##### 📊 현상별 클레임 현황")
            if not filtered_df.empty and '현상명' in filtered_df.columns:
                phen_chart = filtered_df.groupby('현상명').size()
                st.bar_chart(phen_chart)
            else:
                st.info("데이터 없음")

            st.markdown("##### 📊 주행거리별 클레임 현황")
            if not filtered_df.empty and '주행거리Km' in filtered_df.columns:
                filtered_df['주행거리_구간'] = pd.cut(
                    filtered_df['주행거리Km'], 
                    bins=[0, 10000, 30000, 50000, 70000, 100000, 999999], 
                    labels=['~10000', '~30000', '~50000', '~70000', '~100000', '100000~']
                )
                mile_chart = filtered_df.groupby('주행거리_구간', observed=False).size()
                st.bar_chart(mile_chart)
            else:
                st.info("데이터 없음")

        with b_col2:
            st.markdown("##### 📊 사용개월별 클레임 현황")
            if not filtered_df.empty and '사용개월' in filtered_df.columns:
                usage_chart = filtered_df.groupby('사용개월').size()
                st.bar_chart(usage_chart)
            else:
                st.info("데이터 없음")

            st.markdown("##### 📊 차종별 클레임 현황")
            if not filtered_df.empty and '차종' in filtered_df.columns:
                model_chart = filtered_df.groupby('차종').size()
                st.bar_chart(model_chart)
            else:
                st.info("데이터 없음")

        st.markdown("---")
        st.markdown(f"##### 📋 선택된 조건의 상세 RAW DATA 테이블 조회 (총 {len(filtered_df)}건)")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("분석할 클레임 데이터 파일이 없습니다. 엑셀 파일을 업로드해 주세요.")

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
