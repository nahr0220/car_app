import streamlit as st
import pandas as pd

# ✅ 레이아웃 설정
st.set_page_config(layout="wide")
st.title("🚘 국토부 데이터 가격 분포도")
st.subheader("📊 2024년 국산 이전 데이터")

# ✅ 엑셀 데이터 불러오기
df = pd.read_excel("국토부_pricerange_국산_연료추가.xlsx")

# ✅ 콤보박스: 제조사 → 모델명3 → 연료
selected_maker = st.selectbox("제조사", sorted(df['제조사'].dropna().unique()))

model_options = df[df['제조사'] == selected_maker]['모델명3'].dropna().unique()
selected_model = st.selectbox("모델명3", sorted(model_options))

fuel_options = df[
    (df['제조사'] == selected_maker) &
    (df['모델명3'] == selected_model)
]['연료'].dropna().unique()
selected_fuel = st.selectbox("연료", sorted(fuel_options))

# ✅ 필터링
filtered = df[
    (df['제조사'] == selected_maker) &
    (df['모델명3'] == selected_model) &
    (df['연료'] == selected_fuel)
]

# ✅ 전체 차량 수
total_count = filtered['count'].sum()
st.markdown(f"**🚗 선택한 조건의 전체 차량 수: {int(total_count):,} 대**")

# ✅ 단위 안내
st.markdown("<div style='text-align: right;'>📌 단위: 만 원 (₩)</div>", unsafe_allow_html=True)

# ✅ 고정 주행거리 / 기간 구간 설정
km_order = ['~3만km', '~6만km', '~9만km', '~12만km', '12만km초과']
filtered['KM2'] = pd.Categorical(filtered['KM2'], categories=km_order, ordered=True)

month_order = ['~1년', '~2년', '~3년', '~4년', '~5년', '~6년', '~7년',
               '7~10년', '10~15년', '15~20년', '20년 초과']

if not filtered.empty:
    # ✅ 피벗 테이블
    mean = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='mean')
    min_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='min')
    max_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='max')

    # ✅ MONTHS 열 누락 구간 추가 + 순서 고정
    for df_name, df_ in zip(['mean', 'min_', 'max_'], [mean, min_, max_]):
        for col in month_order:
            if col not in df_.columns:
                df_[col] = pd.NA
        if df_name == 'mean':
            mean = df_.reindex(columns=month_order)
        elif df_name == 'min_':
            min_ = df_.reindex(columns=month_order)
        else:
            max_ = df_.reindex(columns=month_order)

    # ✅ 주행거리 인덱스 순서 강제 고정
    unique_makers = filtered['제조사'].dropna().unique()
    unique_models = filtered['모델명2'].dropna().unique()

    full_index = pd.MultiIndex.from_product(
        [unique_makers, unique_models, km_order],
        names=['제조사', '모델명2', 'KM2']
    )

    mean = mean.reindex(index=full_index)
    min_ = min_.reindex(index=full_index)
    max_ = max_.reindex(index=full_index)

    # ✅ 평균 + 범위 문자열 조합
    combined = mean.copy()
    for col in month_order:
        combined[col] = [
            f"{int(m):,}<br>({int(mi):,} ~ {int(ma):,})" if pd.notna(m) and pd.notna(mi) and pd.notna(ma)
            else "None"
            for m, mi, ma in zip(mean[col], min_[col], max_[col])
        ]

    # ✅ 컬럼 정리
    combined = combined.reset_index()
    combined.rename(columns={"모델명2": "모델", "KM2": "주행거리"}, inplace=True)

    # ✅ 중복은 빈칸 처리
    combined['제조사'] = combined['제조사'].mask(combined['제조사'].duplicated()).fillna("")
    combined['모델'] = combined['모델'].mask(combined['모델'].duplicated()).fillna("")

    # ✅ 표 출력
    st.markdown(combined.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")