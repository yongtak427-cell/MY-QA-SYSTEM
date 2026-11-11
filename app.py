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
    st.markdown("클레임 RAW DATA 엑셀 파일을 업로드하여 품목별, 차종별, 현상별 필드 클레임 추이와 다각도 분석 그래프를 확인하세요.")

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
    else:
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("---")
        st.markdown("#### 🔍 클레임 조회 (스크롤 선택 및 직접 검색 가능)")

        # 멀티셀렉트 내장 검색 활용 (사용자가 클릭해서 스크롤로 고르거나 키워드 입력 가능)
        def get_multiselect_filter(label, col_name):
            if col_name in df.columns:
                options = sorted([str(x) for x in df[col_name].dropna().unique()])
                return st.multiselect(f"{label} (검색 및 다중 선택)", options, key=f"filter_{col_name}")
            return []

        # 요청하신 3줄 배치 구조 반영
        # 첫째 줄: 품번(품목), 부품명, 차종, 현상명, 현상상세
        # 둘째 줄: 생산월, 판매월, 수리월, 사용개월, 주행거리
        # 셋째 줄: VIN, 판매국가, 공장

        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
        with r1_c1:
            selected_part_nos = get_multiselect_filter("품번", "품번")
        with r1_c2:
            selected_part_names = get_multiselect_filter("부품명", "부품명")
        with r1_c3:
            selected_cars = get_multiselect_filter("차종", "차종")
        with r1_c4:
            selected_phen_names = get_multiselect_filter("현상명", "현상명")
        with r1_c5:
            selected_phen_details = get_multiselect_filter("현상상세", "현상상세")

        r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
        with r2_c1:
            selected_prod_months = get_multiselect_filter("생산월", "생산월")
        with r2_c2:
            selected_sales_months = get_multiselect_filter("판매월", "판매월")
        with r2_c3:
            selected_repair_months = get_multiselect_filter("수리월", "수리월")
        with r2_c4:
            usage_options = [3, 6, 9, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]
            selected_usages = st.multiselect("사용개월 선택", usage_options, format_func=lambda x: f"{x}개월" if x<=12 else f"{x}개월")
        with r2_c5:
            mile_options = [5000, 10000, 30000, 50000, 70000, 100000, 999999]
            selected_miles = st.multiselect("주행거리 구간 선택", mile_options, format_func=lambda x: "100,000 이상" if x==999999 else f"{x:,} 이하")

        r3_c1, r3_c2, r3_c3 = st.columns(3)
        with r3_c1:
            selected_vins = get_multiselect_filter("VIN", "VIN")
        with r3_c2:
            selected_countries = get_multiselect_filter("판매국가", "판매국가")
        with r3_c3:
            selected_plants = get_multiselect_filter("공장", "공장")

        # 필터링 적용 로직
        filtered_df = df.copy()
        if selected_part_nos:
            filtered_df = filtered_df[filtered_df['품번'].astype(str).isin(selected_part_nos)]
        if selected_part_names:
            filtered_df = filtered_df[filtered_df['부품명'].astype(str).isin(selected_part_names)]
        if selected_cars:
            filtered_df = filtered_df[filtered_df['차종'].astype(str).isin(selected_cars)]
        if selected_phen_names:
            filtered_df = filtered_df[filtered_df['현상명'].astype(str).isin(selected_phen_names)]
        if selected_phen_details and '현상상세' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['현상상세'].astype(str).isin(selected_phen_details)]
        if selected_prod_months:
            filtered_df = filtered_df[filtered_df['생산월'].astype(str).isin(selected_prod_months)]
        if selected_sales_months and '판매월' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['판매월'].astype(str).isin(selected_sales_months)]
        if selected_repair_months:
            filtered_df = filtered_df[filtered_df['수리월'].astype(str).isin(selected_repair_months)]
        if selected_vins:
            filtered_df = filtered_df[filtered_df['VIN'].astype(str).isin(selected_vins)]
        if selected_countries:
            filtered_df = filtered_df[filtered_df['판매국가'].astype(str).isin(selected_countries)]
        if selected_plants:
            filtered_df = filtered_df[filtered_df['공장'].astype(str).isin(selected_plants)]

        if selected_usages and '사용개월' in filtered_df.columns:
            usage_mask = pd.Series(False, index=filtered_df.index)
            for u in selected_usages:
                if u == 3:
                    usage_mask |= (filtered_df['사용개월'] >= 0) & (filtered_df['사용개월'] <= 3)
                elif u == 6:
                    usage_mask |= (filtered_df['사용개월'] >= 4) & (filtered_df['사용개월'] <= 6)
                elif u == 9:
                    usage_mask |= (filtered_df['사용개월'] >= 7) & (filtered_df['사용개월'] <= 9)
                elif u == 12:
                    usage_mask |= (filtered_df['사용개월'] >= 10) & (filtered_df['사용개월'] <= 12)
                else:
                    prev_u = u - 12 if u > 12 else 12
                    usage_mask |= (filtered_df['사용개월'] > prev_u) & (filtered_df['사용개월'] <= u)
            filtered_df = filtered_df[usage_mask]

        if selected_miles and '주행거리Km' in filtered_df.columns:
            mile_mask = pd.Series(False, index=filtered_df.index)
            for m in selected_miles:
                if m == 5000:
                    mile_mask |= (filtered_df['주행거리Km'] >= 0) & (filtered_df['주행거리Km'] <= 5000)
                elif m == 10000:
                    mile_mask |= (filtered_df['주행거리Km'] > 5000) & (filtered_df['주행거리Km'] <= 10000)
                elif m == 30000:
                    mile_mask |= (filtered_df['주행거리Km'] > 10000) & (filtered_df['주행거리Km'] <= 30000)
                elif m == 50000:
                    mile_mask |= (filtered_df['주행거리Km'] > 30000) & (filtered_df['주행거리Km'] <= 50000)
                elif m == 70000:
                    mile_mask |= (filtered_df['주행거리Km'] > 50000) & (filtered_df['주행거리Km'] <= 70000)
                elif m == 100000:
                    mile_mask |= (filtered_df['주행거리Km'] > 70000) & (filtered_df['주행거리Km'] <= 100000)
                elif m == 999999:
                    mile_mask |= (filtered_df['주행거리Km'] > 100000)
            filtered_df = filtered_df[mile_mask]

        st.markdown("---")

        # 3. 상단: 클레임 추이 분석 (Streamlit 네이티브 통합 차트 - 크기 조절/인터랙션 가능)
        st.markdown("### 1. 차종/기간별 클레임 추이 분석 (생산월 파란색 막대 & 수리월 빨간색 꺾은선 통합)")
        if not filtered_df.empty:
            chart_df = pd.DataFrame()
            if '수리월' in filtered_df.columns:
                repair_trend = filtered_df.groupby('수리월').size().rename('수리건수 (꺾은선)')
                chart_df = pd.concat([chart_df, repair_trend], axis=1)
            if '생산월' in filtered_df.columns:
                prod_trend = filtered_df.groupby('생산월').size().rename('생산건수 (막대)')
                chart_df = pd.concat([chart_df, prod_trend], axis=1)
            
            chart_df = chart_df.fillna(0).sort_index()

            if not chart_df.empty:
                # Streamlit 기본 차트 (막대 + 꺾은선 통합 표시)
                st.bar_chart(chart_df, color=["#3b82f6", "#ef4444"])
                st.markdown("<p style='font-size:12px; color:gray;'>💡 우측 상단 아이콘으로 전체화면 보기 및 크기 조절이 가능합니다.</p>", unsafe_allow_html=True)
            else:
                st.info("시각화할 데이터가 없습니다.")
        else:
            st.info("표시할 트렌드 데이터가 없습니다.")

        st.markdown("---")

        # 4. 하단: 현상, 사용개월, 주행거리, 차종별 막대 그래프 분석
        st.markdown("### 2. 다각도 클레임 현황 분석 (막대 그래프)")
        
        b_col1, b_col2 = st.columns(2)

        with b_col1:
            st.markdown("##### 📊 현상명별 클레임 현황")
            if not filtered_df.empty and '현상명' in filtered_df.columns:
                phen_chart = filtered_df.groupby('현상명').size()
                st.bar_chart(phen_chart)
            else:
                st.info("데이터 없음")

            st.markdown("##### 📊 주행거리별 클레임 현황")
            if not filtered_df.empty and '주행거리Km' in filtered_df.columns:
                filtered_df['주행거리_구간'] = pd.cut(
                    filtered_df['주행거리Km'], 
                    bins=[0, 5000, 10000, 30000, 50000, 70000, 100000, 999999], 
                    labels=['~5000', '5001~10000', '10001~30000', '30001~50000', '50001~70000', '70001~100000', '100000이상']
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
        st.info("분석할 클레임 엑셀 파일을 업로드해 주세요.")

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
