import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="QA & 필드 클레임 통합 관리", page_icon="📊", layout="wide")

st.title("📊 품질보증 및 필드 클레임 통합 관리 대시보드")
st.markdown("인터넷 브라우저로 접속하여 필드 클레임 현황, 개선 활동, 고객사 비용을 통합 관리하는 시스템입니다.")

# 사이드바 메뉴 (라디오 버튼을 사용하여 클릭형 리스트로 나열)
st.sidebar.markdown("## 🧭 메뉴 목록")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["🏠 대시보드 & 일정", "📈 필드 클레임 현황", "🔧 개선 활동 관리", "💰 고객사 클레임 비용 분석", "☁️ 구글 시트 연동 설정"],
    label_visibility="collapsed"  # "메뉴 선택"이라는 글자 숨기기
)

if menu == "🏠 대시보드 & 일정":
    st.subheader("오늘 해야 할 일 (Today's Todo)")
    st.checkbox("[현대위아] 10월 클레임 비용 정산 2차 검토 및 보고서 반영", value=False)
    st.checkbox("워터 펌프 어셈블리 소음 이슈 원인 분석 결과 회신", value=False)
    st.checkbox("구글 드라이브 클레임 원본 데이터 동기화 확인", value=True)
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("이번 달 총 클레임", "142 건", "12% 증가")
    col2.metric("당일 처리 대상", "5 건", "긴급 2건")
    col3.metric("진행 중 개선", "3 건", "적용 대기 1건")
    col4.metric("누적 클레임 비용", "₩ 42,580,000")

elif menu == "📈 필드 클레임 현황":
    st.subheader("생산 품목별 필드 클레임 누적 현황")
    st.markdown("구글 시트 원본 데이터 기반 자동 집계 분석 화면입니다.")
    
    chart_data = pd.DataFrame({
        '클레임 발생 건수': [65, 42, 25, 10]
    }, index=['쿨런트 펌프 (K3)', '워터 펌프 (Cee\'d)', '쿨런트 펌프 (쏘렌토)', '기타 부품'])
    st.bar_chart(chart_data)

elif menu == "🔧 개선 활동 관리":
    st.subheader("품목별 개선 내용 및 적용 현황 타임라인")
    data = {
        "품번 / 부품명": ["251002B700 (쿨런트 펌프)", "251003CAC0 (PUMP ASSY)"],
        "주요 불량 현상": ["엔진 소음/이음", "성능 불량 / 누수"],
        "개선 조치 내용": ["임펠러 금형 수정 및 실링재 변경", "하우스 가스켓 조립 공정 치구 보완"],
        "적용 시점": ["2026-07-15 (Lot: 26G15)", "2026-11-01 (예정)"],
        "상태": ["적용 완료", "적용 대기"]
    }
    st.table(pd.DataFrame(data))

elif menu == "💰 고객사 클레임 비용 분석":
    st.subheader("고객사별 클레임 비용 2차 가공 및 분석")
    st.info("현대, 모비스, 현대위아, 글로비스 원본 시트 자동 취합 및 환율/분담율 계산 결과가 여기에 표시됩니다.")
    
    cost_data = {
        "고객사": ["현대 / 글로비스", "현대위아", "모비스"],
        "합산/청구 비용": ["₩ 18,450,000", "₩ 12,300,000", "₩ 11,830,000"]
    }
    st.dataframe(pd.DataFrame(cost_data), use_container_width=True)

elif menu == "☁️ 구글 시트 연동 설정":
    st.subheader("구글 드라이브 & 스프레드시트 연동")
    st.text_input("필드 클레임 현황 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    st.text_input("고객사 클레임 비용 구글 시트 URL", "https://docs.google.com/spreadsheets/d/...")
    if st.button("연동 정보 저장"):
        st.success("구글 클라우드 스프레드시트와 성공적으로 연동되었습니다!")
