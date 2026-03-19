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


zurich_img = 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Aerial_view_of_the_Zurich_Airport%2C_April_2019.jpg'
schiphol_img = 'https://velvetescape.com/wp-content/uploads/2011/05/IMG_7018-640x480.jpeg'

st.set_page_config(layout='wide', page_title='Dashboard')
st.title('Dashboard over vlieg data ✈️')

with st.expander('In dit dashboard zitten twee losse onderdelen:',expanded=True): 
    st.subheader('- Het vliegveld Zurich Airport')
    st.text('Met data over Zurich airport en een analyse in vluchtvertraging')
    st.text('Informatie')
    st.text('Analyse')
    st.text('OLS regressie')
    st.text('')
    st.subheader('- Verschillende vluchten die zijn vertrokken van Schiphol')


with st.expander('', expanded=True):
    a1, a2 = st.columns(2)
    with a1: 
        st.header('Zurich Airport')
        st.image(zurich_img)
    with a2: 
        st.header('Schiphol Airport')
        st.image(schiphol_img)
