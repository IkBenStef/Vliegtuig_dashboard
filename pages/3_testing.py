import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import geopandas as gpd
import base64

# Terminal: python -m streamlit run Dasboard_Vluchten.py



####################################################################################################
# CSS om de achtergrond en sidebar mooi te maken
def set_bg_from_local(image_file='image.png'):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    st.markdown(f"""<style>[data-testid="stAppViewContainer"]{{background-image: url("data:image/png;base64,{encoded_string.decode()}");background-size:cover;background-repeat: no-repeat;background-attachment:fixed;}}</style>""",unsafe_allow_html=True)
def set_sidebar_bg(image_file='image2.png'):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    st.markdown(f"""<style>[data-testid="stSidebar"] {{background-image: url("data:image/png;base64,{encoded_string.decode()}");background-size: cover;background-repeat: no-repeat;background-attachment: fixed;}}</style>""",unsafe_allow_html=True)

set_bg_from_local()
set_sidebar_bg()

st.markdown("""<style>[data-testid="stHeader"] {background: rgba(0,0,0,0);height: 0rem;position: fixed;z-index: 999;}[data-testid="stHeader"] [data-testid="stActionButton"] {display: none;}.block-container {padding-top: 0rem;padding-bottom: 0rem;margin-top: -2rem;}[data-testid="stSidebarUserContent"] {padding-top: 1rem;}</style>""", unsafe_allow_html=True)
red = "#db5656"
blue = "#5762d9"
####################################################################################################

# dataframes
schedule = pd.read_csv(r'case3/schedule_airport.csv')
runways_geo = pd.read_csv(r'Zurich/Zurich_runway.csv')
gates_geo = pd.read_csv(r'Zurich/Zurich_gates.csv')
airports = pd.read_csv(r'airports-extended-clean.csv', sep=';', decimal=',')

schedule['LSV'] = np.where(schedule['LSV'] == 'S', 'uitgaand', 'inkomend')
schedule['afkomst'] = np.where(schedule['LSV'] == 'inkomend', schedule['Org/Des'], 'LSZH')
schedule['bestemming'] = np.where(schedule['LSV'] == 'uitgaand', schedule['Org/Des'], 'LSZH')
schedule['andere_gate'] = schedule['TAR'] != schedule['GAT']

combinedata = schedule['STD'].astype(str) + ' ' + schedule['ATA_ATD_ltc'].astype(str)
combinedsta = schedule['STD'].astype(str) + ' ' + schedule['STA_STD_ltc'].astype(str)
schedule['ATA_ATD_ltc'] = pd.to_datetime(combinedata, format='%d/%m/%Y %H:%M:%S')
schedule['STA_STD_ltc'] = pd.to_datetime(combinedsta, format='%d/%m/%Y %H:%M:%S')
schedule['vertraagd'] = (schedule['ATA_ATD_ltc'] - schedule['STA_STD_ltc']).astype(int) >= 0

vertragin = schedule['ATA_ATD_ltc'] - schedule['STA_STD_ltc']
vervroeging = schedule['STA_STD_ltc'] - schedule['ATA_ATD_ltc']
schedule['vertraging_sec'] = vertragin.dt.total_seconds()
schedule['vertraging_min'] = vertragin.dt.total_seconds() / 60
schedule['vervroeging_sec'] = vervroeging.dt.total_seconds()
schedule['vervroeging_min'] = vervroeging.dt.total_seconds() / 60
schedule['vertraging_sec'] = schedule['vertraging_sec'].mask(schedule['vertraging_sec'] < 0)
schedule['vertraging_min'] = schedule['vertraging_min'].mask(schedule['vertraging_min'] < 0)
schedule['vervroeging_sec'] = schedule['vervroeging_sec'].mask(schedule['vervroeging_sec'] < 0)
schedule['vervroeging_min'] = schedule['vervroeging_min'].mask(schedule['vervroeging_min'] < 0)

airports = airports[airports['Type'] == 'airport']
airports = airports[['ICAO','Latitude','Longitude', 'Name', 'Country']]

groep_runway = schedule.groupby(['LSV','RWY'])['RWY'].count().reset_index(name='aantal_vluchten')
groep_runway = groep_runway.rename(columns={'RWY': 'number'})
runwaynumber_count = pd.merge(groep_runway, runways_geo, on='number')

groep_gate = schedule.groupby('GAT')['GAT'].count().reset_index(name='aantal_vluchten')
groep_gate = groep_gate.rename(columns={'GAT': 'gate'})
gate_count = groep_gate = pd.merge(groep_gate, gates_geo, on='gate')

groep_vluchten = schedule.groupby(['LSV','Org/Des'])['Org/Des'].count().reset_index(name='aantal')
groep_vluchten = pd.merge(groep_vluchten, airports, left_on='Org/Des', right_on='ICAO')

dag_gemiddelde_vluchten = schedule.groupby('STD')['FLT'].count().reset_index(name='aantal')
dag_gemiddelde_vluchten = dag_gemiddelde_vluchten['aantal'].mean().astype(int)

groep_vertraging = schedule.groupby(['LSV', 'andere_gate', 'vertraagd'])['vertraagd'].count().reset_index(name='aantal').sort_values('aantal')

groep_gate_vertraging = schedule.groupby('GAT')['vertraging_min'].sum().reset_index(name='totale_vertraging').drop(axis=1, index=0)
groep_gate_vertraging = pd.merge(groep_gate_vertraging, gates_geo, left_on='GAT', right_on='gate').drop(axis=0, columns='GAT')

groep_vluchten_vertraagd = schedule.groupby(['LSV','Org/Des'])['vertraging_min'].sum().round().reset_index(name='totale_vertraging')
groep_vluchten_vertraagd = pd.merge(groep_vluchten_vertraagd, airports, left_on='Org/Des', right_on='ICAO')
groep_vluchten_vertraagd = groep_vluchten_vertraagd[groep_vluchten_vertraagd['LSV'] == 'inkomend']

####################################################################################################


st.set_page_config(page_title='Vluchten Dashboard', layout='wide')
st.title('Vluchten van Schiphol')

with st.expander('runway'): st.dataframe(runwaynumber_count)
with st.expander('gate'): st.dataframe(gate_count)
with st.expander('airports'): st.dataframe(airports)
with st.expander('schedule'): st.dataframe(schedule)
with st.expander('dag_gemiddelde_vluchten'): st.write(dag_gemiddelde_vluchten)
with st.expander('groep_vertraging'): st.write(groep_vertraging)
with st.expander('groep_gate_vertraging'): st.write(groep_gate_vertraging)
with st.expander('groep_vluchten_vertraagd'): st.write(groep_vluchten_vertraagd)

# grafiek


st.write(runwaynumber_count)
fig_runwaynumber_count = px.bar(
    runwaynumber_count, 
    x='number', 
    y='aantal_vluchten', 
    color='LSV',
    color_discrete_sequence=[red, blue],
    barmode='group',
    title="Landingsbaan aantallen (in LOG)",
    log_y=True,
)
fig_runwaynumber_count.update_xaxes(type='category', title_text='')
fig_runwaynumber_count.update_layout(
    font=dict(size=18), 
    margin={"r":0,"t":50,"l":0,"b":50}, 
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5,
        title_text=''
    )
)
st.plotly_chart(fig_runwaynumber_count)





q99 = schedule['vertraging_min'].quantile(0.99)
lijn = px.histogram(
    data_frame=schedule,
    x='vertraging_min',
    range_x=[0, q99],
)
lijn.update_traces(xbins=dict(
    start=0,
    end=q99,
    size=1,
    
))
st.plotly_chart(lijn, use_container_width=True)

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

st.divider()
a1, a2, a3 = st.columns([2,3,7])
with a1: gekozen_vlucht = st.selectbox('kies een vlucht',('Flight 1','Flight 2','Flight 3','Flight 4','Flight 5','Flight 6','Flight 7'))
with a2: gekozen_interval = st.selectbox('kies een interval, 1 seconden of 30 seconden', ('30', '1'))

gekozen_vlucht_string = r'case3/' + str(gekozen_interval) + gekozen_vlucht + '.xlsx'

vlucht = pd.read_excel(gekozen_vlucht_string)
vlucht['TRUE AIRSPEED (derived)'] = vlucht['TRUE AIRSPEED (derived)'].replace({'\*': ''}, regex=True)
vlucht['TRUE AIRSPEED (derived)'] = pd.to_numeric(vlucht['TRUE AIRSPEED (derived)'])
vlucht['TRUE AIRSPEED (derived)'] = pd.to_numeric(vlucht['TRUE AIRSPEED (derived)'], errors='coerce')

vlucht['[3d Latitude]'] = pd.to_numeric(vlucht['[3d Latitude]'], errors='coerce')
vlucht['[3d Longitude]'] = pd.to_numeric(vlucht['[3d Longitude]'], errors='coerce')
vlucht = vlucht.dropna(subset=['[3d Latitude]', '[3d Longitude]'])
vlucht = vlucht[
    (vlucht['[3d Latitude]'] > 0) & (vlucht['[3d Latitude]'] < 180) & 
    (vlucht['[3d Longitude]'] > 0) & (vlucht['[3d Longitude]'] < 180)
]

# 1. Lijn van de vlucht
fig = px.scatter_map(vlucht, 
                     lat='[3d Latitude]', 
                     lon='[3d Longitude]',
                     zoom=4, 
                     height=600,
                     color='Time (secs)',
                     color_continuous_scale=[blue, red],
                     )

fig_scatter = px.scatter(vlucht,
                 x='Time (secs)',
                 y='[3d Altitude M]'
                 )

#waardes
boven_drempel = vlucht[vlucht['[3d Altitude M]'] >= vlucht['[3d Altitude M]'].max() -500]

if not boven_drempel.empty:
    start_cruise = boven_drempel['Time (secs)'].iloc[0]
    eind_cruise = boven_drempel['Time (secs)'].iloc[-1]
    cruise_tijd = eind_cruise - start_cruise
    ascend_tijd = start_cruise - vlucht.loc[0, 'Time (secs)']
    onder_drempel = vlucht[vlucht['Time (secs)'] > eind_cruise]
    onder_drempel = onder_drempel[onder_drempel['[3d Altitude M]'] < vlucht['[3d Altitude M]'].max() -500]
    
    if not onder_drempel.empty:
        start_descend = onder_drempel['Time (secs)'].iloc[0]
        descend_tijd = vlucht['Time (secs)'].iloc[-1] - start_descend



st.plotly_chart(fig, use_container_width=True, height=700)
st.plotly_chart(fig_scatter)

st.write(f"--- Vluchtfases ---")
st.write(f"Tijd tot bereiken cruise: {ascend_tijd/60:.1f} minuten")
st.write(f"Tijd in cruise fase: {cruise_tijd/60:.1f} minuten")
st.write(f"Tijd in daalfase: {descend_tijd/60:.1f} minuten")
st.write(f"Totale tijd: {vlucht['Time (secs)'].iloc[-1]/60:.1f} minuten - {vlucht['Time (secs)'].iloc[-1]/60/60:.1f} uur")


fig = px.scatter(groep_gate_vertraging,
                 x='lon',
                 y='lat',
                 size='totale_vertraging',
                 )
st.plotly_chart(fig)



st.dataframe(groep_vluchten)



fig_airport = px.scatter_map(groep_vluchten,
                             lat='Latitude',
                             lon='Longitude',
                             color='LSV',
                             color_discrete_map={'inkomend':blue, 'uitgaand':red},
                             size='aantal',
                             size_max=20,
                             opacity=0.5,
                             zoom=1,
                             hover_data={'Latitude': False, 'Longitude': False,  'aantal': True, 'Name': True},
                             )
st.plotly_chart(fig_airport)
