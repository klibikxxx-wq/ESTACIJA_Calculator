import streamlit as st

st.set_page_config(page_title="Saules & Akumulatoru Optimizētājs", page_icon="☀️")

# --- STILS UN VIRSRAKSTS ---
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")
st.write("Ievadiet klienta datus, lai aprēķinātu tehniski un ekonomiski pamatotāko sistēmu.")

# --- IEVADES FORMA (Pirmā lieta, ko redz telefonā) ---
with st.form("ievades_forma"):
    st.subheader("📊 Klienta Enerģijas Dati")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=19000, help="Vidējais mēneša patēriņš gadā")
    with col_input2:
        bill = st.number_input("Mēneša rēķins (€)", min_value=1, value=3100, help="Vidējais rēķins ieskaitot PVN un ST")
    
    submit_button = st.form_submit_button("Aprēķināt optimālo risinājumu")

# --- PAPILDUS IESTATĪJUMI SĀNU JOSLĀ ---
st.sidebar.header("⚙️ Finanšu Iestatījumi")
grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100
interest = st.sidebar.slider("Kredīta procenti (%)", 0.0, 10.0, 5.0) / 100
years = st.sidebar.selectbox("Kredīta termiņš (Gadi)", [5, 7, 10, 15], index=1)

# --- APRĒĶINU LOĢIKA (Tikai ja poga ir nospiesta vai dati jau ir) ---
if submit_button or usage:
    # 1. Optimizācija (40% saules likums, 1.5x akumulatora attiecība)
    calc_solar = (usage * 12 * 0.4) / 1000
    calc_battery = calc_solar * 1.5

    # 2. Dinamiskās cenas (Ekonomija uz apjomu)
    sol_price = 1100 if calc_solar < 15 else (900 if calc_solar < 40 else 750)
    bat_price = 500 if calc_battery < 20 else (380 if calc_battery < 100 else 245)

    total_cost = (calc_solar * sol_price) + (calc_battery * bat_price)
    net_investment = total_cost * (1 - grant_pct)

    # 3. Ietaupījuma loģika
    # Ietaupījums = Saražotā enerģija * (Elektrības cena + ST mainīgā daļa 0.045 EUR)
    solar_savings = (calc_solar * 1000) * ((bill/usage) + 0.045)
    # Akumulatora peļņa no biržas cenas starpības
    battery_savings = (calc_battery * 280 * 0.08 * 0.85)
    total_annual_savings = solar_savings + battery_savings
    payback = net_investment / total_annual_savings

    # --- REZULTĀTU ATTĒLOŠANA ---
    st.divider()
    st.subheader("💡 Rekomendējamā Sistēma")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Saules jauda", f"{calc_solar:.1f} kW")
    m2.metric("Akumulatora ietilpība", f"{calc_battery:.1f} kWh")
    m3.metric("Atmaksāšanās laiks", f"{payback:.1f} Gadi")

    st.success(f"Kopējās investīcijas: {total_cost:,.2f} € (pēc atbalsta: {net_investment:,.2f} €)")

    # --- GRAFIKS ---
    st.subheader("📈 Ietaupījuma prognoze")
    st.info(f"Prognozētais ietaupījums mēnesī: {total_annual_savings/12:,.2f} €")
    
    # Neliels vizuāls grafiks atmaksas gaitai
    yearly_data = {f"{i}. gads": total_annual_savings * i for i in range(1, int(payback + 3))}
    st.area_chart(yearly_data)

    st.caption("Aprēķinā iekļauta Sadales Tīkla jaudas maksas ekonomija (€0.045/kWh) un akumulatora cenas arbitrāža.")
