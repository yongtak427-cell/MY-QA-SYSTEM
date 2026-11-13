import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 페이지 설정 (레이아웃 넓게 설정)
st.set_page_config(page_title="TIKITAK Task Management", page_icon="📊", layout="wide")

# CSS 스타일: 화면 여백 최적화 및 테이블 내 텍스트 줄바꿈/세로 정렬 허용
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
    div[data-testid="column"] button {
        width: auto !important;
        min-width: 60px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 14px !important;
    }
    /* st.dataframe 내부 텍스트 줄바꿈 및 상하 정렬 보장 */
    div[data-testid="stDataFrame"] td {
        white-space: pre-wrap !important;
        vertical-align: middle !important;
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

if 'cal_year' not in st.session_state: st.session_state['cal_year'] = datetime.today().year
if 'cal_month' not in st.session_state: st.session_state['cal_month'] = datetime.today().month
if 'selected_date' not in st.session_state: st.session_state['selected_date'] = date.today()
if 'editing_task_id' not in st.session_state: st.session_state['editing_task_id'] = None

if 'delete_confirm_id' not in st.session_state: st.session_state['delete_confirm_id'] = None
if 'save_confirm_type' not in st.session_state: st.session_state['save_confirm_type'] = None
if 'pending_form_data' not in st.session_state: st.session_state['pending_form_data'] = None

if 'claim_df' not in st.session_state: st.session_state['claim_df'] = pd.DataFrame()
if 'cost_df' not in st.session_state: st.session_state['cost_df'] = pd.DataFrame()
if 'uploaded_file_name' not in st.session_state: st.session_state['uploaded_file_name'] = None
if 'improve_uploaded_file_name' not in st.session_state: st.session_state['improve_uploaded_file_name'] = None
if 'cost_uploaded_file_name' not in st.session_state: st.session_state['cost_uploaded_file_name'] = None

if 'gsheet_url' not in st.session_state: st.session_state['gsheet_url'] = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQoePTO6LK-r65996JMmTMfdC-D8zuj83sa_YBQ4VxyFsq8ZRTaXBbiI5ZmPVngpkrPK-soa9P8IetD/pubhtml"
if 'improve_gsheet_url' not in st.session_state: st.session_state['improve_gsheet_url'] = ""
if 'cost_gsheet_url' not in st.session_state: st.session_state['cost_gsheet_url'] = ""

if 'improve_df' not in st.session_state:
    raw_data = [
        {'대상': '승용', '품명': '워터펌프', '차종': '람다', '현상': '누수/소음', '대책 내용': 'M/SEAL M/R 재질 환원(ES5 ▶ ES4)', '해당 품목': '25100-3CAC0', '고객사명': '-', '적용일': '2016-06-27', '비 고': ''},
        {'대상': '승용', '품명': '워터펌프', '차종': '람다', '현상': '소음', '대책 내용': 'M/SEAL M/R 조도 하한품 적용', '해당 품목': '25100-3CAC0', '고객사명': 'HMC', '적용일': '2021-11-16', '비 고': ''},
        {'대상': '승용', '품명': '워터펌프', '차종': '감마 II', '현상': '누수', '대책 내용': '·설계 변경\n  └ BODY 드레인챔버 용량 증대 (7.4cc ▶ 14cc)', '해당 품목': '25100-2M013', '고객사명': 'WIA', '적용일': '2025-12-03', '비 고': ''}
    ]
    df_init = pd.DataFrame(raw_data)
    df_init.insert(0, 'id', range(1, len(df_init) + 1))
    st.session_state['improve_df'] = df_init

# 사이드바 메뉴 (Menu List)
st.sidebar.markdown("## Menu List")
menu_options = ["종합 현황", "업무 등록/관리", "필드 클레임 현황", "개선 활동 관리", "고객사 클레임 비용 분석", "구글 시트 연동 설정"]
menu = st.sidebar.radio("메뉴 선택", menu_options, label_visibility="collapsed")

st.markdown("---")

# --- 0. 종합 현황 메뉴 ---
if menu == "종합 현황":
    st.subheader("주간 업무 종합 현황 요약")
    tasks = st.session_state['tasks']
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    weekly_tasks = [t for t in tasks if start_of_week <= t['date'] <= end_of_week]
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("이번 주 총 업무 건수", f"{len(weekly_tasks)} 건")
    col_s2.metric("완료된 건수", f"{len([t for t in weekly_tasks if t['completed']])} 건")
    col_s3.metric("미결(진행중) 건수", f"{len(weekly_tasks) - len([t for t in weekly_tasks if t['completed']]):} 건")

    st.markdown("---")
    st.markdown(f"이번 주 ({start_of_week} ~ {end_of_week}) 상세 업무 리스트")
    if not weekly_tasks:
        st.info("이번 주에 등록된 업무가 없습니다.")
    else:
        weekly_df = pd.DataFrame([{
            "ID": t['id'], "날짜": t['date'], "제목": t['title'],
            "카테고리": t['category'], "요청자": t['requester'],
            "마감기한": t['deadline'], "상태": "완료" if t['completed'] else "미결"
        } for t in weekly_tasks])
        st.dataframe(weekly_df, use_container_width=True)

# --- 1. 업무 등록/관리 메뉴 ---
elif menu == "업무 등록/관리":
    st.subheader("월별 업무 관리 현황")
    
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
                btn_text = f"{day}일 ({len(day_tasks)}건)" if len(day_tasks) > 0 else f"{day}"

                with w_cols[i]:
                    if st.button(btn_text, key=f"cal_btn_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        st.session_state['selected_date'] = current_d
                        st.rerun()
                    
                    badges_html = "<div style='display: flex; flex-wrap: wrap; gap: 2px; justify-content: flex-start;'>"
                    for t in day_tasks[:6]:
                        cat = t['category']
                        bg, fg = ("#fee2e2", "#991b1b") if cat == '고객제출' else ("#dbeafe", "#1e40af") if cat == '자료작성' else ("#fef08a", "#854d0e")
                        t_style = "text-decoration: line-through; color: #94a3b8;" if t['completed'] else f"color: {fg}; font-weight: bold;"
                        badges_html += f"<span style='font-size:9px; background:{bg}; color:{fg}; padding:1px 3px; border-radius:3px;'><b style='{t_style}'>{cat}</b></span>"
                    badges_html += "</div>"
                    st.markdown(f"<div style='min-height:75px;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"### 업무현황 ({st.session_state['selected_date']})")
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        if not target_tasks:
            st.info("선택된 날짜에 등록된 업무가 없습니다.")
        else:
            for task in target_tasks:
                box_style = "border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 14px; background-color: #0e1117;"
                cols_t = st.columns([0.88, 0.12])
                cat = task['category']
                c_bg, c_fg = ("#fee2e2", "#991b1b") if cat == '고객제출' else ("#dbeafe", "#1e40af") if cat == '자료작성' else ("#fef08a", "#854d0e")
                update_tag = f" | <span style='color: #f59e0b; font-size: 12px;'>수정일자 : {task['updated_date']}</span>" if task.get('updated_date') else ""

                card_html = f"""
                    <div style='{box_style}'>
                        <span style='font-size: 18px; font-weight: bold; color: white;'>{task['title']}</span> 
                        <span style='font-size:12px; background:{c_bg}; color:{c_fg}; padding:2px 6px; border-radius:4px; font-weight:bold;'>{cat}</span>{update_tag}<br>
                        <div style='font-size: 14px; color: #e2e8f0; margin-top: 6px; line-height: 1.5; white-space: pre-wrap;'><b>요청자:</b> {task['requester']}
<b>마감기한:</b> {task['deadline']}
<b>메모 및 상세 내용:</b>
{task['memo']}</div>
                    </div>
                """
                cols_t[0].markdown(card_html, unsafe_allow_html=True)
                with cols_t[1]:
                    comp_label = "완료취소" if task['completed'] else "완료"
                    if st.button(comp_label, key=f"comp_btn_{task['id']}", use_container_width=True):
                        task['completed'] = not task['completed']
                        task['completed_date'] = str(date.today()) if task['completed'] else None
                        st.rerun()
                    if st.button("수정", key=f"edit_btn_{task['id']}", use_container_width=True):
                        st.session_state['editing_task_id'] = task['id']
                        st.session_state['delete_confirm_id'] = None
                        st.rerun()
                    if st.button("삭제", key=f"del_btn_{task['id']}", use_container_width=True):
                        st.session_state['delete_confirm_id'] = task['id']
                        st.session_state['editing_task_id'] = None
                        st.rerun()

                if st.session_state['delete_confirm_id'] == task['id']:
                    st.warning(f"'{task['title']}' 업무를 정말 삭제하시겠습니까?")
                    d_col1, d_col2 = st.columns(2)
                    if d_col1.button("삭제", key=f"confirm_del_{task['id']}", use_container_width=True):
                        st.session_state['tasks'] = [t for t in st.session_state['tasks'] if t['id'] != task['id']]
                        st.session_state['delete_confirm_id'] = None
                        st.success("삭제되었습니다.")
                        st.rerun()
                    if d_col2.button("취소", key=f"cancel_del_{task['id']}", use_container_width=True):
                        st.session_state['delete_confirm_id'] = None
                        st.rerun()

    with col_right:
        editing_task = next((t for t in st.session_state['tasks'] if t['id'] == st.session_state['editing_task_id']), None)
        if editing_task:
            st.markdown(f"### 기존 업무 내용 수정 (ID: {editing_task['id']})")
            if st.button("수정 취소하기"):
                st.session_state['editing_task_id'] = None
                st.rerun()
        else:
            st.markdown("### 신규 일정 등록")

        if st.session_state['save_confirm_type'] is not None:
            action_name = "신규 등록" if st.session_state['save_confirm_type'] == 'new' else "수정"
            st.warning(f"정말 {action_name}하시겠습니까?")
            c_col1, c_col2 = st.columns(2)
            if c_col1.button("등록", use_container_width=True):
                data = st.session_state['pending_form_data']
                if st.session_state['save_confirm_type'] == 'new':
                    st.session_state['tasks'].append({
                        "id": len(st.session_state['tasks']) + 1, "title": data['title'],
                        "date": data['date'], "deadline": data['deadline'], "memo": data['memo'],
                        "requester": data['requester'], "category": data['category'],
                        "completed": False, "completed_date": None, "updated_date": None
                    })
                    st.success("신규 등록되었습니다!")
                else:
                    target_t = next((t for t in st.session_state['tasks'] if t['id'] == st.session_state['editing_task_id']), None)
                    if target_t:
                        target_t.update({
                            "title": data['title'], "date": data['date'], "deadline": data['deadline'],
                            "category": data['category'], "requester": data['requester'], "memo": data['memo'],
                            "updated_date": datetime.today().strftime('%y-%m-%d')
                        })
                        st.session_state['editing_task_id'] = None
                        st.success("수정되었습니다!")
                st.session_state['save_confirm_type'] = None
                st.session_state['pending_form_data'] = None
                st.rerun()
            if c_col2.button("취소", use_container_width=True):
                st.session_state['save_confirm_type'] = None
                st.session_state['pending_form_data'] = None
                st.rerun()
        else:
            with st.form("task_manage_form"):
                f_title = st.text_input("업무 제목", value=editing_task['title'] if editing_task else "")
                f_date = st.date_input("작성 일자", value=editing_task['date'] if editing_task else st.session_state['selected_date'])
                f_deadline = st.date_input("마감 기한", value=editing_task['deadline'] if editing_task else st.session_state['selected_date'])
                categories = ["고객제출", "업체접수", "자료작성", "업무 확인", "업무 협의", "회의"]
                f_category = st.selectbox("카테고리 선택", categories, index=categories.index(editing_task['category']) if editing_task and editing_task['category'] in categories else 0)
                f_requester = st.text_input("요청자", value=editing_task['requester'] if editing_task else "")
                f_memo = st.text_area("메모 및 상세 내용", value=editing_task['memo'] if editing_task else "")
                
                col_f1, col_f2 = st.columns(2)
                submitted_new = col_f1.form_submit_button("신규등록", use_container_width=True)
                submitted_update = col_f2.form_submit_button("내용 수정/등록", use_container_width=True)

                if submitted_new and not editing_task and f_title.strip():
                    st.session_state['pending_form_data'] = {"title": f_title, "date": f_date, "deadline": f_deadline, "category": f_category, "requester": f_requester, "memo": f_memo}
                    st.session_state['save_confirm_type'] = 'new'
                    st.rerun()
                if submitted_update and editing_task and f_title.strip():
                    st.session_state['pending_form_data'] = {"title": f_title, "date": f_date, "deadline": f_deadline, "category": f_category, "requester": f_requester, "memo": f_memo}
                    st.session_state['save_confirm_type'] = 'update'
                    st.rerun()

# --- 2. 필드 클레임 현황 메뉴 ---
elif menu == "필드 클레임 현황":
    st.subheader("클레임 RAW DATA 분석 및 시각화 대시보드")
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader("클레임 RAW DATA 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])
    with col_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_gsheet_btn = st.button("구글 시트 데이터 자동 불러오기", use_container_width=True)

    def process_raw_dataframe(df_raw):
        cols = list(df_raw.columns)
        if len(cols) > 63: cols[63] = '현상명'
        if len(cols) > 59: cols[59] = '현상상세'
        seen, new_cols = {}, []
        for c in cols:
            if c in seen:
                seen[c] += 1
                new_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                new_cols.append(c)
        df_raw.columns = new_cols
        if len(df_raw.columns) > 63: df_raw['현상명'] = df_raw.iloc[:, 63].astype(str)
        if '사용개월' in df_raw.columns: df_raw['사용개월'] = pd.to_numeric(df_raw['사용개월'], errors='coerce').fillna(0)
        if '주행거리Km' in df_raw.columns: df_raw['주행거리Km'] = pd.to_numeric(df_raw['주행거리Km'], errors='coerce').fillna(0)
        return df_raw

    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, sheet_name=0)
            st.session_state['claim_df'] = process_raw_dataframe(raw_df)
            st.session_state['uploaded_file_name'] = uploaded_file.name
        except Exception as e:
            st.error(f"오류: {e}")

    if load_gsheet_btn:
        try:
            sheet_url = st.session_state['gsheet_url']
            if "pubhtml" in sheet_url:
                export_url = sheet_url.replace("/pubhtml", "/pub?output=csv")
            elif "edit" in sheet_url:
                export_url = sheet_url.split('/edit')[0] + '/export?format=csv'
            else:
                export_url = sheet_url
            raw_df = pd.read_csv(export_url)
            if not raw_df.empty:
                if 'No.' not in str(raw_df.columns):
                    raw_df.columns = raw_df.iloc[0]
                    raw_df = raw_df[1:].reset_index(drop=True)
                raw_df = process_raw_dataframe(raw_df)
                st.session_state['claim_df'] = raw_df
                st.success("구글 시트 데이터 로드 성공!")
                st.rerun()
        except Exception as e:
            st.error(f"구글 시트 연동 오류: {e}")

    df = st.session_state['claim_df']
    if not df.empty:
        st.markdown("---")
        def get_multiselect_filter(label, col_name, custom_options=None):
            if col_name in df.columns:
                options = custom_options if custom_options is not None else sorted([str(x) for x in df[col_name].dropna().unique()])
                return st.multiselect(f"{label}", options, key=f"filter_{col_name}")
            return []

        phenomenon_options = ["누수", "소음", "기타"]
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
        with r1_c1: selected_part_nos = get_multiselect_filter("품번", "품번")
        with r1_c2: selected_part_names = get_multiselect_filter("부품명", "부품명")
        with r1_c3: selected_cars = get_multiselect_filter("차종", "차종")
        with r1_c4: selected_phen_names = get_multiselect_filter("현상명 (누수/소음/기타)", "현상명", custom_options=phenomenon_options)
        with r1_c5: selected_phen_details = get_multiselect_filter("현상상세", "현상상세")

        r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
        with r2_c1: selected_prod_months = get_multiselect_filter("생산월", "생산월")
        with r2_c2: selected_sales_months = get_multiselect_filter("판매월", "판매월")
        with r2_c3: selected_repair_months = get_multiselect_filter("수리월", "수리월")
        with r2_c4: 
            usage_options = [3, 6, 9, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]
            selected_usages = st.multiselect("사용개월", usage_options, format_func=lambda x: f"{x}개월", key="filter_usage")
        with r2_c5:
            mile_options = [5000, 10000, 30000, 50000, 70000, 100000, 999999]
            selected_miles = st.multiselect("주행거리 구간", mile_options, format_func=lambda x: "100,000 이상" if x==999999 else f"{x:,} 이하", key="filter_mile")

        r3_c1, r3_c2, r3_c3 = st.columns(3)
        with r3_c1: selected_vins = get_multiselect_filter("VIN", "VIN")
        with r3_c2: selected_countries = get_multiselect_filter("판매국가", "판매국가")
        with r3_c3: selected_plants = get_multiselect_filter("공장", "공장")

        filtered_df = df.copy()
        if selected_part_nos and '품번' in filtered_df.columns: filtered_df = filtered_df[filtered_df['품번'].astype(str).isin(selected_part_nos)]
        if selected_part_names and '부품명' in filtered_df.columns: filtered_df = filtered_df[filtered_df['부품명'].astype(str).isin(selected_part_names)]
        if selected_cars and '차종' in filtered_df.columns: filtered_df = filtered_df[filtered_df['차종'].astype(str).isin(selected_cars)]
        if selected_phen_names and '현상명' in filtered_df.columns:
            phen_mask = pd.Series(False, index=filtered_df.index)
            for p in selected_phen_names:
                phen_mask |= filtered_df['현상명'].astype(str).str.contains(p, case=False, na=False)
            filtered_df = filtered_df[phen_mask]
        if selected_phen_details and '현상상세' in filtered_df.columns: filtered_df = filtered_df[filtered_df['현상상세'].astype(str).isin(selected_phen_details)]
        if selected_prod_months and '생산월' in filtered_df.columns: filtered_df = filtered_df[filtered_df['생산월'].astype(str).isin(selected_prod_months)]
        if selected_sales_months and '판매월' in filtered_df.columns: filtered_df = filtered_df[filtered_df['판매월'].astype(str).isin(selected_sales_months)]
        if selected_repair_months and '수리월' in filtered_df.columns: filtered_df = filtered_df[filtered_df['수리월'].astype(str).isin(selected_repair_months)]
        if selected_vins and 'VIN' in filtered_df.columns: filtered_df = filtered_df[filtered_df['VIN'].astype(str).isin(selected_vins)]
        if selected_countries and '판매국가' in filtered_df.columns: filtered_df = filtered_df[filtered_df['판매국가'].astype(str).isin(selected_countries)]
        if selected_plants and '공장' in filtered_df.columns: filtered_df = filtered_df[filtered_df['공장'].astype(str).isin(selected_plants)]

        if selected_usages and '사용개월' in filtered_df.columns:
            usage_mask = pd.Series(False, index=filtered_df.index)
            for u in selected_usages:
                if u == 3: usage_mask |= (filtered_df['사용개월'] >= 0) & (filtered_df['사용개월'] <= 3)
                elif u == 6: usage_mask |= (filtered_df['사용개월'] >= 4) & (filtered_df['사용개월'] <= 6)
                elif u == 9: usage_mask |= (filtered_df['사용개월'] >= 7) & (filtered_df['사용개월'] <= 9)
                elif u == 12: usage_mask |= (filtered_df['사용개월'] >= 10) & (filtered_df['사용개월'] <= 12)
                else:
                    prev_u = u - 12 if u > 12 else 12
                    usage_mask |= (filtered_df['사용개월'] > prev_u) & (filtered_df['사용개월'] <= u)
            filtered_df = filtered_df[usage_mask]

        if selected_miles and '주행거리Km' in filtered_df.columns:
            mile_mask = pd.Series(False, index=filtered_df.index)
            for m in selected_miles:
                if m == 5000: mile_mask |= (filtered_df['주행거리Km'] >= 0) & (filtered_df['주행거리Km'] <= 5000)
                elif m == 10000: mile_mask |= (filtered_df['주행거리Km'] > 5000) & (filtered_df['주행거리Km'] <= 10000)
                elif m == 30000: mile_mask |= (filtered_df['주행거리Km'] > 10000) & (filtered_df['주행거리Km'] <= 30000)
                elif m == 50000: mile_mask |= (filtered_df['주행거리Km'] > 30000) & (filtered_df['주행거리Km'] <= 50000)
                elif m == 70000: mile_mask |= (filtered_df['주행거리Km'] > 50000) & (filtered_df['주행거리Km'] <= 70000)
                elif m == 100000: mile_mask |= (filtered_df['주행거리Km'] > 70000) & (filtered_df['주행거리Km'] <= 100000)
                elif m == 999999: mile_mask |= (filtered_df['주행거리Km'] > 100000)
            filtered_df = filtered_df[mile_mask]

        st.markdown("---")
        st.markdown("### 1. 차종/기간별 클레임 추이 분석")
        chart_df = pd.DataFrame()
        if '생산월' in filtered_df.columns:
            prod_trend = filtered_df.groupby('생산월').size().rename('생산건수')
            chart_df = pd.concat([chart_df, prod_trend], axis=1)
        if '수리월' in filtered_df.columns:
            repair_trend = filtered_df.groupby('수리월').size().rename('수리건수')
            chart_df = pd.concat([chart_df, repair_trend], axis=1)
        chart_df = chart_df.fillna(0).sort_index()

        if not chart_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            if '생산건수' in chart_df.columns:
                fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['생산건수'], name="생산월 클레임", marker=dict(color="#3b82f6", opacity=0.7)), secondary_y=False)
            if '수리건수' in chart_df.columns:
                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['수리건수'], name="수리월 클레임", line=dict(color="#ef4444", width=3), mode='lines+markers'), secondary_y=True)
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", height=450, margin=dict(l=40, r=40, t=30, b=40))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown(f"상세 RAW DATA 테이블 (총 {len(filtered_df)}건)")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("클레임 파일을 업로드하거나 구글 시트를 연동해주세요.")

# --- 3. 개선 활동 관리 메뉴 ---
elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 관리")
    col_i_up1, col_i_up2 = st.columns([2, 1])
    with col_i_up1:
        improve_uploaded_file = st.file_uploader("개선 활동 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"], key="improve_file_up")
    with col_i_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_improve_gsheet_btn = st.button("개선 활동 구글 시트 자동 불러오기", use_container_width=True)

    if improve_uploaded_file is not None:
        raw_imp_df = pd.read_csv(improve_uploaded_file) if improve_uploaded_file.name.endswith('.csv') else pd.read_excel(improve_uploaded_file, sheet_name=0)
        if 'id' not in raw_imp_df.columns:
            raw_imp_df.insert(0, 'id', range(1, len(raw_imp_df) + 1))
        st.session_state['improve_df'] = raw_imp_df

    if load_improve_gsheet_btn:
        try:
            imp_sheet_url = st.session_state['improve_gsheet_url']
            if imp_sheet_url:
                export_url = imp_sheet_url.replace("/pubhtml", "/pub?output=csv") if "pubhtml" in imp_sheet_url else imp_sheet_url
                raw_imp_df = pd.read_csv(export_url)
                if 'id' not in raw_imp_df.columns:
                    raw_imp_df.insert(0, 'id', range(1, len(raw_imp_df) + 1))
                st.session_state['improve_df'] = raw_imp_df
                st.success("구글 시트 로드 성공!")
                st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

    imp_df = st.session_state['improve_df']
    tab1, tab2 = st.tabs(["🔍 개선 내역 조회 및 검색", "➕/✏️ 신규 등록 및 수정"])

    with tab1:
        if not imp_df.empty:
            def get_imp_filter(label, col_name):
                if col_name in imp_df.columns:
                    options = sorted([str(x) for x in imp_df[col_name].dropna().unique() if str(x) != 'nan' and str(x) != '-'])
                    return st.multiselect(f"{label}", options, key=f"imp_filter_{col_name}")
                return []

            c1, c2, c3 = st.columns(3)
            with c1: selected_targets = get_imp_filter("대상", "대상")
            with c2: selected_product_names = get_imp_filter("품명", "품명")
            with c3: selected_car_types = get_imp_filter("차종", "차종")

            filtered_imp = imp_df.copy()
            if selected_targets and '대상' in filtered_imp.columns: filtered_imp = filtered_imp[filtered_imp['대상'].astype(str).isin(selected_targets)]
            if selected_product_names and '품명' in filtered_imp.columns: filtered_imp = filtered_imp[filtered_imp['품명'].astype(str).isin(selected_product_names)]
            if selected_car_types and '차종' in filtered_imp.columns: filtered_imp = filtered_imp[filtered_imp['차종'].astype(str).isin(selected_car_types)]

            display_imp = filtered_imp.drop(columns=['id'], errors='ignore').copy()
            st.dataframe(display_imp, use_container_width=True, height=500)
        else:
            st.info("개선 활동 데이터가 없습니다.")

    with tab2:
        with st.form("add_improve_form"):
            new_target = st.text_input("대상")
            new_product = st.text_input("품명")
            new_car = st.text_input("차종")
            new_phenomenon = st.text_input("현상")
            new_measure = st.text_area("대책 내용")
            new_part = st.text_input("해당 품목")
            new_customer = st.text_input("고객사명")
            new_date = st.date_input("적용일", value=date.today())
            new_remark = st.text_input("비고")
            submitted_imp = st.form_submit_button("개선 내용 등록", use_container_width=True)
            if submitted_imp and new_part.strip():
                new_id = int(st.session_state['improve_df']['id'].max() + 1) if not st.session_state['improve_df'].empty else 1
                new_row = {'id': new_id, '대상': new_target, '품명': new_product, '차종': new_car, '현상': new_phenomenon, '대책 내용': new_measure, '해당 품목': new_part, '고객사명': new_customer, '적용일': str(new_date), '비 고': new_remark}
                st.session_state['improve_df'] = pd.concat([st.session_state['improve_df'], pd.DataFrame([new_row])], ignore_index=True)
                st.success("등록 완료!")
                st.rerun()

# --- 4. 고객사 클레임 비용 분석 메뉴 (동적 시트 전체 순회 & 에러 방어) ---
elif menu == "고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 2차 가공 및 취합 분석")
    st.markdown("업로드하신 엑셀 파일의 **모든 시트(새로 추가된 고객사/법인 포함)** 또는 구글 시트를 동적으로 자동 취합합니다.")

    col_c_up1, col_c_up2 = st.columns([2, 1])
    with col_c_up1:
        cost_uploaded_file = st.file_uploader("고객사 클레임 비용 원본 엑셀(.xlsx) 파일 업로드", type=["xlsx"], key="cost_file_up")
    with col_c_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_cost_gsheet_btn = st.button("비용 구글 시트 데이터 불러오기", use_container_width=True)

    def parse_cost_dataframe(df_sheet, default_cust_name="기타고객사"):
        cols = [str(c).strip() for c in df_sheet.columns]
        df_sheet.columns = cols
        
        cust_col = next((c for c in cols if '고객사' in c or '법인' in c or '업체' in c), None)
        if cust_col:
            valid_cust = df_sheet[cust_col].dropna()
            cust_name = str(valid_cust.iloc[0]) if not valid_cust.empty else default_cust_name
        else:
            cust_name = default_cust_name

        source_col = next((c for c in cols if '발생' in c), None)
        df_sheet['발생처'] = df_sheet[source_col].astype(str) if source_col else 'D'

        num_col = next((c for c in cols if '통보서' in c or '클레임번호' in c or 'R/O' in c or 'No' in c), None)
        df_sheet['통보서번호'] = df_sheet[num_col].astype(str) if num_col else ''

        amt_col = next((c for c in cols if '금액' in c or '합계' in c or '청구' in c or '변제' in c), None)
        df_sheet['금액'] = pd.to_numeric(df_sheet[amt_col], errors='coerce').fillna(0) if amt_col else 0

        part_col = next((c for c in cols if '품명' in c or '부품' in c or '품목' in c), None)
        df_sheet['품목'] = df_sheet[part_col].astype(str) if part_col else '기타'

        df_sheet['고객사'] = cust_name
        return df_sheet[['고객사', '발생처', '통보서번호', '금액', '품목']].copy()

    if load_cost_gsheet_btn:
        try:
            cost_sheet_url = st.session_state['cost_gsheet_url']
            if cost_sheet_url:
                export_url = cost_sheet_url.replace("/pubhtml", "/pub?output=csv") if "pubhtml" in cost_sheet_url else cost_sheet_url
                cost_raw_df = pd.read_csv(export_url)
                if not cost_raw_df.empty:
                    parsed_cost_df = parse_cost_dataframe(cost_raw_df, default_cust_name="구글시트고객사")
                    st.session_state['cost_df'] = parsed_cost_df
                    st.session_state['cost_uploaded_file_name'] = "Google Sheet"
                    st.success("구글 시트 데이터 로드 성공!")
                    st.rerun()
        except Exception as e:
            st.error(f"구글 시트 연동 오류: {e}")

    if cost_uploaded_file is not None:
        if st.session_state['cost_uploaded_file_name'] != cost_uploaded_file.name:
            try:
                xls = pd.ExcelFile(cost_uploaded_file)
                all_sheets = xls.sheet_names
                combined_list = []
                for sheet_name in all_sheets:
                    df_sheet = pd.read_excel(cost_uploaded_file, sheet_name=sheet_name)
                    if not df_sheet.empty:
                        parsed_sub = parse_cost_dataframe(df_sheet, default_cust_name=sheet_name)
                        combined_list.append(parsed_sub)

                if combined_list:
                    master_cost_df = pd.concat(combined_list, ignore_index=True)
                    master_cost_df['금액'] = pd.to_numeric(master_cost_df['금액'], errors='coerce').fillna(0)
                    st.session_state['cost_df'] = master_cost_df
                    st.session_state['cost_uploaded_file_name'] = cost_uploaded_file.name
                    st.success(f"총 {len(all_sheets)}개 시트 동적 취합 완료!")
            except Exception as e:
                st.error(f"비용 파일 처리 오류: {e}")

    cost_df = st.session_state['cost_df']
    if not cost_df.empty:
        st.markdown("---")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_customers = sorted(cost_df['고객사'].dropna().unique().tolist())
            selected_cust_filter = st.multiselect("고객사 선택", all_customers, default=all_customers)
        with f_col2:
            all_sources = sorted(cost_df['발생처'].dropna().unique().tolist())
            selected_source_filter = st.multiselect("발생처 선택", all_sources, default=all_sources)
        with f_col3:
            all_parts = sorted(cost_df['품목'].dropna().unique().tolist())
            selected_part_filter = st.multiselect("품목 선택", all_parts, default=all_parts)

        filtered_cost = cost_df[
            cost_df['고객사'].isin(selected_cust_filter) &
            cost_df['발생처'].isin(selected_source_filter) &
            cost_df['품목'].isin(selected_part_filter)
        ]

        st.markdown("---")
        st.markdown("### 📋 1. 필드 클레임 취합")
        grouped_summary = filtered_cost.groupby(['고객사', '발생처', '통보서번호']).agg(
            금액=('금액', 'sum'),
            건수=('금액', 'count')
        ).reset_index()
        st.dataframe(grouped_summary, use_container_width=True, height=400)

        total_amount = filtered_cost['금액'].sum()
        total_count = len(filtered_cost)
        st.markdown(f"**합 계 금액:** ₩ {total_amount:,.0f} | **총 건수:** {total_count:,}건")

        st.markdown("---")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("#### 고객사별 현황")
            cust_summary = filtered_cost.groupby('고객사')['금액'].sum().reset_index()
            st.dataframe(cust_summary, use_container_width=True, height=320)
        with col_t2:
            st.markdown("#### 품목별 현황")
            part_summary = filtered_cost.groupby('품목')['금액'].sum().reset_index()
            st.dataframe(part_summary, use_container_width=True, height=320)
    else:
        st.info("고객사 클레임 비용 원본 엑셀 파일을 업로드하거나 구글 시트를 연동해주세요.")

# --- 5. 구글 시트 연동 설정 메뉴 ---
elif menu == "구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동 설정")
    gsheet_input = st.text_input("필드 클레임 현황 구글 시트 URL", st.session_state['gsheet_url'])
    improve_gsheet_input = st.text_input("개선 활동 관리 구글 시트 URL", st.session_state['improve_gsheet_url'])
    cost_gsheet_input = st.text_input("고객사 클레임 비용 구글 시트 URL", st.session_state['cost_gsheet_url'])
    
    if st.button("연동 정보 저장"):
        st.session_state['gsheet_url'] = gsheet_input
        st.session_state['improve_gsheet_url'] = improve_gsheet_input
        st.session_state['cost_gsheet_url'] = cost_gsheet_input
        st.success("연동 정보가 저장되었습니다!")
