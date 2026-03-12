import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64

# Terminal: python -m streamlit run Layout.py

####################################################################################################
# CSS om de achtergrond en sidebar mooi te maken, met dank aan ai
def set_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    st.markdown(f"""<style>[data-testid="stAppViewContainer"]{{background-image: url("data:image/png;base64,{encoded_string.decode()}");background-size:cover;background-repeat: no-repeat;background-attachment:fixed;}}</style>""",unsafe_allow_html=True)
def set_sidebar_bg(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    st.markdown(f"""<style>[data-testid="stSidebar"] {{background-image: url("data:image/png;base64,{encoded_string.decode()}");background-size: cover;background-repeat: no-repeat;background-attachment: fixed;}}</style>""",unsafe_allow_html=True)

set_bg_from_local('image.png')
set_sidebar_bg('image2.png')

st.markdown("""<style>[data-testid="stHeader"] {background: rgba(0,0,0,0);height: 0rem;position: fixed;z-index: 999;}[data-testid="stHeader"] [data-testid="stActionButton"] {display: none;}.block-container {padding-top: 0rem;padding-bottom: 0rem;margin-top: -2rem; /* Soms nodig om de laatste pixels te corrigeren */}[data-testid="stSidebarUserContent"] {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

####################################################################################################
# dataframes
schedule = pd.read_csv(r'case3\schedule_airport.csv')
vlucht_1 = pd.read_excel(r'case3\30Flight 1.xlsx')
runways_geo = pd.read_csv(r'Zurich\zurich_runway.csv')
gates_geo = pd.read_csv(r'Zurich\zurich_gates84.csv')

schedule['LSV'] = np.where(schedule['LSV'] == 'S', 'opgestegen', 'geland')
schedule['afkomst'] = np.where(schedule['LSV'] == 'geland', schedule['Org/Des'], 'LSZH')
schedule['bestemming'] = np.where(schedule['LSV'] == 'opgestegen', schedule['Org/Des'], 'LSZH')
schedule['andere_gate'] = schedule['TAR'] != schedule['GAT']

combinedata = schedule['STD'].astype(str) + ' ' + schedule['ATA_ATD_ltc'].astype(str)
combinedsta = schedule['STD'].astype(str) + ' ' + schedule['STA_STD_ltc'].astype(str)
schedule['ATA_ATD_ltc'] = pd.to_datetime(combinedata, format='%d/%m/%Y %H:%M:%S')
schedule['STA_STD_ltc'] = pd.to_datetime(combinedsta, format='%d/%m/%Y %H:%M:%S')

vertragin = schedule['ATA_ATD_ltc'] - schedule['STA_STD_ltc']
vervroeging = schedule['STA_STD_ltc'] - schedule['ATA_ATD_ltc']
schedule['vertraging_sec'] = vertragin.dt.total_seconds()
schedule['vertraging_min'] = vertragin.dt.total_seconds() / 60
schedule['vertraging_uur'] = vertragin.dt.total_seconds() / 3600
schedule['vervroeging_sec'] = vervroeging.dt.total_seconds()
schedule['vervroeging_min'] = vervroeging.dt.total_seconds() / 60
schedule['vervroeging_uur'] = vervroeging.dt.total_seconds() / 3600
schedule['vertraging_sec'] = schedule['vertraging_sec'].mask(schedule['vertraging_sec'] < 0)
schedule['vertraging_min'] = schedule['vertraging_min'].mask(schedule['vertraging_min'] < 0)
schedule['vertraging_uur'] = schedule['vertraging_uur'].mask(schedule['vertraging_uur'] < 0)
schedule['vervroeging_sec'] = schedule['vervroeging_sec'].mask(schedule['vervroeging_sec'] < 0)
schedule['vervroeging_min'] = schedule['vervroeging_min'].mask(schedule['vervroeging_min'] < 0)
schedule['vervroeging_uur'] = schedule['vervroeging_uur'].mask(schedule['vervroeging_uur'] < 0)

groep = schedule.groupby(['LSV','RWY'])['RWY'].count()
groep = groep.reset_index(name='aantal_vluchten')
groep = groep.rename(columns={'RWY': 'number'})
runwaynumber_count = pd.merge(groep, runways_geo, on='number')

aantal_vluchten = schedule['FLT'].count()
gem_vertraging = schedule['vertraging_min'].mean().round(2)
####################################################################################################

st.sidebar.title('Menu')
st.title('Vliegtuigen dashboard van Zurich en Schiphol')

fig = px.line()
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_runway = px.scatter_map(
    runwaynumber_count,
    lon='lon',
    lat='lat',
    color='LSV',
    color_discrete_map={'geland': "#5762d9", 'opgestegen': "#db5656"}, 
    size='aantal_vluchten',
    size_max=100,
    hover_data=['aantal_vluchten'],
    zoom=12,
    opacity=0.5,
    title='Vluchtdata van Zurich Airport'
)
fig_runway.add_trace(go.Scattermap(
    lat=gates_geo['lat'],
    lon=gates_geo['lon'],
    mode='markers',
    marker=dict(
        size=10, 
        color="#cb8325"
    ),
    name='Gates', 
    text=gates_geo['gate'],
    opacity=0.3
))
fig_runway.add_trace(go.Scattermap(
    lat=runways_geo['lat'],
    lon=runways_geo['lon'],
    mode='markers+text',
    text=runways_geo['number'],
    texttemplate='%{text}',  # Dwingt het renderen van de tekst-waarde
    textposition='top center',
    textfont=dict(color='black', size=16),
    marker=dict(size=0, color='white'),
    hoverinfo='skip',
    name='landingsbaan nummers'
))
fig_runway.update_layout(margin={"r":0,"t":25,"l":0,"b":0},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')


st.set_page_config(layout='wide', page_title='Layout')

# a zijn de grafieken
a1, a2, a3, a4 = st.columns(4)
with a1: 
    st.plotly_chart(fig, key=1, height=300)

with a2:
     st.plotly_chart(fig, key=2, height=300)

with a3:
     st.plotly_chart(fig, key=3, height=300)

with a4:
     st.plotly_chart(fig, key=4, height=300)

# B is de kaart links en rechts wat waardes
b1, b2 = st.columns([6,1])

with b1:
    st.plotly_chart(fig_runway, key=5, height=430)

with b2:
    st.success(f'Totaal aantal vluchten: {aantal_vluchten}')
    st.success(f'Gemiddelde vertraging (in minuten): {gem_vertraging}')