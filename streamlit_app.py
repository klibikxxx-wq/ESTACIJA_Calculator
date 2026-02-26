import streamlit as st

st.set_page_config(page_title="Saules & Akumulatoru Optimizētājs", page_icon="☀️")
st.logo("New_logo1.png", size="large")

st.title("☀️ Saules un Akumulatoru ROI Kalkulators")

# --- IEVADES FORMA ---
with st.form("ievades_forma"):
    st.subheader("📊 Klienta Enerģijas Dati")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=1500)
    with col_input2:
        bill = st.number_input("Mēneša rēķins (€)", min_value=1, value=300)
    
    submit_button = st.form_submit_button("Aprēķināt optimālo risinājumu")

# --- SĀNU JOSLA IESTATĪJUMIEM ---
st.sidebar.header("⚙️ Finanšu Iestatījumi")
grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100
interest = st.sidebar.slider("Kredīta procenti (%)", 0.0, 10.0, 2.0) / 100
years = st.sidebar.selectbox("Kredīta termiņš (Gadi)", [2, 3, 4, 5], index=1)

# --- SMART OPTIMIZĀCIJAS LOĢIKA ---
if usage <= 2000:
    # Mājsaimniecības profils (ap 1500 kWh -> 14kW)
    calc_solar = 14.0
    calc_battery = 10.0 # Standarta mājas baterija
    sol_price = 850     # Cena par kW mājsaimniecībām
    bat_price = 450     # Cena par kWh mājsaimniecībām
elif usage >= 8000:
    # Industriālais profils (ap 9000 kWh -> 50kW)
    calc_solar = 50.0
    calc_battery = 100.0 # Optimizēta industriālā baterija
    sol_price = 700      # Industriālā cena (tavs 35k/50kW vidējais)
    bat_price = 245      # Industriālā baterijas cena
else:
    # Vidējais segments (Lineāra pāreja starp 14kW un 50kW)
    calc_solar = 14 + (usage - 2000) * (36 / 6000)
    calc_battery = calc_solar * 1.5
    sol_price = 800
    bat_price = 350

# --- APRĒĶINI ---
total_cost = (calc_solar * sol_price) + (calc_battery * bat_price)
net_investment = total_cost * (1 - grant_pct)

# Ietaupījums: Saules raža (1000h) + ST tarifs + Baterijas arbitrāža
solar_savings = (calc_solar * 1000) * ((bill/usage) + 0.045)
battery_savings = (calc_battery * 280 * 0.08 * 0.85)
total_annual_savings = solar_savings + battery_savings
payback = net_investment / total_annual_savings

# --- REZULTĀTI ---
if submit_button or usage:
    st.divider()
    st.subheader("💡 Rekomendējamais risinājums")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Saules sistēma", f"{calc_solar:.1f} kW")
    col2.metric("Akumulators", f"{calc_battery:.1f} kWh")
    col3.metric("Atmaksāšanās", f"{payback:.1f} Gadi")

    # Finanšu kopsavilkums
    st.write(f"### Kopējās izmaksas: **{total_cost:,.0f} €**")
    st.write(f"Valsts atbalsts ({int(grant_pct*100)}%): **-{total_cost*grant_pct:,.0f} €**")
    st.success(f"Tava gala investīcija: **{net_investment:,.0f} €**")

    # Ietaupījuma sadalījums
    st.info(f"Prognozētais ietaupījums: **{total_annual_savings/12:,.2f} € / mēnesī**")
    
    # Grafiks (Atmaksas līkne)
    years_to_show = int(payback + 4)
    chart_data = {f"{i}. gads": (total_annual_savings * i) - net_investment for i in range(years_to_show)}
    st.area_chart(chart_data)
    st.caption("Grafiks attēlo tīro peļņu pēc investīcijas segšanas.")
