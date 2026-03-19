import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64
import statsmodels.formula.api as smf
from haversine import haversine

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
green = "#00cc96"
####################################################################################################
# dataframes
schedule = pd.read_csv(r'case3/schedule_airport.csv')
runways_geo = pd.read_csv(r'Zurich/Zurich_runway.csv')
gates_geo = pd.read_csv(r'Zurich/Zurich_gates.csv')
all_stations = pd.read_csv(r'airports-extended-clean.csv', sep=';', decimal=',')

airports = all_stations[all_stations['Type'] == 'airport']
airports = airports[['ICAO','Latitude','Longitude', 'Name', 'Country', 'Altitude']]

schedule = schedule.drop(columns=['DL1','IX1','DL2','IX2','Identifier'])
schedule['LSV'] = np.where(schedule['LSV'] == 'S', 'uitgaand', 'inkomend')
schedule['afkomst'] = np.where(schedule['LSV'] == 'inkomend', schedule['Org/Des'], 'LSZH')
schedule['bestemming'] = np.where(schedule['LSV'] == 'uitgaand', schedule['Org/Des'], 'LSZH')
schedule['andere_gate'] = schedule['TAR'] != schedule['GAT']

schedule['STD'] = pd.to_datetime(schedule['STD'], format='%d/%m/%Y')

schedule['ATA_ATD_ltc'] = pd.to_datetime(schedule['STD'].dt.strftime('%Y-%m-%d') + ' ' + schedule['ATA_ATD_ltc'].astype(str))
schedule['STA_STD_ltc'] = pd.to_datetime(schedule['STD'].dt.strftime('%Y-%m-%d') + ' ' + schedule['STA_STD_ltc'].astype(str))
schedule['vertraagd'] = (schedule['ATA_ATD_ltc'] - schedule['STA_STD_ltc']).dt.total_seconds() >= 0
schedule['hour']    = schedule['STA_STD_ltc'].dt.hour
schedule['weekday'] = schedule['STD'].dt.dayofweek
schedule['month']   = schedule['STD'].dt.month

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


schedule = pd.merge(schedule, airports, how='left' ,left_on='afkomst', right_on='ICAO')
schedule = pd.merge(schedule, airports, how='left' ,left_on='bestemming', right_on='ICAO')
schedule = schedule.drop(columns=['ICAO_x','ICAO_y'])
schedule = schedule.rename(columns={'Latitude_x':'lat_afkomst',
                                    'Longitude_x':'lon_afkomst',
                                    'Name_x':'naam_afkomst',
                                    'Country_x':'land_afkomst',
                                    'Latitude_y':'lat_bestemming',
                                    'Longitude_y':'lon_bestemming',
                                    'Name_y':'naam_bestemming',
                                    'Country_y':'land_bestemming',
                                    'Altitude_x':'Vliegveld_hoogte_afkomst',
                                    'Altitude_y':'Vliegveld_hoogte_bestemming',})

schedule['afstand_km'] = (haversine(
    schedule['lat_afkomst'],
    schedule['lon_afkomst'],
    schedule['lat_bestemming'],
    schedule['lon_bestemming']
).round()) / 1000
####################################################################################################
#Datum Slider
mindate = schedule['STD'].min().to_pydatetime()
maxdate = schedule['STD'].max().to_pydatetime()
st.sidebar.title('Settings')
periode = st.sidebar.slider(
    label='Selecteer periode',
    min_value=mindate, 
    max_value=maxdate,
    value=(mindate, maxdate)
)
schedule = schedule[
    (schedule['STD'] >= periode[0]) & 
    (schedule['STD'] <= periode[1])
]
####################################################################################################
groep_runway = schedule.groupby(['LSV','RWY'])['RWY'].count().reset_index(name='aantal_vluchten')
groep_runway = groep_runway.rename(columns={'RWY': 'number'})
runwaynumber_count = pd.merge(groep_runway, runways_geo, on='number')

groep_gate = schedule.groupby('GAT')['GAT'].count().reset_index(name='aantal_vluchten')
groep_gate = groep_gate.rename(columns={'GAT': 'gate'})
gate_count = groep_gate = pd.merge(groep_gate, gates_geo, on='gate')

groep_vluchten = schedule.groupby(['LSV','Org/Des'])['Org/Des'].count().reset_index(name='aantal')
groep_vluchten = pd.merge(groep_vluchten, airports, left_on='Org/Des', right_on='ICAO')

aantal_vluchten = schedule['FLT'].count()
gem_vertraging = schedule['vertraging_min'].mean().round(2)
max_vertraging = schedule['vertraging_min'].max().round(2)
aantal_vertragingen = schedule['vertraging_min'].count()
aantal_vertragingen_prc = (aantal_vertragingen / aantal_vluchten * 100).round(1)
gem_vervroeging = schedule['vervroeging_min'].mean().round(2)
gem_afstand = schedule['afstand_km'].mean().round(1)

dag_gemiddelde_vluchten = schedule.groupby('STD')['FLT'].count().reset_index(name='aantal')
dag_gemiddelde_vluchten = dag_gemiddelde_vluchten['aantal'].mean().astype(int)

groep_vertraging = schedule.groupby(['LSV', 'andere_gate', 'vertraagd'])['vertraagd'].count().reset_index(name='aantal').sort_values('aantal')
groep_vertraging['vertraagd_label'] = groep_vertraging['vertraagd'].map({True: 'Vertraagd', False: 'Op tijd'})
groep_vertraging['gate_label'] = groep_vertraging['andere_gate'].map({True: 'Andere Gate', False: 'Zelfde Gate'})

groep_gate_vertraging = schedule.groupby('GAT')['vertraging_min'].mean().reset_index(name='gemiddelde_vertraging').round().drop(axis=1, index=0).fillna(1)
groep_gate_vertraging = pd.merge(groep_gate_vertraging, gates_geo, left_on='GAT', right_on='gate').drop(axis=0, columns='GAT')

groep_vluchten_vertraagd = schedule.groupby(['LSV','Org/Des'])['vertraging_min'].mean().round().reset_index(name='gemiddelde_vertraging').fillna(1)
groep_vluchten_vertraagd = pd.merge(groep_vluchten_vertraagd, airports, left_on='Org/Des', right_on='ICAO')
groep_vluchten_vertraagd = groep_vluchten_vertraagd[groep_vluchten_vertraagd['LSV'] == 'inkomend']

groep_vertraging_rwy_prc = schedule.groupby(['vertraagd', 'RWY'])['RWY'].count().rename('aantal').reset_index()

####################################################################################################
fig = px.line()
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

map_landingsbaan_data = px.scatter_map(
    runwaynumber_count,
    lon='lon',
    lat='lat',
    color='LSV',
    color_discrete_map={'inkomend': blue, 'uitgaand': red}, 
    size='aantal_vluchten',
    size_max=100,
    hover_data={'lon': False, 'lat': False, 'aantal_vluchten': True, 'LSV': True, 'number':True},
    zoom=12,
    opacity=0.5,
    title='Vluchtdata van Zurich Airport'
)
map_landingsbaan_data.add_trace(go.Scattermap(
    lat=gates_geo['lat'],
    lon=gates_geo['lon'],
    mode='markers',
    marker=dict(
        size=10, 
        color="#cb8325"
    ),
    name='Gates', 
    text=gates_geo['gate'],
    opacity=0.3,
    hoverinfo='text'
))
map_landingsbaan_data.add_trace(go.Scattermap(
    lat=runways_geo['lat'],
    lon=runways_geo['lon'],
    mode='markers+text',
    text=runways_geo['number'],
    texttemplate='%{text}', 
    textposition='top center',
    textfont=dict(color='black', size=16),
    marker=dict(size=0, color='white'),
    hoverinfo='skip',
    name='landingsbaan nummers'
))
map_landingsbaan_data.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":0},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

map_gate_data = px.scatter_map(gate_count,
                               lon='lon',
                               lat='lat',
                               color='aantal_vluchten',
                               color_continuous_scale=[blue, red], 
                               hover_data={'lon': False, 'lat': False, 'aantal_vluchten': True, 'gate': True},
                               zoom=13,
                               title='Vluchtdata van Zurich Airport',
                               size='aantal_vluchten',
                               size_max=20,
                               opacity=0.9
)
map_gate_data.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":0},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

q99 = schedule['vertraging_min'].quantile(0.99)
vertraging = px.histogram(
    data_frame=schedule,
    x='vertraging_min',
    range_x=[0, q99],
    title='Frequentie van vertragingen'
)
vertraging.update_traces(
    xbins=dict(
        start=0,
        end=q99,
        size=1,),
    marker_line_width=1,
    marker_line_color="#6CBEFE",
)
vertraging.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

afstand = px.histogram(
    data_frame=schedule,
    x='afstand_km',
    title='Frequentie vluchtafstand',
    nbins=100
)
afstand.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_vliegvelden = px.scatter_map(groep_vluchten,
                                 lat='Latitude',
                                 lon='Longitude',
                                 color='LSV',
                                 color_discrete_map={'inkomend':red, 'uitgaand':blue},
                                 size='aantal',
                                 size_max=20,
                                 opacity=0.5,
                                 zoom=1,
                                 hover_data={'Latitude': False, 'Longitude': False,  'aantal': True, 'Name': True},
                                 )
fig_vliegvelden.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

map_gate_vertraging = px.scatter_map(groep_gate_vertraging,
                                     lon='lon',
                                     lat='lat',
                                     color='gemiddelde_vertraging',
                                     color_continuous_scale=[blue, red], 
                                     hover_data={'lon': False, 'lat': False, 'gemiddelde_vertraging': True, 'gate': True},
                                     zoom=13,
                                     title='Gemiddelde vertraging per gate in minuten',
                                     size='gemiddelde_vertraging',
                                     size_max=20,
                                     opacity=0.9
)
map_gate_vertraging.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":0},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_groep_vluchten_vertraagd = px.scatter_map(groep_vluchten_vertraagd,
                                              lon='Longitude',
                                              lat='Latitude',
                                              color='gemiddelde_vertraging',
                                              color_continuous_scale=[blue, red], 
                                              hover_data={'Longitude': False, 'Latitude': False, 'gemiddelde_vertraging': True, 'Name': True},
                                              zoom=1,
                                              title='Gemiddelde vertraging per vliegveld in minuten',
                                              size='gemiddelde_vertraging',
                                              size_max=20,
                                              opacity=0.9
)
fig_groep_vluchten_vertraagd.update_layout(font=dict(size=18), margin={"r":0,"t":25,"l":0,"b":0},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_Sunburst = px.sunburst(groep_vertraging, 
                           path=['LSV', 'gate_label', 'vertraagd_label'], 
                           values='aantal',
                           color='vertraagd_label',
                           color_discrete_map={'Vertraagd': red, 'Op tijd': green},
                           color_discrete_sequence=[blue],
                           hover_data={'aantal': True}
)
fig_Sunburst.update_traces(textinfo="label+percent parent")
fig_Sunburst.update_layout(font=dict(size=18), margin={"r":0,"t":0,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

fig_runwaynumber_count = px.bar(runwaynumber_count, 
                                x='number', 
                                y='aantal_vluchten', 
                                color='LSV',
                                color_discrete_sequence=[blue, red],
                                barmode='group',
                                title="Landingsbaan aantallen (in LOG)",
                                log_y=True,
                                labels={'aantal_vluchten': 'Aantal vluchten'},
)
fig_runwaynumber_count.update_xaxes(type='category', title_text='')
fig_runwaynumber_count.update_layout(font=dict(size=18), margin={"r":0,"t":50,"l":0,"b":50}, paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5,
        title_text=''
    )
)

corolatie = schedule.corr(numeric_only=True)
corolatie = corolatie[['vertraagd']]
corolatie = corolatie.drop(['vertraagd','vertraging_sec','vertraging_min','vervroeging_sec','vervroeging_min','lat_afkomst','lon_afkomst','lat_bestemming','lon_bestemming','Vliegveld_hoogte_bestemming'], axis=0)
corolatie = corolatie.sort_values(by='vertraagd', ascending=False)

fig_corolatie = px.imshow(corolatie, 
                text_auto=True, 
                color_continuous_scale=[blue,'white',red],
                aspect="auto",
                zmin=-1,
                zmax=1)
fig_corolatie.update_layout(font=dict(size=18), margin={"r":0,"t":0,"l":0,"b":25},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)') 

fig_vertraging_rwy = px.bar(
    groep_vertraging_rwy_prc, 
    x='RWY',
    y='aantal',
    color='vertraagd',
    barmode='relative',
    color_discrete_sequence=[red, blue],
)
fig_vertraging_rwy.update_xaxes(type='category', title_text='')
fig_vertraging_rwy.update_layout(barnorm='percent', yaxis_title='Percentage vertraging', xaxis_title='Startbaan (RWY)',
                  font=dict(size=18), margin={"r":0,"t":0,"l":0,"b":50}, paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')

vertraging_dag = schedule.groupby('weekday')['vertraging_min'].mean().reset_index()
vertraging_dag['dag'] = vertraging_dag['weekday'].map(
    {0:'Ma',1:'Di',2:'Wo',3:'Do',4:'Vr',5:'Za',6:'Zo'})
fig_dag = px.bar(vertraging_dag, x='dag', y='vertraging_min',
    title='Gemiddelde vertraging per dag van de week',
    labels={'dag': 'Dag', 'vertraging_min': 'Gem. vertraging (min)'},
    color='vertraging_min', color_continuous_scale=[blue, red])
fig_dag.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=16))

vertraging_uur = schedule.groupby('hour')['vertraging_min'].mean().reset_index()
fig_uur = px.bar(vertraging_uur, x='hour', y='vertraging_min',
    title='Gemiddelde vertraging per uur van de dag',
    labels={'hour': 'Uur', 'vertraging_min': 'Gem. vertraging (min)'},
    color='vertraging_min', color_continuous_scale=[blue, red])
fig_uur.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=16))

####################################################################################################
# Streamlit

st.title('Zurich Airport informatie')
st.set_page_config(layout='wide', page_title='Layout')

kaart_opties = {
    'Vluchten per landingsbaan': map_landingsbaan_data,
    'Vluchten per vliegveld' : fig_vliegvelden,
    'Gemiddelde vertraging per vliegveld' : fig_groep_vluchten_vertraagd,
    'Aantal vluchten per gate': map_gate_data,
    'Gemiddelde vertraging per Gate' : map_gate_vertraging,
}
gekozen_label = st.sidebar.selectbox('kies data voor kaart', list(kaart_opties.keys()))
gekozen_kaart_string = kaart_opties[gekozen_label]

# a zijn de grafieken
a1, a2, a3 = st.columns(3)
with a1: 
    st.plotly_chart(vertraging, height=300)

with a2:
     st.plotly_chart(afstand, height=300)

with a3:
     st.plotly_chart(fig_runwaynumber_count, height=300)

# B is de kaart links en rechts wat waardes
b1, b2 = st.columns([4,1])

with b1:
    st.plotly_chart(gekozen_kaart_string, height=430)

with b2:
    with st.expander('Info 📊', expanded=True): 
        st.text(f'Totaal aantal vluchten: {aantal_vluchten}')
        st.text(f'Aantal vertragingen: {aantal_vertragingen} ({aantal_vertragingen_prc}%)')
        st.text(f'Gemiddelde vertraging: {gem_vertraging} min')
        st.text(f'Maximale vertraging: {max_vertraging} min')
        st.text(f'Gemiddelde vluchtafstand: {gem_afstand} km')
        st.text(f'Gemiddelde vluchten per dag: {dag_gemiddelde_vluchten}')

st.divider()
st.title('Zurich Airport vertraging analyse')


c1, c2, c3= st.columns(3)
with c1: 
    with st.expander('Vertragingen bij Gate-wijzigingen', expanded=True): st.plotly_chart(fig_Sunburst)
with c2: 
    with st.expander("Correlatie met 'vertraagd'", expanded=True): st.plotly_chart(fig_corolatie)
with c3: 
    with st.expander('Procent vertragingen per startbaan', expanded=True): st.plotly_chart(fig_vertraging_rwy)

with st.expander('tijd analyse', expanded=True):
    d1, d2 = st.columns(2)
    with d1: st.plotly_chart(fig_uur, use_container_width=True)
    with d2: st.plotly_chart(fig_dag, use_container_width=True)

####################################################################################################
####################################################################################################
# Liniare regressie
 
#groepeer op route + uur
route_df = schedule.groupby(
    ['Org/Des', 'hour', 'weekday', 'RWC']
).agg(
    vertraging_min = ('vertraging_min', 'mean'),
    afstand_km     = ('afstand_km', 'first'),
    month          = ('month', 'first'),
).reset_index().dropna()
 
route_df = route_df[route_df['vertraging_min'] <= 60]
route_df = route_df[route_df['vertraging_min'] >= -30]
 
 
#smf.ols model
formula = """vertraging_min ~ afstand_km
                             + hour
                             + weekday
                             + month
                             + C(RWC)
                             + C(Q('Org/Des'))"""
 
model = smf.ols(formula=formula, data=route_df).fit()


 
#Coëfficiënten tabel

hoofdvars = ['Intercept', 'afstand_km', 'hour', 'weekday', 'month']
coef_df = pd.DataFrame({
    'Variabele':   model.params.index,
    'Coëfficiënt': model.params.values.round(4),
    'p-waarde':    model.pvalues.values.round(4),
}).reset_index(drop=True)
coef_df['Sig.'] = coef_df['p-waarde'].apply(
    lambda p: '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else '—'))
)
coef_hoofd = coef_df[coef_df['Variabele'].isin(hoofdvars)]

 
#Scatter voorspeld vs werkelijk
route_df['voorspeld'] = model.predict(route_df)
fig_pred = px.scatter(
    route_df,
    x='vertraging_min',
    y='voorspeld',
    trendline='ols',
    trendline_color_override=red,
    labels={
        'vertraging_min': 'Werkelijke vertraging (min)',
        'voorspeld':      'Voorspelde vertraging (min)'
    },
    title='Voorspeld vs Werkelijk'
)
fig_pred.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(size=16))


# Streamlit voor Liniare regressie
st.divider()
st.title('OLS Regressiemodel - Vliegtuigvertraging')

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.header("R²")
    st.subheader(f"{model.rsquared:.4f}")
with col2:
    st.header("Adj. R²")
    st.subheader(f"{model.rsquared_adj:.4f}")
with col3:
    st.header("F-stat")
    st.subheader(f"{model.fvalue:,.4f}")
with col4:
    st.header("Obs.")
    st.subheader(f"{int(model.nobs):,}")


st.plotly_chart(fig_pred, use_container_width=True)
st.subheader("Coëfficiënten (hoofdvariabelen)")
st.dataframe(coef_hoofd, use_container_width=True)

with st.expander("Volledige OLS samenvatting"):
    st.code(str(model.summary()))
 
st.divider()
