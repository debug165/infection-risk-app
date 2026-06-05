import streamlit as st
import pandas as pd

st.set_page_config(page_title="감염병 취약성 진단 시스템", page_icon="🦠")

# ===== 원본 분석 로직 =====
def load_and_preprocess_data():
    pop_df = pd.read_csv('전국인구.csv', encoding='cp949', skiprows=[0])
    inf_df = pd.read_csv('감염병지역신고.csv', encoding='cp949')
    med_df = pd.read_csv('의료기관진료현황.csv', encoding='cp949')
    pub_med_df = pd.read_csv('전국공공의료기관.csv', encoding='cp949')
    hc_df = pd.read_csv('보건진료소.csv', encoding='cp949')

    pop_df.columns = ['지역명_원본', '총인구', '남자', '여자']
    pop_df = pop_df[pop_df['지역명_원본'] != '전국'].copy()
    pop_df['총인구'] = pd.to_numeric(pop_df['총인구'], errors='coerce')

    regions = ['서울','부산','대구','인천','광주','대전','울산','세종','경기','강원','충북','충남','전북','전남','경북','경남','제주']
    inf_totals = {r: pd.to_numeric(inf_df[r], errors='coerce').sum() for r in regions}
    inf_sum_df = pd.DataFrame(list(inf_totals.items()), columns=['지역명','감염병건수'])

    med_df = med_df[med_df['입원및외래별(1)']=='합계'].copy()

    mapping = {
        '서울특별시':'서울','부산광역시':'부산','대구광역시':'대구','인천광역시':'인천',
        '광주광역시':'광주','대전광역시':'대전','울산광역시':'울산','세종특별자치시':'세종',
        '경기도':'경기','강원특별자치도':'강원','충청북도':'충북','충청남도':'충남',
        '전북특별자치도':'전북','전라남도':'전남','경상북도':'경북','경상남도':'경남',
        '제주특별자치도':'제주'
    }

    pop_df['지역명']=pop_df['지역명_원본'].map(mapping)
    med_df['지역명']=med_df['시도별(1)'].map(mapping)
    pub_med_df['지역명']=pub_med_df['시도별(1)'].map(mapping)
    hc_df['지역명']=hc_df['시도별(1)'].map(mapping)

    master = pop_df[['지역명','총인구']].dropna()
    master = master.merge(inf_sum_df,on='지역명')
    master = master.merge(med_df[['지역명','진료실인원수 (명)']],on='지역명')
    master = master.merge(pub_med_df[['지역명','공공의료기관 (개소)']],on='지역명')
    master = master.merge(hc_df[['지역명','합계']],on='지역명')

    master.columns=['지역명','총인구','감염병건수','일반진료인원','공공의료기관수','보건인프라수']
    return master

def analyze(df):
    df['위험도']=(df['감염병건수']/df['총인구'])*10000
    df['취약도']=(df['일반진료인원']/df['총인구'])*10000
    df['대응력']=((df['공공의료기관수']+df['보건인프라수'])/df['총인구'])*10000

    for col in ['위험도','취약도','대응력']:
        df[col+'_점수']=(df[col]-df[col].min())/(df[col].max()-df[col].min())

    df['취약지수']=df['위험도_점수']+df['취약도_점수']-df['대응력_점수']
    df['등급']=pd.qcut(df['취약지수'],5,labels=['E','D','C','B','A'])
    return df

@st.cache_data
def get_data():
    return analyze(load_and_preprocess_data())

df = get_data()

st.title("🦠 감염병 취약성 진단 시스템")
st.write("지역을 선택하면 취약성 분석 결과를 확인할 수 있습니다.")

region = st.selectbox("지역 선택", sorted(df['지역명'].tolist()))

row = df[df['지역명']==region].iloc[0]

grade_color = {
    'A':'🔴','B':'🟠','C':'🟡','D':'🟢','E':'🔵'
}

st.metric("취약 등급", f"{grade_color[str(row['등급'])]} {row['등급']}")

st.metric("취약 지수", f"{row['취약지수']:.2f}")

st.subheader("세부 지표")
st.write(f"위험도: 인구 1만명당 {row['위험도']:.2f}건")
st.write(f"취약도: 인구 1만명당 {row['취약도']:.2f}명")
st.write(f"대응력: 인구 1만명당 {row['대응력']:.2f}개소")

st.bar_chart(df.set_index('지역명')['취약지수'])
