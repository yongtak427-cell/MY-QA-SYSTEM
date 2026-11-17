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
    st.session_state['gsheet_url'] = saved_settings.get('gsheet_url', "https://docs.google.com/spreadsheets/d/e/2PACX-1vQoePTO6LK-r65996JMmTMfdC-D8zuj83sa_YBQ4VxyFsq8ZRTaXBbiI5ZmPVngpkrPK-soa9P8IetD/pubhtml")
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
        {'대상': '승용', '품명': '워터펌프', '차종': '람다', '현상': '누수/소음', '대책 내용': 'M/SEAL M/R 재질 환원(ES5 ▶ ES4)', '해당 품목': '25100-3L100', '고객사명': '-', '적용일': '2016-06-27', '비 고': ''},
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
    st.markdown("이번 주(월요일 ~ 일요일 기준) 등록된 업무 현황 건수, 완료 건수, 미결 건수를 확인합니다.")

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

    st.markdown("---")
    st.markdown(f"이번 주 ({start_of_week} ~ {end_of_week}) 상세 업무 리스트")
    if not weekly_tasks:
        st.info("이번 주에 등록된 업무가 없습니다.")
    else:
        weekly_df = pd.DataFrame([{
            "ID": t['id'],
            "날짜": t['date'],
            "제목": t['title'],
            "카테고리": t['category'],
            "요청자": t['requester'],
            "마감기한": t['deadline'],
            "상태": "완료" if t['completed'] else "미결"
        } for t in weekly_tasks])
        st.dataframe(weekly_df, use_container_width=True)

# --- 1. 업무 등록/관리 메뉴 ---
elif menu == "업무 등록/관리":
    st.subheader("월별 업무 관리 현황")
    
    sync_col1, sync_col2 = st.columns(2)
    with sync_col1:
        if st.button("🔄 구글 시트에서 업무 새로고침/불러오기", use_container_width=True):
            loaded = load_tasks_from_gsheet()
            if loaded:
                st.session_state['tasks'] = loaded
                save_tasks_to_local(st.session_state['tasks'])
                st.success("구글 시트에서 업무 데이터를 불러와 자동 저장되었습니다!")
                st.rerun()
            else:
                st.warning("구글 시트 URL이 올바르지 않거나 데이터가 없습니다.")
    with sync_col2:
        if st.session_state['tasks']:
            task_export_df = pd.DataFrame(st.session_state['tasks'])
            for col in ['date', 'deadline']:
                if col in task_export_df.columns:
                    task_export_df[col] = task_export_df[col].astype(str)
            output_t = io.BytesIO()
            with pd.ExcelWriter(output_t, engine='openpyxl') as writer:
                task_export_df.to_excel(writer, index=False, sheet_name='tasks')
            t_excel_data = output_t.getvalue()
            st.download_button(
                label="📥 현재 업무 목록 엑셀 다운로드 (구글 시트 백업용)",
                data=t_excel_data,
                file_name="tikitak_tasks_backup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with st.expander("📋 [추천] 구글 시트 1초 즉시 동기화 (파일 업로드 없이 복사·붙여넣기)"):
        st.markdown("아래 박스의 **[텍스트 전체 복사]** 버튼을 누른 뒤, 구글 시트 **A1 셀**에 붙여넣기(`Ctrl + V`) 하시면 업로드 과정 없이 즉시 반영됩니다.")
        if st.session_state['tasks']:
            tsv_df = pd.DataFrame(st.session_state['tasks'])
            for col in ['date', 'deadline']:
                if col in tsv_df.columns:
                    tsv_df[col] = tsv_df[col].astype(str)
            tsv_text = tsv_df.to_csv(sep='\t', index=False)
            st.text_area("구글 시트 붙여넣기용 데이터", tsv_text, height=120)

    st.markdown("---")
    
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
                
                if len(day_tasks) > 0:
                    btn_text = f"{day}일 ({len(day_tasks)}건)"
                else:
                    btn_text = f"{day}"

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
                        save_tasks_to_local(st.session_state['tasks'])
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
                        save_tasks_to_local(st.session_state['tasks'])
                        if st.session_state['editing_task_id'] == task['id']:
                            st.session_state['editing_task_id'] = None
                        st.session_state['delete_confirm_id'] = None
                        st.success("삭제되고 자동 저장되었습니다.")
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
                    new_id = max([t['id'] for t in st.session_state['tasks']], default=0) + 1
                    st.session_state['tasks'].append({
                        "id": new_id,
                        "title": data['title'],
                        "date": data['date'],
                        "deadline": data['deadline'],
                        "memo": data['memo'],
                        "requester": data['requester'],
                        "category": data['category'],
                        "completed": False,
                        "completed_date": None,
                        "updated_date": None
                    })
                    st.success("신규 등록 및 자동 저장되었습니다!")
                else:
                    target_t = next((t for t in st.session_state['tasks'] if t['id'] == st.session_state['editing_task_id']), None)
                    if target_t:
                        target_t.update({
                            "title": data['title'],
                            "date": data['date'],
                            "deadline": data['deadline'],
                            "category": data['category'],
                            "requester": data['requester'],
                            "memo": data['memo'],
                            "updated_date": datetime.today().strftime('%y-%m-%d')
                        })
                        st.session_state['editing_task_id'] = None
                        st.success("수정 및 자동 저장되었습니다!")
                
                save_tasks_to_local(st.session_state['tasks'])
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
                
                default_date = editing_task['date'] if editing_task else st.session_state['selected_date']
                default_deadline = editing_task['deadline'] if editing_task else st.session_state['selected_date']
                
                f_date = st.date_input("작성 일자", value=default_date)
                f_deadline = st.date_input("마감 기한", value=default_deadline)
                
                categories = ["고객제출", "업체접수", "자료작성", "업무 확인", "업무 협의", "회의"]
                f_category = st.selectbox("카테고리 선택", categories, index=categories.index(editing_task['category']) if editing_task and editing_task['category'] in categories else 0)
                
                f_requester = st.text_input("요청자", value=editing_task['requester'] if editing_task else "")
                f_memo = st.text_area("메모 및 상세 내용", value=editing_task['memo'] if editing_task else "")
                
                col_f1, col_f2 = st.columns(2)
                submitted_new = col_f1.form_submit_button("신규등록", use_container_width=True)
                submitted_update = col_f2.form_submit_button("내용 수정/등록", use_container_width=True)

                if submitted_new and not editing_task:
                    if f_title.strip():
                        st.session_state['pending_form_data'] = {
                            "title": f_title, "date": f_date, "deadline": f_deadline,
                            "category": f_category, "requester": f_requester, "memo": f_memo
                        }
                        st.session_state['save_confirm_type'] = 'new'
                        st.rerun()

                if submitted_update and editing_task:
                    if f_title.strip():
                        st.session_state['pending_form_data'] = {
                            "title": f_title, "date": f_date, "deadline": f_deadline,
                            "category": f_category, "requester": f_requester, "memo": f_memo
                        }
                        st.session_state['save_confirm_type'] = 'update'
                        st.rerun()

# --- 2. 필드 클레임 현황 메뉴 ---
elif menu == "필드 클레임 현황":
    st.subheader("클레임 RAW DATA 분석 및 시각화 대시보드")
    st.markdown("구글 시트에 등록된 데이터를 불러오거나 엑셀 파일을 업로드하여 클레임 분석을 진행하세요.")

    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader("클레임 RAW DATA 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])
    with col_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_gsheet_btn = st.button("구글 시트 데이터 자동 불러오기", use_container_width=True)

    def process_raw_dataframe(df_raw):
        cols = list(df_raw.columns)
        if len(cols) > 63:
            cols[63] = '현상명'
        if len(cols) > 59:
            cols[59] = '현상상세'
            
        seen = {}
        new_cols = []
        for c in cols:
            if c in seen:
                seen[c] += 1
                new_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                new_cols.append(c)
        df_raw.columns = new_cols
        
        if len(df_raw.columns) > 63:
            df_raw['현상명'] = df_raw.iloc[:, 63].astype(str)
            
        if '사용개월' in df_raw.columns:
            df_raw['사용개월'] = pd.to_numeric(df_raw['사용개월'], errors='coerce').fillna(0)
        if '주행거리Km' in df_raw.columns:
            df_raw['주행거리Km'] = pd.to_numeric(df_raw['주행거리Km'], errors='coerce').fillna(0)
            
        return df_raw

    if uploaded_file is not None:
        if st.session_state['uploaded_file_name'] != uploaded_file.name:
            try:
                raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, sheet_name=0)
                raw_df = process_raw_dataframe(raw_df)
                st.session_state['claim_df'] = raw_df
                st.session_state['uploaded_file_name'] = uploaded_file.name
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

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
                st.success("구글 시트에서 데이터를 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("구글 시트 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"구글 시트 연동 중 오류 발생: {e}")

    df = st.session_state['claim_df']

    if not df.empty:
        st.markdown("---")
        st.markdown("클레임 조회 (직접 검색 및 다중 선택 가능)")

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
            selected_usages = st.multiselect("사용개월", usage_options, format_func=lambda x: f"{x}개월" if x<=12 else f"{x}개월", key="filter_usage")
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

        if selected_phen_details and '현상상세' in filtered_df.columns: 
            filtered_df = filtered_df[filtered_df['현상상세'].astype(str).isin(selected_phen_details)]

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

        st.markdown("### 1. 차종/기간별 클레임 추이 분석 (생산월 파란색 막대 [좌측 축] & 수리월 빨간색 꺾은선 [우측 축])")
        if not filtered_df.empty:
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
                    fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['생산건수'], name="생산월 클레임 (막대)", marker=dict(color="#3b82f6", opacity=0.7)), secondary_y=False)
                if '수리건수' in chart_df.columns:
                    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['수리건수'], name="수리월 클레임 (꺾은선)", line=dict(color="#ef4444", width=3), mode='lines+markers'), secondary_y=True)

                fig.update_layout(template="plotly_dark", paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", height=450, margin=dict(l=40, r=40, t=30, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig.update_yaxes(title_text="<b>생산건수 (좌측)</b>", secondary_y=False, rangemode="tozero", showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(title_text="<b>수리건수 (우측)</b>", secondary_y=True, rangemode="tozero", showgrid=False)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("시각화할 데이터가 없습니다.")
        else:
            st.info("표시할 트렌드 데이터가 없습니다.")

        st.markdown("---")

        st.markdown("### 2. 다각도 클레임 현황 분석 (수평 막대 그래프)")
        
        def plot_horizontal_bar(data_series, title_text, height=450, custom_order=None):
            if data_series.empty:
                st.info("데이터 없음")
                return
            
            if custom_order is not None:
                data_series = data_series.reindex(custom_order).fillna(0)
                y_vals = [str(i) for i in data_series.index]
            else:
                data_series = data_series.sort_values(ascending=True)
                y_vals = [str(i) for i in data_series.index]

            fig = go.Figure(go.Bar(
                x=data_series.values,
                y=y_vals,
                orientation='h',
                text=data_series.values,
                textposition='auto',
                marker=dict(color='#3b82f6')
            ))
            
            fig.update_layout(
                title=title_text,
                template="plotly_dark",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                height=height,
                margin=dict(l=150, r=50, t=30, b=30),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', rangemode='tozero'),
                yaxis=dict(tickfont=dict(size=11), type='category', categoryorder='array', categoryarray=y_vals)
            )
            st.plotly_chart(fig, use_container_width=True)

        hb_col1, hb_col2 = st.columns(2)

        with hb_col1:
            st.markdown("현상명별 클레임 현황 (누수 / 소음 / 기타)")
            if '현상명' in filtered_df.columns:
                leak_count = filtered_df['현상명'].astype(str).str.contains("누수", case=False, na=False).sum()
                noise_count = filtered_df['현상명'].astype(str).str.contains("소음|이음", case=False, na=False).sum()
                other_count = len(filtered_df) - (leak_count + noise_count)
                phen_summary = pd.Series({"누수": leak_count, "소음": noise_count, "기타": max(0, other_count)})
                plot_horizontal_bar(phen_summary.sort_values(ascending=True), "", height=300)
            else:
                st.info("데이터에 '현상명' 컬럼이 존재하지 않습니다.")

            st.markdown("주행거리별 클레임 현황")
            if '주행거리Km' in filtered_df.columns:
                filtered_df['주행거리_구간'] = pd.cut(filtered_df['주행거리Km'], bins=[0, 5000, 10000, 30000, 50000, 70000, 100000, 999999], labels=['~5000', '5001~10000', '10001~30000', '30001~50000', '50001~70000', '70001~100000', '100000이상'])
                mile_grouped = filtered_df.groupby('주행거리_구간', observed=False).size()
                mile_order = ['~5000', '5001~10000', '10001~30000', '30001~50000', '50001~70000', '70001~100000', '100000이상']
                plot_horizontal_bar(mile_grouped, "", height=350, custom_order=mile_order)
            else:
                st.info("데이터에 '주행거리Km' 컬럼이 존재하지 않습니다.")

        with hb_col2:
            st.markdown("사용개월별 클레임 현황")
            if '사용개월' in filtered_df.columns:
                bins = [-1, 3, 6, 9, 12, 24, 36, 48, 60, 999999]
                labels = ['3개월 (0~3)', '6개월 (4~6)', '9개월 (7~9)', '12개월 (10~12)', '24개월 (13~24)', '36개월 (25~36)', '48개월 (37~48)', '60개월 (49~60)', '60개월 이상']
                
                temp_df = filtered_df.copy()
                temp_df['사용개월_구간'] = pd.cut(temp_df['사용개월'], bins=bins, labels=labels)
                usage_grouped = temp_df.groupby('사용개월_구간', observed=False).size()
                
                plot_horizontal_bar(usage_grouped, "", height=380, custom_order=labels)
            else:
                st.info("데이터에 '사용개월' 컬럼이 존재하지 않습니다.")

            st.markdown("차종별 클레임 현황 (상위 항목)")
            if '차종' in filtered_df.columns:
                car_grouped = filtered_df.groupby('차종').size().nlargest(15).sort_values(ascending=True)
                plot_horizontal_bar(car_grouped, "", height=380)
            else:
                st.info("데이터에 '차종' 컬럼이 존재하지 않습니다.")

        st.markdown("---")
        st.markdown(f"선택된 조건의 상세 RAW DATA 테이블 조회 (총 {len(filtered_df)}건)")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("분석할 클레임 엑셀 파일을 업로드하거나, 상단의 '구글 시트 데이터 자동 불러오기' 버튼을 눌러주세요.")

# --- 3. 개선 활동 관리 메뉴 ---
elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 관리")
    st.markdown("구글 시트 데이터를 연동하거나 엑셀 파일을 업로드하여 개선 내역을 조회, 검색, 수정할 수 있습니다.")

    col_i_up1, col_i_up2 = st.columns([2, 1])
    with col_i_up1:
        improve_uploaded_file = st.file_uploader("개선 활동 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"], key="improve_file_up")
    with col_i_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_improve_gsheet_btn = st.button("개선 활동 구글 시트 자동 불러오기", use_container_width=True)

    if improve_uploaded_file is not None:
        if st.session_state['improve_uploaded_file_name'] != improve_uploaded_file.name:
            try:
                raw_imp_df = pd.read_csv(improve_uploaded_file) if improve_uploaded_file.name.endswith('.csv') else pd.read_excel(improve_uploaded_file, sheet_name=0)
                if 'id' not in raw_imp_df.columns:
                    raw_imp_df.insert(0, 'id', range(1, len(raw_imp_df) + 1))
                st.session_state['improve_df'] = raw_imp_df
                st.session_state['improve_uploaded_file_name'] = improve_uploaded_file.name
                st.success("엑셀 파일이 성공적으로 업로드 및 반영되었습니다!")
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    if load_improve_gsheet_btn:
        try:
            imp_sheet_url = st.session_state['improve_gsheet_url']
            if not imp_sheet_url:
                st.warning("'구글 시트 연동 설정' 메뉴에서 개선 활동 구글 시트 URL을 먼저 입력해주세요.")
            else:
                if "pubhtml" in imp_sheet_url:
                    export_url = imp_sheet_url.replace("/pubhtml", "/pub?output=csv")
                elif "edit" in imp_sheet_url:
                    export_url = imp_sheet_url.split('/edit')[0] + '/export?format=csv'
                else:
                    export_url = imp_sheet_url

                raw_imp_df = pd.read_csv(export_url)
                if not raw_imp_df.empty:
                    if 'id' not in raw_imp_df.columns:
                        raw_imp_df.insert(0, 'id', range(1, len(raw_imp_df) + 1))
                    st.session_state['improve_df'] = raw_imp_df
                    st.success("구글 시트에서 개선 활동 데이터를 성공적으로 불러왔습니다!")
                    st.rerun()
                else:
                    st.error("구글 시트 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"구글 시트 연동 중 오류 발생: {e}")

    st.markdown("---")

    imp_df = st.session_state['improve_df']

    tab1, tab2 = st.tabs(["🔍 개선 내역 조회 및 검색", "➕/✏️ 신규 등록 및 수정"])

    with tab1:
        if not imp_df.empty:
            st.markdown("### 개선 활동 내역 조회 및 검색 (대상, 품명, 차종, 현상, 해당 품목, 고객사명)")

            def get_imp_filter(label, col_name):
                if col_name in imp_df.columns:
                    options = sorted([str(x) for x in imp_df[col_name].dropna().unique() if str(x) != 'nan' and str(x) != '-'])
                    return st.multiselect(f"{label}", options, key=f"imp_filter_{col_name}")
                return []

            c1, c2, c3 = st.columns(3)
            with c1: selected_targets = get_imp_filter("대상", "대상")
            with c2: selected_product_names = get_imp_filter("품명", "품명")
            with c3: selected_car_types = get_imp_filter("차종", "차종")

            c4, c5, c6 = st.columns(3)
            with c4: selected_phenomenons = get_imp_filter("현상", "현상")
            with c5: selected_parts = get_imp_filter("해당 품목", "해당 품목")
            with c6: selected_customers = get_imp_filter("고객사명", "고객사명")

            filtered_imp = imp_df.copy()
            if selected_targets and '대상' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['대상'].astype(str).isin(selected_targets)]
            if selected_product_names and '품명' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['품명'].astype(str).isin(selected_product_names)]
            if selected_car_types and '차종' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['차종'].astype(str).isin(selected_car_types)]
            if selected_phenomenons and '현상' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['현상'].astype(str).isin(selected_phenomenons)]
            if selected_parts and '해당 품목' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['해당 품목'].astype(str).isin(selected_parts)]
            if selected_customers and '고객사명' in filtered_imp.columns:
                filtered_imp = filtered_imp[filtered_imp['고객사명'].astype(str).isin(selected_customers)]

            st.markdown("---")
            st.markdown(f"조회된 개선 활동 내역 (총 {len(filtered_imp)}건)")
            
            display_imp = filtered_imp.drop(columns=['id'], errors='ignore').copy()
            styled_df = display_imp.style.set_properties(
                subset=['대책 내용'], 
                **{'white-space': 'pre-wrap', 'text-align': 'left'}
            )
            
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.info("개선 활동 데이터가 비어있습니다.")

    with tab2:
        st.markdown("### 개선 내용 신규 등록 및 기존 내역 수정")
        
        mode = st.radio("작업 선택", ["신규 등록", "기존 내역 수정"], horizontal=True)

        if mode == "기존 내역 수정":
            st.markdown("##### 🔍 수정할 항목 검색 및 필터링")
            
            def get_edit_filter(label, col_name):
                if col_name in imp_df.columns:
                    options = sorted([str(x) for x in imp_df[col_name].dropna().unique() if str(x) != 'nan' and str(x) != '-'])
                    return st.multiselect(f"{label}", options, key=f"edit_filter_{col_name}")
                return []

            e_c1, e_c2, e_c3 = st.columns(3)
            with e_c1: edit_targets = get_edit_filter("대상", "대상")
            with e_c2: edit_products = get_edit_filter("품명", "품명")
            with e_c3: edit_cars = get_edit_filter("차종", "차종")

            e_c4, e_c5, e_c6 = st.columns(3)
            with e_c4: edit_phenoms = get_edit_filter("현상", "현상")
            with e_c5: edit_parts_f = get_edit_filter("해당 품목", "해당 품목")
            with e_c6: edit_custs = get_edit_filter("고객사명", "고객사명")

            target_pool = imp_df.copy()
            if edit_targets and '대상' in target_pool.columns: target_pool = target_pool[target_pool['대상'].astype(str).isin(edit_targets)]
            if edit_products and '품명' in target_pool.columns: target_pool = target_pool[target_pool['품명'].astype(str).isin(edit_products)]
            if edit_cars and '차종' in target_pool.columns: target_pool = target_pool[target_pool['차종'].astype(str).isin(edit_cars)]
            if edit_phenoms and '현상' in target_pool.columns: target_pool = target_pool[target_pool['현상'].astype(str).isin(edit_phenoms)]
            if edit_parts_f and '해당 품목' in target_pool.columns: target_pool = target_pool[target_pool['해당 품목'].astype(str).isin(edit_parts_f)]
            if edit_custs and '고객사명' in target_pool.columns: target_pool = target_pool[target_pool['고객사명'].astype(str).isin(edit_custs)]

            if target_pool.empty:
                st.warning("선택한 조건에 해당하는 개선 내역이 없습니다.")
            else:
                def make_option_label(r):
                    part = str(r['해당 품목']) if pd.notna(r['해당 품목']) else ""
                    car = str(r['차종']) if pd.notna(r['차종']) else ""
                    measure = str(r['대책 내용']).replace('\n', ' ') if pd.notna(r['대책 내용']) else ""
                    return f"[ID:{r['id']}] 품목: {part} / 차종: {car} / 대책: {measure[:30]}..."

                imp_options = target_pool.apply(make_option_label, axis=1).tolist()
                selected_option = st.selectbox("수정할 개선 항목 선택", imp_options)
                
                if selected_option:
                    selected_id = int(selected_option.split(']')[0].replace('[ID:', ''))
                    target_row = imp_df[imp_df['id'] == selected_id].iloc[0]
                    
                    with st.form("edit_improve_form"):
                        e_target = st.text_input("대상", value=str(target_row['대상']) if pd.notna(target_row['대상']) else "")
                        e_product = st.text_input("품명", value=str(target_row['품명']) if pd.notna(target_row['품명']) else "")
                        e_car = st.text_input("차종", value=str(target_row['차종']) if pd.notna(target_row['차종']) else "")
                        e_phenomenon = st.text_input("현상", value=str(target_row['현상']) if pd.notna(target_row['현상']) else "")
                        e_measure = st.text_area("대책 내용 (줄바꿈 반영 가능)", value=str(target_row['대책 내용']) if pd.notna(target_row['대책 내용']) else "")
                        e_part = st.text_input("해당 품목", value=str(target_row['해당 품목']) if pd.notna(target_row['해당 품목']) else "")
                        e_customer = st.text_input("고객사명", value=str(target_row['고객사명']) if pd.notna(target_row['고객사명']) else "")
                        
                        try:
                            default_date = datetime.strptime(str(target_row['적용일']).split()[0], '%Y-%m-%d').date()
                        except:
                            default_date = date.today()
                        e_date = st.date_input("적용일", value=default_date)
                        e_remark = st.text_input("비고", value=str(target_row['비 고']) if pd.notna(target_row['비 고']) else "")

                        col_btn1, col_btn2 = st.columns(2)
                        submitted_edit = col_btn1.form_submit_button("수정 내용 저장", use_container_width=True)
                        submitted_delete = col_btn2.form_submit_button("이 항목 삭제하기", use_container_width=True)

                        if submitted_edit:
                            st.session_state['improve_df'].loc[st.session_state['improve_df']['id'] == selected_id, ['대상', '품명', '차종', '현상', '대책 내용', '해당 품목', '고객사명', '적용일', '비 고']] = [
                                e_target, e_product, e_car, e_phenomenon, e_measure, e_part, e_customer, str(e_date), e_remark
                            ]
                            st.success("개선 내용이 성공적으로 수정되었습니다!")
                            st.rerun()

                        if submitted_delete:
                            st.session_state['improve_df'] = st.session_state['improve_df'][st.session_state['improve_df']['id'] != selected_id].reset_index(drop=True)
                            st.success("해당 개선 항목이 삭제되었습니다!")
                            st.rerun()
        else:
            with st.form("add_improve_form"):
                new_target = st.text_input("대상 (예: 승용, 상용)")
                new_product = st.text_input("품명 (예: 워터펌프)")
                new_car = st.text_input("차종 (예: 람다, 감마 II)")
                new_phenomenon = st.text_input("현상 (예: 누수, 소음)")
                new_measure = st.text_area("대책 내용 (엔터로 줄바꿈을 반영할 수 있습니다)")
                new_part = st.text_input("해당 품목 (예: 25100-3CAC0)")
                new_customer = st.text_input("고객사명 (예: HMC, WIA, KMC, -)")
                new_date = st.date_input("적용일", value=date.today())
                new_remark = st.text_input("비고")

                submitted_imp = st.form_submit_button("개선 내용 등록", use_container_width=True)
                if submitted_imp:
                    if new_part.strip():
                        new_id = int(st.session_state['improve_df']['id'].max() + 1) if not st.session_state['improve_df'].empty else 1
                        new_row = {
                            'id': new_id,
                            '대상': new_target,
                            '품명': new_product,
                            '차종': new_car,
                            '현상': new_phenomenon,
                            '대책 내용': new_measure,
                            '해당 품목': new_part,
                            '고객사명': new_customer,
                            '적용일': str(new_date),
                            '비 고': new_remark
                        }
                        st.session_state['improve_df'] = pd.concat([st.session_state['improve_df'], pd.DataFrame([new_row])], ignore_index=True)
                        st.success("신규 개선 내용이 성공적으로 등록되었습니다!")
                        st.rerun()
                    else:
                        st.error("해당 품목은 필수 입력 항목입니다.")

# --- 4. 고객사 클레임 비용 분석 메뉴 (HKMC, WIA, 글로비스, 모비스 개별 취합 및 표준 포맷 적용) ---
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

    # 공통 표준 컬럼 정의
    target_columns = [
        '법인', '발생구분', '통보서', 'H/K', '업체', 'SEQ', 'RO년월', 'R/O번호', 'VIN', 'C/TYPE', '차종', 
        '원인부품', '원인품명', '주작업코드', '원인', '현상', '생산일자', '수리일자', '판매일자', '사용개월', 
        '주행거리', '납입율', '분담율', '적용율', '부품비', '공임비', '외주비', '합계'
    ]

    # 공통 날짜 파싱 (YY-MM-DD 형식)
    def fmt_date(val):
        if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan':
            return ''
        try:
            dt = pd.to_datetime(val)
            if pd.isna(dt):
                return str(val).split()[0].replace('.', '-')
            return dt.strftime('%y-%m-%d')
        except:
            s = str(val).split()[0].replace('.', '-')
            if len(s) == 10 and s[4] == '-' and s[7] == '-':
                return s[2:]
            return s

    # 1. HKMC 파싱 함수 (다중 시트 지원 및 헤더 자동 감지)
    def parse_hkmc_file(uploaded_file):
        if uploaded_file is None:
            return pd.DataFrame()
        try:
            xls = pd.ExcelFile(uploaded_file)
            combined = []
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
                if df_raw.empty or len(df_raw) < 1:
                    continue
                header_idx = 0
                for idx, row in df_raw.iloc[:10].iterrows():
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    if any(k in row_str for k in ["법인", "발생구분", "통보서", "R/O번호", "VIN"]):
                        header_idx = idx
                        break
                df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)
                df_sheet = df_sheet.dropna(how='all')
                if df_sheet.empty:
                    continue
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                rows = []
                for _, row in df_sheet.iterrows():
                    prod_d = fmt_date(row.get('생산일자', row.get('생산일', '')))
                    rep_d = fmt_date(row.get('수리일자', row.get('수리일', '')))
                    sale_d = fmt_date(row.get('판매일자', row.get('판매일', '')))
                    
                    raw_mile = pd.to_numeric(row.get('주행거리', row.get('주행거리(Km)', 0)), errors='coerce') or 0
                    mile_str = f"{int(raw_mile):,}"
                    use_m = pd.to_numeric(row.get('사용개월', 0), errors='coerce') or 0
                    
                    part_val = float(pd.to_numeric(row.get('부품비', 0), errors='coerce') or 0)
                    labor_val = float(pd.to_numeric(row.get('공임비', 0), errors='coerce') or 0)
                    out_val = float(pd.to_numeric(row.get('외주비', 0), errors='coerce') or 0)
                    tot_val = float(pd.to_numeric(row.get('합계', part_val + labor_val + out_val), errors='coerce') or (part_val + labor_val + out_val))
                    
                    r_dict = {
                        '법인': str(row.get('법인', sheet)),
                        '발생구분': str(row.get('발생구분', 'D')),
                        '통보서': str(row.get('통보서', '')),
                        'H/K': str(row.get('H/K', 'H')),
                        '업체': str(row.get('업체', 'RI14')),
                        'SEQ': str(row.get('SEQ', '1')),
                        'RO년월': str(row.get('RO년월', '')),
                        'R/O번호': str(row.get('R/O번호', '')),
                        'VIN': str(row.get('VIN', '')),
                        'C/TYPE': str(row.get('C/TYPE', 'W')),
                        '차종': str(row.get('차종', '')),
                        '원인부품': str(row.get('원인부품', '')),
                        '원인품명': str(row.get('원인품명', '')),
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
                return pd.concat(combined, ignore_index=True)
        except Exception as e:
            st.error(f"[HKMC] 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

    # 2. WIA 파싱 함수 (요청사항 반영)
    def parse_wia_file(uploaded_file):
        if uploaded_file is None:
            return pd.DataFrame()
        try:
            xls = pd.ExcelFile(uploaded_file)
            combined = []
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
                if df_raw.empty or len(df_raw) < 1:
                    continue
                header_idx = 0
                for idx, row in df_raw.iloc[:10].iterrows():
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    if any(k in row_str for k in ["고객통보서", "RO(클레임)번호", "VIN NO", "품번"]):
                        header_idx = idx
                        break
                df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)
                df_sheet = df_sheet.dropna(how='all')
                if df_sheet.empty:
                    continue
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                rows = []
                for _, row in df_sheet.iterrows():
                    prod_d = fmt_date(row.get('생산일', row.get('생산일자', '')))
                    rep_d = fmt_date(row.get('수리일', row.get('수리일자', '')))
                    sale_d = fmt_date(row.get('판매일', row.get('판매일자', '')))
                    
                    raw_mile = pd.to_numeric(row.get('주행거리(Km)', row.get('주행거리', 0)), errors='coerce') or 0
                    mile_str = f"{int(raw_mile):,}"
                    use_m = pd.to_numeric(row.get('사용개월', 0), errors='coerce') or 0
                    
                    part_val = float(pd.to_numeric(row.get('변제부품비', 0), errors='coerce') or 0)
                    labor_val = float(pd.to_numeric(row.get('변제공임비', 0), errors='coerce') or 0)
                    out_val = float(pd.to_numeric(row.get('변제외주비', 0), errors='coerce') or 0)
                    tot_val = float(pd.to_numeric(row.get('변제합계', part_val + labor_val + out_val), errors='coerce') or (part_val + labor_val + out_val))
                    
                    r_dict = {
                        '법인': str(sheet), # 엑셀시트 '이름' 반영
                        '발생구분': str(row.get('발생구분', 'D')),
                        '통보서': str(row.get('고객통보서', '')), # 고객통보서(B열)
                        'H/K': 'W', # 항상 W 반영
                        '업체': str(row.get('변제업체', 'RI14')),
                        'SEQ': str(row.get('SEQ', '1')),
                        'RO년월': str(row.get('RO년월', '')),
                        'R/O번호': str(row.get('RO(클레임)번호', '')), # RO(클레임)번호(F열)
                        'VIN': str(row.get('VIN NO', '')), # VIN NO(G열)
                        'C/TYPE': str(row.get('C/TYPE', 'W:일반 클레임')),
                        '차종': str(row.get('차종(표준)', '')), # 차종(표준)(I열)
                        '원인부품': str(row.get('품번', '')), # 품번(K열)
                        '원인품명': str(row.get('품명', '')),
                        '주작업코드': str(row.get('주작업코드', '')),
                        '원인': str(row.get('원인', '')),
                        '현상': str(row.get('현상', '')),
                        '생산일자': prod_d,
                        '수리일자': rep_d,
                        '판매일자': sale_d,
                        '사용개월': f"{use_m:.1f}" if use_m % 1 != 0 else str(int(use_m)),
                        '주행거리': mile_str,
                        '납입율': float(pd.to_numeric(row.get('제안분담율', 100.0), errors='coerce') or 100.0),
                        '분담율': float(pd.to_numeric(row.get('제안분담율', 19.01), errors='coerce') or 19.01),
                        '적용율': float(pd.to_numeric(row.get('제안분담율', 19.01), errors='coerce') or 19.01),
                        '부품비': part_val, # 변제부품비(V열)
                        '공임비': labor_val, # 변제공임비(W열)
                        '외주비': out_val, # 변제외주비(X열)
                        '합계': tot_val # 변제합계(Y열)
                    }
                    rows.append(r_dict)
                if rows:
                    df_sub = pd.DataFrame(rows)
                    for tc in target_columns:
                        if tc not in df_sub.columns:
                            df_sub[tc] = ''
                    combined.append(df_sub[target_columns])
            if combined:
                return pd.concat(combined, ignore_index=True)
        except Exception as e:
            st.error(f"[WIA] 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

    # 3. 글로비스 파싱 함수 (요청사항 반영: 발생구분 'E', SEQ=List No, R/O번호=RO No, 원인=원인코드, 현상=현상코드)
    def parse_globis_file(uploaded_file):
        if uploaded_file is None:
            return pd.DataFrame()
        try:
            xls = pd.ExcelFile(uploaded_file)
            combined = []
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
                if df_raw.empty or len(df_raw) < 1:
                    continue
                header_idx = 0
                for idx, row in df_raw.iloc[:10].iterrows():
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    if any(k in row_str for k in ["통보서", "List No", "RO No", "원인품번"]):
                        header_idx = idx
                        break
                df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)
                df_sheet = df_sheet.dropna(how='all')
                if df_sheet.empty:
                    continue
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                rows = []
                for _, row in df_sheet.iterrows():
                    prod_d = fmt_date(row.get('생산일', ''))
                    rep_d = fmt_date(row.get('수리일', ''))
                    sale_d = fmt_date(row.get('판매일', ''))
                    
                    raw_mile = pd.to_numeric(row.get('주행거리', 0), errors='coerce') or 0
                    mile_str = f"{int(raw_mile):,}"
                    use_m = pd.to_numeric(row.get('사용기간', 0), errors='coerce') or 0
                    
                    part_val = float(pd.to_numeric(row.get('변제 부품비', row.get('부품비', 0)), errors='coerce') or 0)
                    labor_val = float(pd.to_numeric(row.get('변제 공임비', row.get('공임비', 0)), errors='coerce') or 0)
                    out_val = float(pd.to_numeric(row.get('변제 외주비', row.get('외주비', 0)), errors='coerce') or 0)
                    tot_val = float(pd.to_numeric(row.get('변제 합계', row.get('합계', part_val + labor_val + out_val)), errors='coerce') or (part_val + labor_val + out_val))
                    
                    r_dict = {
                        '법인': str(sheet),
                        '발생구분': 'E', # 항상 E 반영
                        '통보서': str(row.get('통보서', '')),
                        'H/K': 'H',
                        '업체': str(row.get('업체', 'RI14')),
                        'SEQ': str(row.get('List No', '1')), # List No(C열)
                        'RO년월': str(row.get('RO년월', '')),
                        'R/O번호': str(row.get('RO No', '')), # RO No(F열)
                        'VIN': str(row.get('VIN', '')),
                        'C/TYPE': str(row.get('C/T', 'W')),
                        '차종': str(row.get('차종', '')),
                        '원인부품': str(row.get('원인품번', '')),
                        '원인품명': str(row.get('원인품명', '')),
                        '주작업코드': str(row.get('주작업코드', '')),
                        '원인': str(row.get('원인코드', '')), # 원인코드(I열)
                        '현상': str(row.get('현상코드', '')), # 현상코드(H열)
                        '생산일자': prod_d,
                        '수리일자': rep_d,
                        '판매일자': sale_d,
                        '사용개월': f"{use_m:.1f}" if use_m % 1 != 0 else str(int(use_m)),
                        '주행거리': mile_str,
                        '납입율': float(pd.to_numeric(row.get('분담율', 100.0), errors='coerce') * 100 if pd.notna(row.get('분담율')) and float(row.get('분담율', 0)) < 1 else 100.0),
                        '분담율': float(pd.to_numeric(row.get('분담율', 19.39), errors='coerce') * 100 if pd.notna(row.get('분담율')) and float(row.get('분담율', 0)) < 1 else 19.39),
                        '적용율': float(pd.to_numeric(row.get('분담율', 19.39), errors='coerce') * 100 if pd.notna(row.get('분담율')) and float(row.get('분담율', 0)) < 1 else 19.39),
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
                return pd.concat(combined, ignore_index=True)
        except Exception as e:
            st.error(f"[글로비스] 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

    # 4. 모비스 파싱 함수 (모비스(전) / 모비스(후) 시트별 맞춤 연동)
    def parse_mobis_file(uploaded_file):
        if uploaded_file is None:
            return pd.DataFrame()
        try:
            xls = pd.ExcelFile(uploaded_file)
            combined = []
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
                if df_raw.empty or len(df_raw) < 1:
                    continue
                header_idx = 0
                for idx, row in df_raw.iloc[:10].iterrows():
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    if any(k in row_str for k in ["클레임번호", "부품번호", "클레임유형"]):
                        header_idx = idx
                        break
                df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)
                df_sheet = df_sheet.dropna(how='all')
                if df_sheet.empty:
                    continue
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                rows = []
                for _, row in df_sheet.iterrows():
                    prod_d = fmt_date(row.get('생산일자', row.get('생산', '')))
                    rep_d = fmt_date(row.get('수리일자', row.get('수리', '')))
                    sale_d = fmt_date(row.get('판매일자', row.get('판매', '')))
                    
                    raw_mile = pd.to_numeric(row.get('주행거리', 0), errors='coerce') or 0
                    mile_str = f"{int(raw_mile):,}"
                    use_m = pd.to_numeric(row.get('사용개월', 0), errors='coerce') or 0

                    # 모비스(전) vs 모비스(후) 구분 처리
                    if "전" in sheet:
                        claim_no = str(row.get('클레임번호', ''))
                        part_no = str(row.get('부품번호', ''))
                        req_amt = float(pd.to_numeric(row.get('변제청구금액', 0), errors='coerce') or 0)
                        
                        r_dict = {
                            '법인': str(sheet),
                            '발생구분': 'D',
                            '통보서': claim_no,
                            'H/K': 'M', # 항상 M 반영
                            '업체': 'RI14',
                            'SEQ': '1',
                            'RO년월': '',
                            'R/O번호': claim_no,
                            'VIN': '',
                            'C/TYPE': 'W',
                            '차종': '',
                            '원인부품': part_no, # 부품번호(D열)
                            '원인품명': '',
                            '주작업코드': '',
                            '원인': '',
                            '현상': '',
                            '생산일자': prod_d,
                            '수리일자': rep_d,
                            '판매일자': sale_d,
                            '사용개월': '0',
                            '주행거리': '0',
                            '납입율': 100.0,
                            '분담율': 19.01,
                            '적용율': 19.01,
                            '부품비': 0.0,
                            '공임비': 0.0,
                            '외주비': req_amt, # 외주비 = 변제청구금액(E열)
                            '합계': req_amt # 합계 = 변제청구금액(E열)
                        }
                    else: # 모비스(후) 및 일반 시트
                        claim_no = str(row.get('클레임번호', ''))
                        part_no = str(row.get('원인부품번호', row.get('부품번호', '')))
                        part_name = str(row.get('원인부품명', ''))
                        phen = str(row.get('현상코드', ''))
                        cause = str(row.get('원인코드', ''))
                        vin_val = str(row.get('VIN', ''))
                        car_val = str(row.get('차종', ''))
                        
                        # 예시안3 기준 수식 계산 (부품청구금액, 공임비 등에 분담율 적용 등)
                        share_rate = float(pd.to_numeric(row.get('업체분담률\n(%)', row.get('업체분담률(%)', 19.01)), errors='coerce') or 19.01)
                        part_raw = float(pd.to_numeric(row.get('부품청구금액', 0), errors='coerce') or 0)
                        labor_raw = float(pd.to_numeric(row.get('공임비', 0), errors='coerce') or 0)
                        out_raw = float(pd.to_numeric(row.get('외주비', 0), errors='coerce') or 0)
                        
                        # 분담율 적용 부품비 및 공임비 계산
                        calc_part = round(part_raw * (share_rate / 100.0), 2) if part_raw > 0 else 0.0
                        calc_labor = round(labor_raw * (share_rate / 100.0), 2) if labor_raw > 0 else 0.0
                        tot_amt = float(pd.to_numeric(row.get('변제청구금액', calc_part + calc_labor + out_raw), errors='coerce') or (calc_part + calc_labor + out_raw))

                        r_dict = {
                            '법인': str(sheet),
                            '발생구분': str(row.get('발생구분', 'E')),
                            '통보서': claim_no,
                            'H/K': str(row.get('H/K\n구분', row.get('H/K', 'M'))), # 항상 M 반영
                            '업체': 'RI14',
                            'SEQ': '1',
                            'RO년월': '',
                            'R/O번호': claim_no, # 클레임번호(D열)
                            'VIN': vin_val,
                            'C/TYPE': 'W',
                            '차종': car_val,
                            '원인부품': part_no, # 원인부품번호(E열)
                            '원인품명': part_name,
                            '주작업코드': '',
                            '원인': cause, # 원인코드(R열)
                            '현상': phen, # 현상코드(Q열)
                            '생산일자': prod_d,
                            '수리일자': rep_d,
                            '판매일자': sale_d,
                            '사용개월': f"{use_m:.1f}" if use_m % 1 != 0 else str(int(use_m)),
                            '주행거리': mile_str,
                            '납입율': 100.0,
                            '분담율': share_rate,
                            '적용율': share_rate,
                            '부품비': calc_part,
                            '공임비': calc_labor,
                            '외주비': out_raw,
                            '합계': tot_amt
                        }
                    rows.append(r_dict)
                if rows:
                    df_sub = pd.DataFrame(rows)
                    for tc in target_columns:
                        if tc not in df_sub.columns:
                            df_sub[tc] = ''
                    combined.append(df_sub[target_columns])
            if combined:
                return pd.concat(combined, ignore_index=True)
        except Exception as e:
            st.error(f"[모비스] 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

    # 각 파일별 개별 파싱 및 세션 저장
    df_hkmc = parse_hkmc_file(file_hkmc)
    df_wia = parse_wia_file(file_wia)
    df_globis = parse_globis_file(file_globis)
    df_mobis = parse_mobis_file(file_mobis)

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
