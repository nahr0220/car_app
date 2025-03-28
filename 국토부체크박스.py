import streamlit as st
import pandas as pd

# ✅ 레이아웃 설정
st.set_page_config(layout="wide")
st.title("🚘 국토부 데이터 가격 분포도")
st.subheader("📊 2024년 국산 이전 데이터")

# ✅ 엑셀 데이터 불러오기
df = pd.read_excel("국토부_pricerange_국산_연료추가.xlsx")

# ✅ 1단계: 제조사 선택
selected_maker = st.selectbox("제조사", sorted(df['제조사'].dropna().unique()))

# ✅ 2단계: 제조사에 따른 모델명3 리스트 생성
model_options = df[df['제조사'] == selected_maker]['모델명3'].dropna().unique()
selected_model = st.selectbox("모델명3", sorted(model_options))

# ✅ 3단계: 제조사 + 모델명3에 따른 연료 리스트 생성
fuel_options = df[
    (df['제조사'] == selected_maker) &
    (df['모델명3'] == selected_model)
]['연료'].dropna().unique()
selected_fuel = st.selectbox("연료", sorted(fuel_options))

# ✅ 최종 필터링
filtered = df[
    (df['제조사'] == selected_maker) &
    (df['모델명3'] == selected_model) &
    (df['연료'] == selected_fuel)
]

# ✅ 차량 수 출력
total_count = filtered['count'].sum()
st.markdown(f"**🚗 선택한 조건의 전체 차량 수: {int(total_count):,} 대**")

# ✅ 단위 표시 (오른쪽 정렬)
st.markdown("<div style='text-align: right;'>📌 단위: 만 원 (₩)</div>", unsafe_allow_html=True)

# ✅ 주행거리 정렬
km_order = ['~3만km', '~6만km', '~9만km', '~12만km', '12만km초과']
filtered['KM2'] = pd.Categorical(filtered['KM2'], categories=km_order, ordered=True)

# ✅ 기간(MONTHS) 정렬
month_order = ['~1년', '~2년', '~3년', '~4년', '~5년', '~6년', '~7년',
               '7~10년', '10~15년', '15~20년', '20년 초과']

if not filtered.empty:
    # ✅ 피벗 테이블 생성
    mean = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='mean')
    min_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='min')
    max_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='max')

    # ✅ 열 순서 재정렬
    available_months = [m for m in month_order if m in mean.columns]
    mean = mean[available_months]
    min_ = min_[available_months]
    max_ = max_[available_months]

    # ✅ mean + (min~max) 문자열로 합치기
    combined = mean.copy()
    for col in available_months:
        combined[col] = [
            f"{int(m):,}<br>({int(mi):,} ~ {int(ma):,})" if pd.notna(m) and pd.notna(mi) and pd.notna(ma)
            else "None"
            for m, mi, ma in zip(mean[col], min_[col], max_[col])
        ]

    # ✅ 중복값은 빈칸 처리
    combined = combined.reset_index()

    # ✅ 여기 추가
    combined.rename(columns={"모델명2": "모델", "KM2": "주행거리"}, inplace=True)


    combined['제조사'] = combined['제조사'].mask(combined['제조사'].duplicated()).fillna("")
    combined['모델'] = combined['모델'].mask(combined['모델'].duplicated()).fillna("")

    # ✅ HTML 테이블 출력 (줄바꿈 포함)
    st.markdown(combined.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")