import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정 (레이아웃 넓게 설정)
st.set_page_config(page_title="TIKITAK Task Management", page_icon="📊", layout="wide")

# CSS 스타일: 화면 여백 최적화
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

# 클레임 데이터 세션 유지 보장
if 'claim_df' not in st.session_state: st.session_state['claim_df'] = pd.DataFrame()
if 'uploaded_file_name' not in st.session_state: st.session_state['uploaded_file_name'] = None
if 'gsheet_url' not in st.session_state: st.session_state['gsheet_url'] = "https://docs.google.com/spreadsheets/d/..."

# 사이드바 메뉴 (Menu List)
st.sidebar.markdown("## 🧭 Menu List")
menu_options = ["업무 현황", "필드 클레임 현황", "개선 활동 관리", "고객사 클레임 비용 분석", "구글 시트 연동 설정"]
menu = st.sidebar.radio("메뉴 선택", menu_options, label_visibility="collapsed")

st.markdown("---")

# --- 1. 업무 현황 메뉴 ---
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
                        bg, fg = ("#fee2e2", "#991b1b") if cat == '고객제출' else ("#dbeafe", "#1e40af") if cat == '자료작성' else ("#fef08a", "#854d0e")
                        t_style = "text-decoration: line-through; color: #94a3b8;" if t['completed'] else f"color: {fg}; font-weight: bold;"
                        badges_html += f"<span style='font-size:9px; background:{bg}; color:{fg}; padding:1px 3px; border-radius:3px;'><b style='{t_style}'>{cat}</b></span>"
                    badges_html += "</div>"
                    st.markdown(f"<div style='min-height:75px;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"### 📌 선택한 날짜: {st.session_state['selected_date']} 업무 현황")
        target_tasks = [t for t in st.session_state['tasks'] if str(t['date']) == str(st.session_state['selected_date'])]
        if not target_tasks:
            st.info("선택된 날짜에 등록된 업무가 없습니다.")
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
                c_bg, c_fg = ("#fee2e2", "#991b1b") if cat == '고객제출' else ("#dbeafe", "#1e40af") if cat == '자료작성' else ("#fef08a", "#854d0e")
                update_tag = f" | <span style='color: #f59e0b; font-size: 12px;'>수정일자 : {task['updated_date']}</span>" if task.get('updated_date') else ""

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
        editing_task = next((t for t in st.session_state['tasks'] if t['id'] == st.session_state['editing_task_id']), None)
        if editing_task:
            st.markdown(f"### ✏️ 기존 업무 내용 수정 (ID: {editing_task['id']})")
            if st.button("❌ 수정 취소하기"):
                st.session_state['editing_task_id'] = None
                st.rerun()
        else:
            st.markdown("### ✍️ 신규 일정 등록")

        with st.form("task_manage_form"):
            f_title = st.text_input("업무 제목", value=editing_task['title'] if editing_task else "")
            f_date = st.date_input("일정 날짜", value=editing_task['date'] if editing_task else st.session_state['selected_date'])
            f_deadline = st.date_input("마감 기한", value=editing_task['deadline'] if editing_task else date.today())
            categories = ["고객제출", "업체접수", "자료작성"]
            f_category = st.selectbox("카테고리 선택", categories, index=categories.index(editing_task['category']) if editing_task and editing_task['category'] in categories else 0)
            f_requester = st.text_input("요청자", value=editing_task['requester'] if editing_task else "")
            f_memo = st.text_area("메모 및 상세 내용", value=editing_task['memo'] if editing_task else "")
            
            col_f1, col_f2 = st.columns(2)
            submitted_new = col_f1.form_submit_button("일정 저장 및 달력 반영", use_container_width=True)
            submitted_update = col_f2.form_submit_button("내용 수정/등록", use_container_width=True)

            if submitted_new and not editing_task:
                if f_title.strip():
                    st.session_state['tasks'].append({
                        "id": len(st.session_state['tasks']) + 1, "title": f_title, "date": f_date,
                        "deadline": f_deadline, "memo": f_memo, "requester": f_requester,
                        "category": f_category, "completed": False, "completed_date": None, "updated_date": None
                    })
                    st.success("일정이 저장되었습니다!")
                    st.rerun()

            if submitted_update and editing_task:
                if f_title.strip():
                    editing_task.update({
                        "title": f_title, "date": f_date, "deadline": f_deadline,
                        "category": f_category, "requester": f_requester, "memo": f_memo,
                        "updated_date": datetime.today().strftime('%y-%m-%d')
                    })
                    st.session_state['editing_task_id'] = None
                    st.success("수정되었습니다!")
                    st.rerun()

# --- 2. 필드 클레임 현황 메뉴 ---
elif menu == "필드 클레임 현황":
    st.subheader("📈 클레임 RAW DATA 분석 및 시각화 대시보드")
    st.markdown("구글 시트에 등록된 데이터를 불러오거나 엑셀 파일을 업로드하여 클레임 분석을 진행하세요.")

    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader("클레임 RAW DATA 엑셀(.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])
    with col_up2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_gsheet_btn = st.button("🔄 구글 시트 데이터 자동 불러오기", use_container_width=True)

    if uploaded_file is not None:
        if st.session_state['uploaded_file_name'] != uploaded_file.name:
            try:
                raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, sheet_name=0)
                # BL열(현상명), BH열(현상상세) 컬럼명 매핑 보장
                if len(raw_df.columns) > 63:
                    raw_df.rename(columns={raw_df.columns[63]: '현상명'}, inplace=True)
                if len(raw_df.columns) > 59:
                    raw_df.rename(columns={raw_df.columns[59]: '현상상세'}, inplace=True)
                st.session_state['claim_df'] = raw_df
                st.session_state['uploaded_file_name'] = uploaded_file.name
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    if load_gsheet_btn:
        try:
            sheet_url = st.session_state['gsheet_url']
            export_url = sheet_url.split('/edit')[0] + '/export?format=csv' if "edit" in sheet_url else sheet_url
            raw_df = pd.read_csv(export_url)
            if len(raw_df.columns) > 63:
                raw_df.rename(columns={raw_df.columns[63]: '현상명'}, inplace=True)
            if len(raw_df.columns) > 59:
                raw_df.rename(columns={raw_df.columns[59]: '현상상세'}, inplace=True)
            st.session_state['claim_df'] = raw_df
            st.success("구글 시트에서 데이터를 성공적으로 불러왔습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"구글 시트 연동 중 오류 발생: {e}")

    df = st.session_state['claim_df']

    if not df.empty:
        st.markdown("---")
        st.markdown("#### 🔍 클레임 조회 (직접 검색 및 다중 선택 가능)")

        def get_multiselect_filter(label, col_name, custom_options=None):
            if col_name in df.columns:
                if custom_options is not None:
                    options = custom_options
                else:
                    options = sorted([str(x) for x in df[col_name].dropna().unique()])
                return st.multiselect(f"{label}", options, key=f"filter_{col_name}")
            return []

        # 요청하신 항목별 배치 (현상명은 '누수', '소음', '기타'만 검색/선택 가능하게 설정)
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

        # 필터링 적용 로직
        filtered_df = df.copy()
        if selected_part_nos: filtered_df = filtered_df[filtered_df['품번'].astype(str).isin(selected_part_nos)]
        if selected_part_names: filtered_df = filtered_df[filtered_df['부품명'].astype(str).isin(selected_part_names)]
        if selected_cars: filtered_df = filtered_df[filtered_df['차종'].astype(str).isin(selected_cars)]
        
        # 현상명(BL열) 필터링: 사용자가 선택한 '누수', '소음', '기타' 키워드가 포함된 데이터 매칭
        if selected_phen_names and '현상명' in filtered_df.columns:
            phen_mask = pd.Series(False, index=filtered_df.index)
            for p in selected_phen_names:
                phen_mask |= filtered_df['현상명'].astype(str).str.contains(p, case=False, na=False)
            filtered_df = filtered_df[phen_mask]

        if selected_phen_details and '현상상세' in filtered_df.columns: 
            filtered_df = filtered_df[filtered_df['현상상세'].astype(str).isin(selected_phen_details)]

        if selected_prod_months: filtered_df = filtered_df[filtered_df['생산월'].astype(str).isin(selected_prod_months)]
        if selected_sales_months and '판매월' in filtered_df.columns: filtered_df = filtered_df[filtered_df['판매월'].astype(str).isin(selected_sales_months)]
        if selected_repair_months: filtered_df = filtered_df[filtered_df['수리월'].astype(str).isin(selected_repair_months)]
        if selected_vins: filtered_df = filtered_df[filtered_df['VIN'].astype(str).isin(selected_vins)]
        if selected_countries: filtered_df = filtered_df[filtered_df['판매국가'].astype(str).isin(selected_countries)]
        if selected_plants: filtered_df = filtered_df[filtered_df['공장'].astype(str).isin(selected_plants)]

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

        # 1. 상단 추이 분석 그래프 (생산월: 파란색 막대 [좌측 축] & 수리월: 빨간색 꺾은선 [우측 축])
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
                fig.update_yaxes(title_text="<b>생산건수 (좌측)</b>", secondary_y=False, showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(title_text="<b>수리건수 (우측)</b>", secondary_y=True, showgrid=False)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("시각화할 데이터가 없습니다.")
        else:
            st.info("표시할 트렌드 데이터가 없습니다.")

        st.markdown("---")

        # 2. 하단 다각도 분석 (수평 막대 그래프: 누수/소음/기타 집계 및 사용개월 높이 최적화)
        st.markdown("### 2. 다각도 클레임 현황 분석 (수평 막대 그래프)")
        
        def plot_horizontal_bar(data_series, title_text, top_n=15, height=450):
            if data_series.empty:
                st.info("데이터 없음")
                return
            if len(data_series) > top_n:
                data_series = data_series.nlargest(top_n)
            data_series = data_series.sort_values(ascending=True)
            
            fig = go.Figure(go.Bar(
                x=data_series.values,
                y=[str(i) for i in data_series.index],
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
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(tickfont=dict(size=11), type='category')
            )
            st.plotly_chart(fig, use_container_width=True)

        hb_col1, hb_col2 = st.columns(2)

        with hb_col1:
            st.markdown("##### 📊 현상명별 클레임 현황 (누수 / 소음 / 기타)")
            if '현상명' in filtered_df.columns:
                # 누수, 소음, 기타 카테고리별 집계 생성
                leak_count = filtered_df['현상명'].astype(str).str.contains("누수", case=False, na=False).sum()
                noise_count = filtered_df['현상명'].astype(str).str.contains("소음|이음", case=False, na=False).sum()
                other_count = len(filtered_df) - (leak_count + noise_count)
                phen_summary = pd.Series({"누수": leak_count, "소음": noise_count, "기타": max(0, other_count)})
                plot_horizontal_bar(phen_summary, "", top_n=3, height=300)
            else:
                st.info("데이터 없음")

            st.markdown("##### 📊 주행거리별 클레임 현황")
            if '주행거리Km' in filtered_df.columns:
                filtered_df['주행거리_구간'] = pd.cut(filtered_df['주행거리Km'], bins=[0, 5000, 10000, 30000, 50000, 70000, 100000, 999999], labels=['~5000', '5001~10000', '10001~30000', '30001~50000', '50001~70000', '70001~100000', '100000이상'])
                plot_horizontal_bar(filtered_df.groupby('주행거리_구간', observed=False).size(), "", top_n=10, height=350)
            else:
                st.info("데이터 없음")

        with hb_col2:
            st.markdown("##### 📊 사용개월별 클레임 현황")
            if '사용개월' in filtered_df.columns:
                # 사용개월별 데이터 높이 축소 및 가독성 최적화
                usage_series = filtered_df.groupby('사용개월').size()
                plot_horizontal_bar(usage_series, "", top_n=20, height=380)
            else:
                st.info("데이터 없음")

            st.markdown("##### 📊 차종별 클레임 현황 (상위 항목)")
            if '차종' in filtered_df.columns:
                plot_horizontal_bar(filtered_df.groupby('차종').size(), "", top_n=15, height=380)
            else:
                st.info("데이터 없음")

        st.markdown("---")
        st.markdown(f"##### 📋 선택된 조건의 상세 RAW DATA 테이블 조회 (총 {len(filtered_df)}건)")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("분석할 클레임 엑셀 파일을 업로드하거나, 상단의 '구글 시트 데이터 자동 불러오기' 버튼을 눌러주세요.")

# --- 3. 개선 활동 관리 메뉴 ---
elif menu == "개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 타임라인")
    st.table(pd.DataFrame({
        "품번 / 부품명": ["251002B700 (쿨런트 펌프)", "251003CAC0 (PUMP ASSY)"],
        "주요 불량 현상": ["엔진 소음/이음", "성능 불량 / 누수"],
        "개선 조치 내용": ["임펠러 금형 수정 및 실링재 변경", "하우스 가스켓 조립 공정 치구 보완"],
        "적용 시점": ["2026-07-15 (Lot: 26G15)", "2026-11-01 (예정)"],
        "상태": ["적용 완료", "적용 대기"]
    }))

# --- 4. 고객사 클레임 비용 분석 메뉴 ---
elif menu == "고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 2차 가공 및 분석")
    st.info("현대, 모비스, 현대위아, 글로비스 원본 시트 자동 취합 및 환율/분담율 계산 결과가 여기에 표시됩니다.")
    st.dataframe(pd.DataFrame({"고객사": ["현대 / 글로비스", "현대위아", "모비스"], "합산/청구 비용": ["₩ 18,450,000", "₩ 12,300,000", "₩ 11,830,000"]}), use_container_width=True)

# --- 5. 구글 시트 연동 설정 메뉴 ---
elif menu == "구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동")
    gsheet_input = st.text_input("필드 클레임 현황 구글 시트 URL", st.session_state['gsheet_url'])
    if st.button("연동 정보 저장"):
        st.session_state['gsheet_url'] = gsheet_input
        st.success("구글 클라우드 스프레드시트 URL이 성공적으로 저장되었습니다! 이제 '필드 클레임 현황' 메뉴에서 '구글 시트 데이터 자동 불러오기'를 사용할 수 있습니다.")
