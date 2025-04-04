import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# 초기화 버튼 동작 처리
if "reset_triggered" not in st.session_state:
    st.session_state.reset_triggered = False

def reset_filters():
    st.session_state.selected_maker = ""
    st.session_state.selected_model = ""
    st.session_state.selected_fuel = ""
    st.session_state.reset_triggered = True

# 👉 타이틀과 파일선택 + 초기화 버튼을 같은 줄에 배치
title_col, file_col, reset_col = st.columns([6, 2, 1])
with title_col:
    st.title("🚘 국토부 데이터 가격 분포도")

with file_col:
    file_options = {
        "20% 제거": ("국토부_pricerange_국산_연료추가.xlsx", "#e8f4fd"),
        "30% 제거": ("국토부_pricerange_국산_연료추가30%.xlsx", "#fff3cd"),
        "40% 제거": ("국토부_pricerange_국산_연료추가40%.xlsx", "#fde2e2")
    }

    # 기준 데이터 선택
    st.markdown('<div style="font-size: 0.75rem;">📂 기준 데이터 선택</div>', unsafe_allow_html=True)
    selected_file_label = st.selectbox(
        "",
        list(file_options.keys()),
        label_visibility="collapsed",
        key="file_selectbox"
    )
    selected_file, bg_color = file_options[selected_file_label]

    # 데이터 형식 선택
    st.markdown('<div style="font-size: 0.75rem; margin-top: 6px;">📊 데이터 형식</div>', unsafe_allow_html=True)
    data_type = st.selectbox(
        "",
        ["가격", "감가율"],
        label_visibility="collapsed",
        key="data_type"
    )

    # 안내 문구
    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 0.75rem;
            margin-top: -10px;
            text-align: right;
        ">
        ✅ 기준: <b>{selected_file_label}</b> 데이터 사용 중
        </div>
        """,
        unsafe_allow_html=True
    )

with reset_col:
    st.write("")
    st.write("")
    if st.button("🔄 조건 초기화"):
        reset_filters()

st.markdown("🔍 제조사, 모델, 연료를 선택하면 평균 가격과 범위를 확인할 수 있어요.")
st.subheader("📊 2024년 국산 이전 데이터")

# 🔄 선택한 파일 불러오기
df = pd.read_excel(selected_file)

# 고정 구간 정의
km_order = ['~3만km', '~6만km', '~9만km', '~12만km', '12만km초과']
month_order = ['~1년', '~2년', '~3년', '~4년', '~5년', '~6년', '~7년',
               '~8년', '~9년', '~10년', '~11년', '~12년', '~13년', '~14년',
               '~15년', '~16년', '~17년', '~18년', '~19년', '~20년', '20년 초과']

# ✅ 콤보박스: 제조사, 모델, 연료
selected_maker = st.selectbox(
    "제조사", [""] + sorted(df['제조사'].dropna().unique()),
    index=0,
    key="selected_maker"
)

if selected_maker:
    model_options = df[df['제조사'] == selected_maker]['모델명3'].dropna().unique()
    selected_model = st.selectbox(
        "모델", [""] + sorted(model_options),
        index=0,
        key="selected_model"
    )

    if selected_model:
        fuel_options = df[
            (df['제조사'] == selected_maker) & 
            (df['모델명3'] == selected_model)
        ]['연료'].dropna().unique()
        selected_fuel = st.selectbox(
            "연료", [""] + sorted(fuel_options),
            index=0,
            key="selected_fuel"
        )

        if selected_fuel:
            filtered = df[
                (df['제조사'] == selected_maker) &
                (df['모델명3'] == selected_model) &
                (df['연료'] == selected_fuel)
            ]

            suffix = "가격" if data_type == "가격" else "감가"
            total_count = filtered[f'count_{suffix}'].sum()
            st.markdown(f"**🚗 선택한 조건의 전체 차량 수: {int(total_count):,} 대**")
            st.markdown(f"<div style='text-align: right;'>📌 단위: <b>{'퍼센트(%)' if data_type == '감가율' else '만 원 (₩)'}</b></div>", unsafe_allow_html=True)

            filtered['KM2'] = pd.Categorical(filtered['KM2'], categories=km_order, ordered=True)

            if not filtered.empty:
                mean_col = f"mean_{suffix}"
                min_col = f"min_{suffix}"
                max_col = f"max_{suffix}"
                count_col = f"count_{suffix}"

                mean = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values=mean_col)
                min_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values=min_col)
                max_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values=max_col)
                count_ = filtered.pivot_table(index=['제조사', '모델명2', 'KM2'], columns='MONTHS', values=count_col)

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

                combined = mean.copy()
                for col in month_order:
                    combined[col] = [
                        f"<span style='font-weight:900; font-size:1.1em;'>{round(m,1) if data_type=='감가율' else int(m):,}</span><br>"
                        f"({round(mi,1) if data_type=='감가율' else int(mi):,} ~ {round(ma,1) if data_type=='감가율' else int(ma):,})<br>[{int(c)}건]"
                        if pd.notna(m) and pd.notna(mi) and pd.notna(ma) and pd.notna(c)
                        else " "
                        for m, mi, ma, c in zip(mean[col], min_[col], max_[col], count_[col])
                    ]

                combined = combined.reset_index()
                combined.rename(columns={"모델명2": "모델", "KM2": "주행거리"}, inplace=True)
                combined = combined[['제조사', '모델', '주행거리'] + month_order]

                combined['제조사'] = combined['제조사'].mask(combined['제조사'].duplicated()).fillna("")
                combined['모델'] = combined['모델'].mask(combined['모델'].duplicated()).fillna("")

                st.markdown(combined.to_html(escape=False, index=False), unsafe_allow_html=True)

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
                본 표는 국토교통부 공공데이터를 기반으로, 모델, 차령(연식), 주행거리, 연료 종류를 기준으로 중고차 매매거래가의 통계값을 정리한 자료입니다.
                <ul>
                <li><b>차령 (1년~20년)</b> : 차량 이전 등록일과 최초 출고일의 차이를 기준으로 산출한 연식 구간입니다.</li>
                <li><b>모델명</b> : 세부 트림이나 등급 구분 없이, 통합된 차량 모델명을 기준으로 정리하였습니다.</li>
                <li><b>데이터 형식</b> : 아래 두 가지 형식 중 선택할 수 있으며, 동일한 구조의 표로 제공됩니다.
                    <ul>
                        <li><b>가격</b> : 중고차 매매거래가 기준 통계값</li>
                        <li><b>감가율</b> : 최초 신차 가격 대비 거래가의 감가율</li>
                    </ul>
                </li>
                <li><b>표시 정보</b> : 아래 세 가지 항목이 함께 표기됩니다.
                    <ol>
                    <li>평균값</li>
                    <li>최소~최대 범위</li>
                    <li>해당 조건에 포함된 거래 건수</li>
                    </ol>
                    <div style="margin-top: 5px;">
                    ※ 단, 사고 여부가 확인되지 않은 점을 고려하여, 
                    <b>선택한 기준(20% / 30% / 40%)에 따라 하위 가격 데이터를 제외</b>한 후 산출된 값입니다.
                    </div>
                </li>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
