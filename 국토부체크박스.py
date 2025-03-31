import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🚘 국토부 데이터 가격 분포도")
st.markdown("🔍 제조사, 모델명, 연료를 선택하면 평균 가격과 범위를 확인할 수 있어요.")
st.subheader("📊 2024년 국산 이전 데이터")

# ✅ 엑셀 불러오기
df = pd.read_excel("국토부_pricerange_국산_연료추가.xlsx")

# ✅ 고정 구간 정의
km_order = ['~3만km', '~6만km', '~9만km', '~12만km', '12만km초과']
month_order = ['~1년', '~2년', '~3년', '~4년', '~5년', '~6년', '~7년',
               '7~10년', '10~15년', '15~20년', '20년 초과']

# ✅ 콤보박스
selected_maker = st.selectbox("제조사", [""] + sorted(df['제조사'].dropna().unique()), index=0)

if selected_maker:
    model_options = df[df['제조사'] == selected_maker]['모델명3'].dropna().unique()
    selected_model = st.selectbox("모델", [""] + sorted(model_options), index=0)

    if selected_model:
        fuel_options = df[
            (df['제조사'] == selected_maker) &
            (df['모델명3'] == selected_model)
        ]['연료'].dropna().unique()
        selected_fuel = st.selectbox("연료", [""] + sorted(fuel_options), index=0)

        if selected_fuel:
            # ✅ 필터링
            filtered = df[
                (df['제조사'] == selected_maker) &
                (df['모델명3'] == selected_model) &
                (df['연료'] == selected_fuel)
            ]

            # ✅ 차량 수
            total_count = filtered['count'].sum()
            st.markdown(f"**🚗 선택한 조건의 전체 차량 수: {int(total_count):,} 대**")
            st.markdown("<div style='text-align: right;'>📌 단위: 만 원 (₩)</div>", unsafe_allow_html=True)

            filtered['KM2'] = pd.Categorical(filtered['KM2'], categories=km_order, ordered=True)

            if not filtered.empty:
                # ✅ 피벗 테이블
                mean = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='mean')
                min_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='min')
                max_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='max')
                count_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values='count')

                for df_ in [mean, min_, max_, count_]:
                    df_.columns.name = None
                    for col in month_order:
                        if col not in df_.columns:
                            df_[col] = pd.NA
                    df_ = df_.reindex(columns=month_order)

                full_index = pd.MultiIndex.from_product(
                    [filtered['제조사'].unique(), filtered['모델명2'].unique(), km_order],
                    names=['제조사', '모델명2', 'KM2']
                )
                mean = mean.reindex(index=full_index)
                min_ = min_.reindex(index=full_index)
                max_ = max_.reindex(index=full_index)
                count_ = count_.reindex(index=full_index)

                # ✅ 조합 텍스트
                combined = mean.copy()
                for col in month_order:
                    combined[col] = [
                        f"<span style='font-weight:900; font-size:1.1em;'>{int(m):,}</span><br>({int(mi):,} ~ {int(ma):,})<br>[{int(c)}건]"
                        if pd.notna(m) and pd.notna(mi) and pd.notna(ma) and pd.notna(c)
                        else " "
                        for m, mi, ma, c in zip(mean[col], min_[col], max_[col], count_[col])
                    ]

                combined = combined.reset_index()
                combined.rename(columns={"모델명2": "모델", "KM2": "주행거리"}, inplace=True)
                if "MONTHS" in combined.columns:
                    combined.drop(columns="MONTHS", inplace=True)

                combined['제조사'] = combined['제조사'].mask(combined['제조사'].duplicated()).fillna("")
                combined['모델'] = combined['모델'].mask(combined['모델'].duplicated()).fillna("")

                # ✅ 표 출력
                st.markdown(combined.to_html(escape=False, index=False), unsafe_allow_html=True)

                # ✅ 회색 박스 설명 추가
                st.markdown("""
                <br>
                <div style="
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid #ddd;
                    line-height: 1.6;
                    font-size: 0.95rem;
                ">
                <b>ℹ️ 표 구성 안내</b><br>
                - '기간'은 차량이전일에서 최초출고일을 뺀 값입니다.<br>
                - 모델은 세부 모델명을 대표 차종 기준으로 통합한 값입니다.<br>
                - 가격은 <b>평균값</b>, 아래에는 <i>(최소~최대)</i> 범위와 <b> [건수]</b>가 함께 제공되며,<br>
                &nbsp;&nbsp;&nbsp;<u>데이터는 하위 20% 제외한 기준값</u>입니다.
                </div>
                """, unsafe_allow_html=True)

            else:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")