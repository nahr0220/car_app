import streamlit as st
import pandas as pd
import numpy as np

# 엑셀 파일 불러오기
df = pd.read_excel("C:/Users/24100801/OneDrive - 오토플러스(주)/나혜린/현물/국토부_app/제목 없는 스프레드시트 (3).xlsx")

# 기본적인 UI
st.title("중고차 평균 가격 조회")

# 체크박스 선택
selected_models = st.multiselect("모델명3을 선택하세요", sorted(df['모델명3'].dropna().unique()))
selected_fuels = st.multiselect("연료를 선택하세요", sorted(df['연료'].dropna().unique()))

# 필터링
filtered = df[
    df['모델명3'].isin(selected_models) &
    df['연료'].isin(selected_fuels)
]

# 피벗 테이블 생성
if not filtered.empty:
    pivot = filtered.pivot_table(
        index=['모델명2', 'KM2'],
        columns='MONTHS',
        values='mean',
        aggfunc='mean'
    )

    st.dataframe(pivot)
else:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")