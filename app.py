import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import os
import json
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
    div[data-testid="stDataFrame"] td {
        white-space: pre-wrap !important;
        vertical-align: middle !important;
    }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.title("Quality Assurance/Management")

# 로컬 파일 자동 저장 및 불러오기 경로 (업무 데이터 & 설정 링크)
TASKS_FILE = "tasks_data.csv"
SETTINGS_FILE = "settings_data.json"
COST_DATA_DIR = "saved_cost_files"

if not os.path.exists(COST_DATA_DIR):
    os.makedirs(COST_DATA_DIR)

def save_tasks_to_local(tasks):
    try:
        df_save = pd.DataFrame(tasks)
        for col in ['date', 'deadline']:
            if col in df_save.columns:
                df_save[col] = pd.to_datetime(df_save[col]).dt.strftime('%Y-%m-%d')
        df_save.to_csv(TASKS_FILE, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"로컬 저장 중 오류 발생: {e}")

def load_tasks_from_local():
    if os.path.exists(TASKS_FILE):
        try:
            df = pd.read_csv(TASKS_FILE)
            if not df.empty:
                tasks = []
                for _, row in df.iterrows():
                    try:
                        t_date = datetime.strptime(str(row.get('date', date.today())).split()[0], '%Y-%m-%d').date()
                    except:
                        t_date = date.today()
                    try:
                        t_deadline = datetime.strptime(str(row.get('deadline', row.get('deadlin', date.today()))).split()[0], '%Y-%m-%d').date()
                    except:
                        t_deadline = date.today()
                        
                    tasks.append({
                        "id": int(row.get('id', len(tasks) + 1)),
                        "title": str(row.get('title', '')),
                        "date": t_date,
                        "deadline": t_deadline,
                        "memo": str(row.get('memo', '')) if pd.notna(row.get('memo')) else "",
                        "requester": str(row.get('requester', '')) if pd.notna(row.get('requester')) else "",
                        "category": str(row.get('category', '고객제출')),
                        "completed": str(row.get('completed', 'False')).lower() == 'true',
                        "completed_date": str(row.get('completed_date')) if pd.notna(row.get('completed_date')) and str(row.get('completed_date')) != 'nan' else None,
                        "updated_date": str(row.get('updated_date')) if pd.notna(row.get('updated_date')) and str(row.get('updated_date')) != 'nan' else None
                    })
                return tasks
        except Exception:
            pass
    return None

def save_settings_to_local(settings_dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"설정 저장 오류: {e}")

def load_settings_from_local():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# 구글 시트에서 tasks 데이터를 불러오는 함수
def load_tasks_from_gsheet():
    try:
        sheet_url = st.session_state.get('task_gsheet_url', '')
        if not sheet_url:
            return None
        if "pubhtml" in sheet_url:
            export_url = sheet_url.replace("/pubhtml", "/pub?output=csv")
        elif "edit" in sheet_url:
            export_url = sheet_url.split('/edit')[0] + '/export?format=csv'
        else:
            export_url = sheet_url
            
        df = pd.read_csv(export_url)
        if df.empty:
            return None
            
        tasks = []
        for _, row in df.iterrows():
            try:
                t_date = datetime.strptime(str(row.get('date', date.today())).split()[0], '%Y-%m-%d').date()
            except:
                t_date = date.today()
            try:
                dl_val = row.get('deadline', row.get('deadlin', date.today()))
                t_deadline = datetime.strptime(str(dl_val).split()[0], '%Y-%m-%d').date()
            except:
                t_deadline = date.today()
                
            tasks.append({
                "id": int(row.get('id', len(tasks) + 1)),
                "title": str(row.get('title', '')),
                "date": t_date,
                "deadline": t_deadline,
                "memo": str(row.get('memo', '')) if pd.notna(row.get('memo')) else "",
                "requester": str(row.get('requester', '')) if pd.notna(row.get('requester')) else "",
                "category": str(row.get('category', '고객제출')),
                "completed": str(row.get('completed', 'False')).lower() == 'true',
                "completed_date": str(row.get('completed_date')) if pd.notna(row.get('completed_date')) and str(row.get('completed_date')) != 'nan' else None,
                "updated_date": str(row.get('updated_date')) if pd.notna(row.get('updated_date')) and str(row.get('updated_date')) != 'nan' else None
            })
        return tasks
    except Exception as e:
        return None

# 세션 스테이트 초기화 (로컬 저장된 설정 불러오기)
saved_settings = load_settings_from_local()

if 'gsheet_url' not in st.session_state:
    st.session_state['gsheet_url'] = saved_settings.get('gsheet_url', "")
if 'improve_gsheet_url' not in st.session_state:
    st.session_state['improve_gsheet_url'] = saved_settings.get('improve_gsheet_url', "")
if 'cost_gsheet_url' not in st.session_state:
    st.session_state['cost_gsheet_url'] = saved_settings.get('cost_gsheet_url', "")
if 'task_gsheet_url' not in st.session_state:
    st.session_state['task_gsheet_url'] = saved_settings.get('task_gsheet_url', "")

if 'tasks' not in st.session_state:
    loaded_local = load_tasks_from_local()
    if loaded_local:
        st.session_state['tasks'] = loaded_local
    else:
        loaded_tasks = load_tasks_from_gsheet()
        if loaded_tasks:
            st.session_state['tasks'] = loaded_tasks
        else:
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
                }
            ]
        save_tasks_to_local(st.session_state['tasks'])

if 'cal_year' not in st.session_state: st.session_state['cal_year'] = datetime.today().year
if 'cal_month' not in st.session_state: st.session_state['cal_month'] = datetime.today().month
if 'selected_date' not in st.session_state: st.session_state['selected_date'] = date.today()
if 'editing_task_id' not in st.session_state: st.session_state['editing_task_id'] = None
if 'delete_confirm_id' not in st.session_state: st.session_state['delete_confirm_id'] = None
if 'save_confirm_type' not in st.session_state: st.session_state['save_confirm_type'] = None
if 'pending_form_data' not in st.session_state: st.session_state['pending_form_data'] = None

if 'claim_df' not in st.session_state: st.session_state['claim_df'] = pd.DataFrame()
if 'uploaded_file_name' not in st.session_state: st.session_state['uploaded_file_name'] = None
if 'improve_uploaded_file_name' not in st.session_state: st.session_state['improve_uploaded_file_name'] = None

if 'improve_df' not in st.session_state:
    raw_data = [
        {'대상': '승용', '품명': '워터펌프', '차종': '람다', '현상': '누수/소음', '대책 내용': 'M/SEAL M/R 재질 환원(ES5 ▶ ES4)', '해당 품목': '25100-3CAC0', '고객사명': '-', '적용일': '2016-06-27', '비 고': ''},
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
    total_weekly = len(weekly_tasks)
    completed_weekly = len([t for t in weekly_tasks if t['completed']])
    pending_weekly = total_weekly - completed_weekly

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("이번 주 총 업무 건수", f"{total_weekly} 건")
    col_s2.metric("완료된 건수", f"{completed_weekly} 건")
    col_s3.metric("미결(진행중) 건수", f"{pending_weekly} 건")

# --- 1. 업무 등록/관리 메뉴 ---
elif menu == "업무 등록/관리":
    st.subheader("월별 업무 관리 및 지속 기록 캘린더")
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
        st.markdown(f"### 선택일 업무 현황 ({st.session_state['selected_date']})")
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        if not target_tasks:
            st.info("선택된 날짜에 등록된 업무가 없습니다.")
        else:
            for task in target_tasks:
                box_style = "border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 14px; background-color: #0e1117;"
                cols_t = st.columns([0.88, 0.12])
                cat = task['category']
                c_bg, c_fg = ("#fee2e2", "#991b1b") if cat == '고객제출' else ("#dbeafe", "#1e40af") if cat == '자료작성' else ("#fef08a", "#854d0e")
                card_html = f"""
                    <div style='{box_style}'>
                        <span style='font-size: 18px; font-weight: bold; color: white;'>{task['title']}</span> 
                        <span style='font-size:12px; background:{c_bg}; color:{c_fg}; padding:2px 6px; border-radius:4px; font-weight:bold;'>{cat}</span><br>
                        <div style='font-size: 14px; color: #e2e8f0; margin-top: 6px; line-height: 1.5; white-space: pre-wrap;'><b>요청자:</b> {task['requester']}
<b>마감기한:</b> {task['deadline']}
<b>메모:</b> {task['memo']}</div>
                    </div>
                """
                cols_t[0].markdown(card_html, unsafe_allow_html=True)
                with cols_t[1]:
                    if st.button("완료", key=f"comp_btn_{task['id']}", use_container_width=True):
                        task['completed'] = not task['completed']
                        save_tasks_to_local(st.session_state['tasks'])
                        st.rerun()
                    if st.button("삭제", key=f"del_btn_{task['id']}", use_container_width=True):
                        st.session_state['tasks'] = [t for t in st.session_state['tasks'] if t['id'] != task['id']]
                        save_tasks_to_local(st.session_state['tasks'])
                        st.rerun()

    with col_right:
        st.markdown("### 신규 일정 등록")
        with st.form("task_manage_form"):
            f_title = st.text_input("업무 제목")
            f_date = st.date_input("작성 일자", value=st.session_state['selected_date'])
            f_deadline = st.date_input("마감 기한", value=st.session_state['selected_date'])
            f_category = st.selectbox("카테고리 선택", ["고객제출", "업체접수", "자료작성", "업무 확인", "업무 협의", "회의"])
            f_requester = st.text_input("요청자")
            f_memo = st.text_area("메모 및 상세 내용")
            submitted = st.form_submit_button("신규 등록 및 자동저장", use_container_width=True)
            if submitted and f_title.strip():
                new_id = max([t['id'] for t in st.session_state['tasks']], default=0) + 1
                st.session_state['tasks'].append({
                    "id": new_id, "title": f_title, "date": f_date, "deadline": f_deadline,
                    "memo": f_memo, "requester": f_requester, "category": f_category,
                    "completed": False, "completed_date": None, "updated_date": None
                })
                save_tasks_to_local(st.session_state['tasks'])
                st.success("등록 완료 및 자동 저장되었습니다!")
                st.rerun()

# --- 2. 필드 클레임 현황 메뉴 ---
elif menu == "필드 클레임 현황":
    st.subheader("필드 클레임 RAW DATA 분석")

# --- 3. 개선 활동 관리 메뉴 ---
elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 관리")

# --- 4. 고객사 클레임 비용 분석 (HKMC, WIA, 글로비스, 모비스 개별 취합 및 표준 포맷 적용) ---
elif menu == "고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 개별 업로드 및 표준 취합 대시보드")
    st.markdown("HKMC, WIA, 글로비스, 모비스 4개 고객사의 엑셀 파일을 각각 개별 업로드하여 **개별 클레임 취합 결과**를 확인하세요.")
    st.markdown("---")

    # 4개 개별 업로더 배치
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        file_hkmc = st.file_uploader("1. 완성차(HKMC) 클레임 비용 엑셀 업로드", type=["xlsx", "xls"], key="ind_hkmc")
        file_globis = st.file_uploader("2. 글로비스 클레임 비용 엑셀 업로드", type=["xlsx", "xls"], key="ind_globis")
    with col_up2:
        file_wia = st.file_uploader("3. 위아(WIA) 클레임 비용 엑셀 업로드", type=["xlsx", "xls"], key="ind_wia")
        file_mobis = st.file_uploader("4. 모비스 클레임 비용 엑셀 업로드", type=["xlsx", "xls"], key="ind_mobis")

    # 공통 파싱 및 표준화 함수 (날짜 YY-MM-DD, 주행거리 00,000 포맷 적용)
    def parse_cost_file(uploaded_file, corp_name):
        if uploaded_file is None:
            return pd.DataFrame()
        try:
            xls = pd.ExcelFile(uploaded_file)
            combined = []
            target_columns = [
                '법인', '발생구분', '통보서', 'H/K', '업체', 'SEQ', 'RO년월', 'R/O번호', 'VIN', 'C/TYPE', '차종', 
                '원인부품', '원인품명', '주작업코드', '원인', '현상', '생산일자', '수리일자', '판매일자', '사용개월', 
                '주행거리', '납입율', '분담율', '적용율', '부품비', '공임비', '외주비', '합계'
            ]

            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
                if df_raw.empty or len(df_raw) < 1:
                    continue
                
                header_idx = 0
                for idx, row in df_raw.iloc[:10].iterrows():
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    if any(k in row_str for k in ["원인부품", "R/O번호", "통보서", "VIN", "차종", "원인품번", "클레임번호", "No.", "업체", "법인"]):
                        header_idx = idx
                        break
                
                df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)
                df_sheet = df_sheet.dropna(how='all')
                if df_sheet.empty:
                    continue
                
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                rows = []
                for _, row in df_sheet.iterrows():
                    # 날짜 포맷 변환 (YY-MM-DD)
                    def fmt_date(val):
                        if pd.isna(val) or str(val).strip() == '':
                            return ''
                        try:
                            dt = pd.to_datetime(val)
                            return dt.strftime('%y-%m-%d')
                        except:
                            s = str(val).split()[0].replace('.', '-')
                            if len(s) == 10 and s[4] == '-' and s[7] == '-':
                                return s[2:] # YYYY-MM-DD -> YY-MM-DD
                            return s

                    prod_d = fmt_date(row.get('생산일자', row.get('생산일', '')))
                    rep_d = fmt_date(row.get('수리일자', row.get('수리일', '')))
                    sale_d = fmt_date(row.get('판매일자', row.get('판매일', '')))

                    # 주행거리 포맷 (00,000)
                    raw_mile = pd.to_numeric(row.get('주행거리', row.get('주행거리(Km)', 0)), errors='coerce') or 0
                    mile_str = f"{int(raw_mile):,}"

                    # 사용개월 (정수 또는 실수 깔끔하게)
                    use_m = pd.to_numeric(row.get('사용개월', row.get('사용기간', 0)), errors='coerce') or 0

                    # 금액 파싱 오류 방지 (WIA, 모비스 등 금액 컬럼 안전 연동)
                    part_val = float(pd.to_numeric(row.get('부품비', row.get('변제 부품비', row.get('부품청구금액', 0))), errors='coerce') or 0)
                    labor_val = float(pd.to_numeric(row.get('공임비', row.get('변제 공임비', row.get('공임비', 0))), errors='coerce') or 0)
                    out_val = float(pd.to_numeric(row.get('외주비', row.get('변제 외주비', row.get('외주비', 0))), errors='coerce') or 0)
                    tot_val = float(pd.to_numeric(row.get('합계', row.get('청구금액', part_val + labor_val + out_val)), errors='coerce') or (part_val + labor_val + out_val))

                    r_dict = {
                        '법인': str(row.get('법인', corp_name)),
                        '발생구분': str(row.get('발생구분', row.get('결함구분', 'D'))),
                        '통보서': str(row.get('통보서', row.get('클레임번호', ''))),
                        'H/K': str(row.get('H/K', 'H')),
                        '업체': str(row.get('업체', 'RI14')),
                        'SEQ': str(row.get('SEQ', '1')),
                        'RO년월': str(row.get('RO년월', '')),
                        'R/O번호': str(row.get('R/O번호', '')),
                        'VIN': str(row.get('VIN', '')),
                        'C/TYPE': str(row.get('C/TYPE', 'W')),
                        '차종': str(row.get('차종', '')),
                        '원인부품': str(row.get('원인부품', row.get('원인품번', ''))),
                        '원인품명': str(row.get('원인품명', row.get('원인부품명', row.get('품명', '')))),
                        '주작업코드': str(row.get('주작업코드', '')),
                        '원인': str(row.get('원인', '')),
                        '현상': str(row.get('현상', '')),
                        '생산일자': prod_d,
                        '수리일자': rep_d,
                        '판매일자': sale_d,
                        '사용개월': f"{use_m:.1f}" if use_m % 1 != 0 else str(int(use_m)),
                        '주행거리': mile_str,
                        '납입율': float(pd.to_numeric(row.get('납입율', 100.0), errors='coerce') or 100.0),
                        '분담율': float(pd.to_numeric(row.get('분담율', 19.01), errors='coerce') or 19.01),
                        '적용율': float(pd.to_numeric(row.get('적용율', 19.01), errors='coerce') or 19.01),
                        '부품비': part_val,
                        '공임비': labor_val,
                        '외주비': out_val,
                        '합계': tot_val
                    }
                    rows.append(r_dict)
                
                if rows:
                    df_sub = pd.DataFrame(rows)
                    for tc in target_columns:
                        if tc not in df_sub.columns:
                            df_sub[tc] = ''
                    combined.append(df_sub[target_columns])

            if combined:
                res_df = pd.concat(combined, ignore_index=True)
                return res_df
        except Exception as e:
            st.error(f"[{corp_name}] 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

    # 각 파일별 개별 파싱 및 세션 저장
    df_hkmc = parse_cost_file(file_hkmc, "HKMC")
    df_wia = parse_cost_file(file_wia, "WIA")
    df_globis = parse_cost_file(file_globis, "글로비스")
    df_mobis = parse_cost_file(file_mobis, "모비스")

    st.markdown("---")

    # 4개 탭으로 개별 취합 결과 출력
    tab_h, tab_w, tab_g, tab_m = st.tabs(["완성차(HKMC)", "위아(WIA)", "글로비스", "모비스"])

    def render_cost_tab(df_target, title_prefix):
        if df_target.empty:
            st.info(f"{title_prefix} 클레임 비용 엑셀 파일을 업로드해주세요.")
            return

        st.markdown(f"#### 📋 {title_prefix} 개별 클레임 취합 결과 (총 {len(df_target):,}건)")
        
        # 금액 포맷팅 뷰
        display_df = df_target.copy()
        for col in ['부품비', '공임비', '외주비', '합계']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"₩ {x:,.0f}" if isinstance(x, (int, float)) else x)

        st.dataframe(display_df, use_container_width=True, height=400)

        # 다운로드 버튼
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_target.to_excel(writer, index=False, sheet_name=f'{title_prefix}_취합')
        excel_data = output.getvalue()

        st.download_button(
            label=f"📥 {title_prefix} 취합 결과 엑셀 다운로드",
            data=excel_data,
            file_name=f"{title_prefix}_클레임_비용_취합.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{title_prefix}"
        )

        t_part = df_target['부품비'].sum() if '부품비' in df_target.columns else 0
        t_labor = df_target['공임비'].sum() if '공임비' in df_target.columns else 0
        t_out = df_target['외주비'].sum() if '외주비' in df_target.columns else 0
        t_sum = df_target['합계'].sum() if '합계' in df_target.columns else 0

        st.markdown(f"**[ {title_prefix} 합계 ] 부품비:** ₩ {t_part:,.0f} | **공임비:** ₩ {t_labor:,.0f} | **외주비:** ₩ {t_out:,.0f} | **총 합계 금액:** ₩ {t_sum:,.0f}")

    with tab_h:
        render_cost_tab(df_hkmc, "HKMC")
    with tab_w:
        render_cost_tab(df_wia, "WIA")
    with tab_g:
        render_cost_tab(df_globis, "글로비스")
    with tab_m:
        render_cost_tab(df_mobis, "모비스")

# --- 5. 구글 시트 연동 설정 메뉴 ---
elif menu == "구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동 설정")
    gsheet_input = st.text_input("필드 클레임 현황 구글 시트 URL", st.session_state['gsheet_url'])
    improve_gsheet_input = st.text_input("개선 활동 관리 구글 시트 URL", st.session_state['improve_gsheet_url'])
    cost_gsheet_input = st.text_input("고객사 클레임 비용 구글 시트 URL", st.session_state['cost_gsheet_url'])
    task_gsheet_input = st.text_input("업무 관리 구글 시트 URL", st.session_state['task_gsheet_url'])
    
    if st.button("연동 정보 저장"):
        st.session_state['gsheet_url'] = gsheet_input
        st.session_state['improve_gsheet_url'] = improve_gsheet_input
        st.session_state['cost_gsheet_url'] = cost_gsheet_input
        st.session_state['task_gsheet_url'] = task_gsheet_input
        
        save_settings_to_local({
            'gsheet_url': gsheet_input,
            'improve_gsheet_url': improve_gsheet_input,
            'cost_gsheet_url': cost_gsheet_input,
            'task_gsheet_url': task_gsheet_input
        })
        st.success("구글 시트 연동 정보가 저장되었습니다.")
