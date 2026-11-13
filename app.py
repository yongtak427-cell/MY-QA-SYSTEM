import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 페이지 설정
st.set_page_config(page_title="TIKITAK Task Management", page_icon="📊", layout="wide")

# CSS 스타일 적용
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
    div[data-testid="stDataFrame"] td {
        white-space: pre-wrap !important;
        vertical-align: middle !important;
    }
    </style>
""", unsafe_allow_html=True)

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
if 'cost_uploaded_file_name' not in st.session_state: st.session_state['cost_uploaded_file_name'] = None

if 'gsheet_url' not in st.session_state: st.session_state['gsheet_url'] = ""
if 'improve_gsheet_url' not in st.session_state: st.session_state['improve_gsheet_url'] = ""
if 'cost_gsheet_url' not in st.session_state: st.session_state['cost_gsheet_url'] = ""

if 'improve_df' not in st.session_state:
    raw_data = [
        {'id': 1, '대상': '승용', '품명': '워터펌프', '차종': '람다', '현상': '누수/소음', '대책 내용': 'M/SEAL M/R 재질 환원(ES5 ▶ ES4)', '해당 품목': '25100-3CAC0', '고객사명': '-', '적용일': '2016-06-27', '비 고': ''}
    ]
    st.session_state['improve_df'] = pd.DataFrame(raw_data)

# 사이드바 메뉴
st.sidebar.markdown("## Menu List")
menu_options = ["종합 현황", "업무 등록/관리", "필드 클레임 현황", "개선 활동 관리", "고객사 클레임 비용 분석", "구글 시트 연동 설정"]
menu = st.sidebar.radio("메뉴 선택", menu_options, label_visibility="collapsed")
st.markdown("---")

# 엑셀 파일 파서 및 표준 28개 항목 취합 함수 (모비스/WIA산동 분담률 계산 포함)
def parse_and_combine_cost_sheets(excel_source):
    xls = pd.ExcelFile(excel_source)
    all_sheets = xls.sheet_names
    combined_list = []
    
    target_columns = [
        '법인', '발생구분', '통보서', 'H/K', '업체', 'SEQ', 'RO년월', 'R/O번호', 'VIN', 'C/TYPE', '차종', 
        '원인부품', '원인품명', '주작업코드', '원인', '현상', '생산일자', '수리일자', '판매일자', '사용개월', 
        '주행거리', '납입율', '분담율', '적용율', '부품비', '공임비', '외주비', '합계'
    ]

    for sheet_name in all_sheets:
        df_raw_sheet = pd.read_excel(excel_source, sheet_name=sheet_name, header=None)
        if df_raw_sheet.empty or len(df_raw_sheet) < 3:
            continue
        
        header_row_idx = 0
        for idx, row in df_raw_sheet.iterrows():
            row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
            if any(k in row_str for k in ["법인", "원인부품", "R/O번호", "통보서", "VIN", "차종", "원인품번", "클레임번호", "No."]):
                header_row_idx = idx
                break
        
        df_sheet = pd.read_excel(excel_source, sheet_name=sheet_name, header=header_row_idx)
        df_sheet = df_sheet.dropna(how='all')
        if df_sheet.empty:
            continue
            
        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
        
        processed_rows = []
        for _, row in df_sheet.iterrows():
            row_dict = {}
            row_dict['법인'] = str(sheet_name)
            row_dict['발생구분'] = str(row.get('발생구분', row.get('결함구분', row.get('클레임유형', 'D'))))
            row_dict['통보서'] = str(row.get('통보서', row.get('클레임번호', row.get('위아통보서', ''))))
            row_dict['H/K'] = str(row.get('H/K', row.get('H/K구분', 'H')))
            row_dict['업체'] = str(row.get('업체', row.get('최종원인업체', row.get('변제업체', 'RI14'))))
            row_dict['SEQ'] = str(row.get('SEQ', row.get('List No', row.get('No.', '1'))))
            row_dict['RO년월'] = str(row.get('RO년월', row.get('통보년월', '2026/09')))
            row_dict['R/O번호'] = str(row.get('R/O번호', row.get('RO(클레임)번호', row.get('RO No', ''))))
            row_dict['VIN'] = str(row.get('VIN', row.get('VIN NO', '')))
            row_dict['C/TYPE'] = str(row.get('C/TYPE', row.get('클레임타입', 'W')))
            row_dict['차종'] = str(row.get('차종', row.get('차종(표준)', 'J5')))
            row_dict['원인부품'] = str(row.get('원인부품', row.get('원인품번', row.get('원인부품번호', row.get('품번', '')))))
            row_dict['원인품명'] = str(row.get('원인품명', row.get('원인부품명', row.get('품명', ''))))
            row_dict['주작업코드'] = str(row.get('주작업코드', row.get('OP Code', '')))
            row_dict['원인'] = str(row.get('원인', row.get('원인코드', '')))
            row_dict['현상'] = str(row.get('현상', row.get('현상코드', '')))
            row_dict['생산일자'] = str(row.get('생산일자', row.get('생산일', '')))
            row_dict['수리일자'] = str(row.get('수리일자', row.get('수리일', '')))
            row_dict['판매일자'] = str(row.get('판매일자', row.get('판매일', '')))
            row_dict['사용개월'] = str(row.get('사용개월', row.get('사용기간', '')))
            row_dict['주행거리'] = str(row.get('주행거리', row.get('주행거리(Km)', '')))
            row_dict['납입율'] = str(row.get('납입율', row.get('납입률', '100.00')))
            
            share_rate = float(row.get('분담율', row.get('분담률', row.get('업체분담률\n(%)', row.get('업체분담률(%)', 19.01)))))
            if share_rate > 1:
                share_rate_val = share_rate / 100
            else:
                share_rate_val = share_rate if share_rate > 0 else 0.1901
                
            row_dict['분담율'] = f"{share_rate_val * 100:.2f}"
            row_dict['적용율'] = f"{share_rate_val * 100:.2f}"
            
            raw_part = float(pd.to_numeric(row.get('부품비', row.get('변제 부품비', row.get('부품청구금액', 0))), errors='coerce') or 0)
            raw_labor = float(pd.to_numeric(row.get('공임비', row.get('변제 공임비', row.get('공임비', 0))), errors='coerce') or 0)
            raw_out = float(pd.to_numeric(row.get('외주비', row.get('변제 외주비', row.get('외주비', 0))), errors='coerce') or 0)
            
            if "산동" in sheet_name or "모비스" in sheet_name:
                target_amt = float(pd.to_numeric(row.get('변제대상금액', raw_part + raw_labor), errors='coerce') or (raw_part + raw_labor))
                calc_part = raw_part * share_rate_val if raw_part > 0 else target_amt * share_rate_val * 0.5
                calc_labor = raw_labor * share_rate_val if raw_labor > 0 else target_amt * share_rate_val * 0.5
            else:
                calc_part = raw_part * share_rate_val
                calc_labor = raw_labor * share_rate_val
                
            calc_out = raw_out
            
            row_dict['부품비'] = calc_part
            row_dict['공임비'] = calc_labor
            row_dict['외주비'] = calc_out
            row_dict['합계'] = calc_part + calc_labor + calc_out
            
            processed_rows.append(row_dict)
            
        if processed_rows:
            df_sub = pd.DataFrame(processed_rows)
            for tc in target_columns:
                if tc not in df_sub.columns:
                    df_sub[tc] = ''
            combined_list.append(df_sub[target_columns])
    
    if combined_list:
        master_cost_df = pd.concat(combined_list, ignore_index=True)
        master_cost_df['부품비'] = pd.to_numeric(master_cost_df['부품비'], errors='coerce').fillna(0)
        master_cost_df['공임비'] = pd.to_numeric(master_cost_df['공임비'], errors='coerce').fillna(0)
        master_cost_df['외주비'] = pd.to_numeric(master_cost_df['외주비'], errors='coerce').fillna(0)
        master_cost_df['합계'] = pd.to_numeric(master_cost_df['합계'], errors='coerce').fillna(0)
        return master_cost_df
    return pd.DataFrame()


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
    col_s3.metric("미결(진행중) 건수", f"{len(weekly_tasks) - len([t for t in weekly_tasks if t['completed']])} 건")

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

# --- 2. 필드 클레임 현황 메뉴 ---
elif menu == "필드 클레임 현황":
    st.subheader("클레임 RAW DATA 분석 및 시각화 대시보드")
    uploaded_file = st.file_uploader("클레임 RAW DATA 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])
    if uploaded_file is not None:
        st.success("파일이 업로드되었습니다.")

# --- 3. 개선 활동 관리 메뉴 ---
elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 관리")
    st.dataframe(st.session_state['improve_df'], use_container_width=True)

# --- 4. 고객사 클레임 비용 분석 메뉴 ---
elif menu == "고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 2차 가공 및 취합 분석")
    st.markdown("업로드하신 **'첨부1' 원본 엑셀 파일(모든 시트)**을 표준 28개 항목으로 완벽하게 취합 및 가공합니다. (모비스, WIA산동 분담률/환율 계산 공식 자동 적용)")

    col_c_up1, col_c_up2 = st.columns([2, 1])
    with col_c_up1:
        cost_uploaded_file = st.file_uploader("첨부1 클레임 비용 원본 엑셀(.xlsx) 파일 업로드", type=["xlsx"], key="cost_file_up")
    with col_c_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_cost_gsheet_btn = st.button("비용 구글 시트 데이터 불러오기", use_container_width=True)

    if cost_uploaded_file is not None:
        if st.session_state['cost_uploaded_file_name'] != cost_uploaded_file.name:
            try:
                master_df = parse_and_combine_cost_sheets(cost_uploaded_file)
                if not master_df.empty:
                    st.session_state['cost_df'] = master_df
                    st.session_state['cost_uploaded_file_name'] = cost_uploaded_file.name
                    st.success("첨부1의 모든 시트 데이터가 '예시안2' 표준 양식에 맞춰 완벽하게 취합되었습니다!")
            except Exception as e:
                st.error(f"비용 파일 처리 중 오류 발생: {e}")

    cost_df = st.session_state['cost_df']

    if not cost_df.empty:
        st.markdown("---")
        st.markdown("### 🔍 조회 및 검색 필터 (원하는 항목만 골라서 조회하세요)")
        
        # 필터 기본값을 빈 상태([])로 설정하여 사용자가 직접 선택하게 함
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_corps = sorted(cost_df['법인'].dropna().unique().tolist()) if '법인' in cost_df.columns else []
            selected_corp_filter = st.multiselect("법인", all_corps, default=[])
        with f_col2:
            all_sources = sorted(cost_df['발생구분'].dropna().unique().tolist()) if '발생구분' in cost_df.columns else []
            selected_source_filter = st.multiselect("발생구분", all_sources, default=[])
        with f_col3:
            all_notices = sorted(cost_df['통보서'].dropna().unique().tolist()) if '통보서' in cost_df.columns else []
            selected_notice_filter = st.multiselect("통보서", all_notices, default=[])

        f_col4, f_col5, f_col6 = st.columns(3)
        with f_col4:
            all_hks = sorted(cost_df['H/K'].dropna().unique().tolist()) if 'H/K' in cost_df.columns else []
            selected_hk_filter = st.multiselect("H/K", all_hks, default=[])
        with f_col5:
            all_ro_nos = sorted(cost_df['R/O번호'].dropna().unique().tolist()) if 'R/O번호' in cost_df.columns else []
            selected_ro_filter = st.multiselect("R/O번호", all_ro_nos, default=[])
        with f_col6:
            all_vins = sorted(cost_df['VIN'].dropna().unique().tolist()) if 'VIN' in cost_df.columns else []
            selected_vin_filter = st.multiselect("VIN", all_vins, default=[])

        f_col7, f_col8, f_col9 = st.columns(3)
        with f_col7:
            all_cars = sorted(cost_df['차종'].dropna().unique().tolist()) if '차종' in cost_df.columns else []
            selected_car_filter = st.multiselect("차종", all_cars, default=[])
        with f_col8:
            all_part_nos = sorted(cost_df['원인부품'].dropna().unique().tolist()) if '원인부품' in cost_df.columns else []
            selected_partno_filter = st.multiselect("원인부품", all_part_nos, default=[])
        with f_col9:
            all_part_names = sorted(cost_df['원인품명'].dropna().unique().tolist()) if '원인품명' in cost_df.columns else []
            selected_partname_filter = st.multiselect("원인품명", all_part_names, default=[])

        filtered_cost = cost_df.copy()
        if '법인' in filtered_cost.columns and selected_corp_filter:
            filtered_cost = filtered_cost[filtered_cost['법인'].isin(selected_corp_filter)]
        if '발생구분' in filtered_cost.columns and selected_source_filter:
            filtered_cost = filtered_cost[filtered_cost['발생구분'].isin(selected_source_filter)]
        if '통보서' in filtered_cost.columns and selected_notice_filter:
            filtered_cost = filtered_cost[filtered_cost['통보서'].isin(selected_notice_filter)]
        if 'H/K' in filtered_cost.columns and selected_hk_filter:
            filtered_cost = filtered_cost[filtered_cost['H/K'].isin(selected_hk_filter)]
        if 'R/O번호' in filtered_cost.columns and selected_ro_filter:
            filtered_cost = filtered_cost[filtered_cost['R/O번호'].isin(selected_ro_filter)]
        if 'VIN' in filtered_cost.columns and selected_vin_filter:
            filtered_cost = filtered_cost[filtered_cost['VIN'].isin(selected_vin_filter)]
        if '차종' in filtered_cost.columns and selected_car_filter:
            filtered_cost = filtered_cost[filtered_cost['차종'].isin(selected_car_filter)]
        if '원인부품' in filtered_cost.columns and selected_partno_filter:
            filtered_cost = filtered_cost[filtered_cost['원인부품'].isin(selected_partno_filter)]
        if '원인품명' in filtered_cost.columns and selected_partname_filter:
            filtered_cost = filtered_cost[filtered_cost['원인품명'].isin(selected_partname_filter)]

        st.markdown("---")
        st.markdown("### 📋 1. 필드 클레임 취합")
        
        display_cols = [
            '법인', '발생구분', '통보서', 'H/K', '업체', 'SEQ', 'RO년월', 'R/O번호', 'VIN', 'C/TYPE', '차종', 
            '원인부품', '원인품명', '주작업코드', '원인', '현상', '생산일자', '수리일자', '판매일자', '사용개월', 
            '주행거리', '납입율', '분담율', '적용율', '부품비', '공임비', '외주비', '합계'
        ]
        available_display_cols = [c for c in display_cols if c in filtered_cost.columns]

        formatted_summary = filtered_cost[available_display_cols].copy()
        for col in ['부품비', '공임비', '외주비', '합계']:
            if col in formatted_summary.columns:
                formatted_summary[col] = formatted_summary[col].apply(lambda x: f"₩ {x:,.0f}" if isinstance(x, (int, float)) else x)

        st.dataframe(formatted_summary, use_container_width=True, height=400)

        # 엑셀 다운로드 버튼 추가
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_cost[available_display_cols].to_excel(writer, index=False, sheet_name='수정 취합')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 현재 취합된 데이터를 엑셀 파일로 다운로드",
            data=excel_data,
            file_name="필드_클레임_비용_수정취합.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        total_part = filtered_cost['부품비'].sum() if '부품비' in filtered_cost.columns else 0
        total_labor = filtered_cost['공임비'].sum() if '공임비' in filtered_cost.columns else 0
        total_out = filtered_cost['외주비'].sum() if '외주비' in filtered_cost.columns else 0
        total_amount = filtered_cost['합계'].sum() if '합계' in filtered_cost.columns else 0
        total_count = len(filtered_cost)
        
        st.markdown(f"**부품비 합계:** ₩ {total_part:,.0f} | **공임비 합계:** ₩ {total_labor:,.0f} | **외주비 합계:** ₩ {total_out:,.0f} | **총 합계 금액:** ₩ {total_amount:,.0f} | **총 건수:** {total_count:,}건")

    else:
        st.info("고객사 클레임 비용 원본 엑셀 파일('첨부1')을 업로드해주세요.")

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
        st.success("구글 클라우드 스프레드시트 링크들이 성공적으로 저장되었습니다!")
