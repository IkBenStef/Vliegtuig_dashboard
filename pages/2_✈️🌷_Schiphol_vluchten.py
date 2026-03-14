import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64

# Terminal: python -m streamlit run Layout.py

####################################################################################################
# CSS om de achtergrond en sidebar mooi te maken
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

st.markdown("""<style>[data-testid="stHeader"] {background: rgba(0,0,0,0);height: 0rem;position: fixed;z-index: 999;}[data-testid="stHeader"] [data-testid="stActionButton"] {display: none;}.block-container {padding-top: 0rem;padding-bottom: 0rem;margin-top: -2rem;}[data-testid="stSidebarUserContent"] {padding-top: 1rem;}</style>""", unsafe_allow_html=True)
red = "#db5656"
blue = "#5762d9"
####################################################################################################


st.sidebar.title('Settings')
with st.sidebar:
    gekozen_vlucht = st.selectbox('kies een vlucht',('Flight 1','Flight 2','Flight 3','Flight 4','Flight 5','Flight 6','Flight 7'))
    gekozen_interval = st.selectbox('kies een interval, 1 seconden of 30 seconden', ('30', '1'))

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
fig_vlucht = px.scatter_map(vlucht, 
                     lat='[3d Latitude]', 
                     lon='[3d Longitude]',
                     zoom=4, 
                     height=600,
                     color='Time (secs)',
                     color_continuous_scale=[blue, red],
                     )
fig_vlucht.update_layout(margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_altitude = px.scatter(vlucht,
                 x='Time (secs)',
                 y='[3d Altitude M]'
                 )
fig_altitude.update_layout(margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
fig_airspeed = px.scatter(vlucht,
                 x='Time (secs)',
                 y='TRUE AIRSPEED (derived)'
                 )
fig_airspeed.update_layout(margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')


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








####################################################################################################
# Streamlit

st.title('Vluchten vanaf Schiphol Airport')
st.set_page_config(layout='wide', page_title='Layout')



# B is de kaart links en rechts wat waardes
b1, b2 = st.columns([5,1])
with b1:
    st.plotly_chart(fig_vlucht, key=5, height=430)

    a1, a2 = st.columns(2)
    with a1: 
        st.plotly_chart(fig_altitude, key=1, height=300)

    with a2:
         st.plotly_chart(fig_airspeed, key=2, height=300)



with b2:
    with st.expander('Info 📊', expanded=True): 
        st.markdown("**🔘 Vluchtfases**")
        st.text(f"Tijd tot bereiken cruise: {ascend_tijd/60:.1f} minuten")
        st.text(f"Tijd in cruise fase: {cruise_tijd/60:.1f} minuten")
        st.text(f"Tijd in daalfase: {descend_tijd/60:.1f} minuten")
        st.text(f"Totale tijd: {vlucht['Time (secs)'].iloc[-1]/60:.1f} minuten - {vlucht['Time (secs)'].iloc[-1]/60/60:.1f} uur")
        st.markdown('**🔘 Statestieken**')
        st.text(f'Maximale snelheid: {vlucht['TRUE AIRSPEED (derived)'].max()} km/u')
        st.text(f'Hoogste hoogte gevlogen: {vlucht['[3d Altitude M]'].max()/1000} km')
        st.text('nog meer info')
        st.text('nog meer info')

with st.expander('ruew vluchtdata'): st.dataframe(vlucht)
