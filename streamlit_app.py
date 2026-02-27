import streamlit as st
import numpy as np

st.set_page_config(page_title="ESTACIJA Saules & Akumulatoru ROI", page_icon="☀️")

# --- LOGO UN VIRSRAKSTS ---
# Ja tev ir logo fails, atkomentē nākamo rindu:
st.image("New_logo1.png", width=200) 
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")
st.subheader("Tikai juridiskām personām (Biznesa klientiem)")

# --- IEVADES FORMA ---
with st.form("ievades_forma"):
    st.subheader("📊 Enerģijas dati")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        # Sākuma vērtība 9000 kWh (biznesa piemērs)
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=9000)
    with col_input2:
        # Rēķins bez PVN
        bill = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=1.0, value=1500.0)
    
    submit_button = st.form_submit_button("Aprēķināt risinājumu")

# --- SĀNU JOSLA: FINANSES ---
st.sidebar.header("⚙️ Finanšu iestatījumi")
grant_pct = st.sidebar.slider("Valsts atbalsts uzņēmumam (%)", 0, 50, 30) / 100
interest_rate = st.sidebar.slider("Kredīta procenti (%)", 0.0, 15.0, 5.9) / 100
loan_years = st.sidebar.selectbox("Kredīta termiņš (Gadi)", [5, 7, 10, 15], index=1)

# --- LINEĀRĀ OPTIMIZĀCIJAS LOĢIKA ---
# Sākumpunkts: 600 kWh -> 6 kW
# Punkts B: 9000 kWh -> 50 kW
if usage <= 600:
    calc_solar = 6.0
else:
    # Lineārs pieaugums bez griestiem (44kW pieaugums uz 8400kWh starpību)
    calc_solar = 6.0 + (usage - 600) * (44 / 8400)

# Baterijas izmērs (Industriālais standarts 1kW saules : 2kWh baterija vai pēc tavas izvēles)
calc_battery = calc_solar * 2.0 

# Bāzes cenas bez PVN (Dinamiskas atkarībā no jaudas)
if calc_solar < 20:
    sol_price_base, bat_price_base = 800, 350
elif calc_solar < 50:
    sol_price_base, bat_price_base = 700, 280
else:
    # Industriālās cenas (Tavs piemērs: 50kW ap 35k un 208kWh ap 50k)
    sol_price_base, bat_price_base = 650, 240

# Kopējās izmaksas (Biznesam viss bez PVN)
total_cost = (calc_solar * sol_price_base) + (calc_battery * bat_price_base)

# Atbalsta piemērošana (% no kopējās summas)
grant_amount = total_cost * grant_pct
net_investment = total_cost - grant_amount

# KREDĪTA APRĒĶINS (PMT formula)
monthly_interest = interest_rate / 12
total_months = loan_years * 12
if interest_rate > 0 and net_investment > 0:
    monthly_loan = net_investment * (monthly_interest * (1 + monthly_interest)**total_months) / ((1 + monthly_interest)**total_months - 1)
else:
    monthly_loan = net_investment / total_months if total_months > 0 else 0

# IETAUPĪJUMA APRĒĶINS
elec_price_per_kwh = bill / usage if usage > 0 else 0
# 1050h saules raža + Sadales Tīkla ietaupījums 0.045 EUR/kWh
solar_savings_annual = (calc_solar * 1050) * (elec_price_per_kwh + 0.045)
# Baterijas arbitrāža
battery_savings_annual = (calc_battery * 280 * 0.08 * 0.85)
total_savings_monthly = (solar_savings_annual + battery_savings_annual) / 12

# ROI
payback_years = net_investment / (solar_savings_annual + battery_savings_annual) if (solar_savings_annual + battery_savings_annual) > 0 else 0
monthly_net_profit = total_savings_monthly - monthly_loan

# --- REZULTĀTU ATTĒLOŠANA ---
if submit_button or usage:
    st.divider()
    
    st.subheader("📊 Optimizētais biznesa risinājums")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Saules Jauda", f"{calc_solar:.1f} kW")
    c2.metric("Baterija", f"{calc_battery:.1f} kWh")
    c3.metric("Atmaksāšanās", f"{payback_years:.1f} Gadi")

    f1, f2, f3 = st.columns(3)
    f1.metric("Investīcija (€)", f"{total_cost:,.0f}")
    f2.metric("Mēneša kredīts", f"€{monthly_loan:,.2f}")
    f3.metric("Mēneša peļņa", f"€{monthly_net_profit:,.2f}", delta=f"{monthly_net_profit:,.2f} €/mēn")

    st.write(f"**Valsts atbalsts ({int(grant_pct*100)}%): €{grant_amount:,.0f}** | **Neto investīcija: €{net_investment:,.0f}**")

    if monthly_net_profit > 0:
        st.success(f"✅ Projekts sevi pilnībā finansē! Ietaupījums pārsniedz kredīta maksājumu par {monthly_net_profit:.2f} € mēnesī.")
    else:
        st.info(f"ℹ️ Ikmēneša ietaupījums sedz { (total_savings_monthly/monthly_loan)*100 if monthly_loan > 0 else 0:.0f}% no kredīta maksājuma.")

    # Grafiks
    st.subheader("📈 Investīcijas atmaksas prognoze (Gados)")
    years_plot = np.arange(0, int(max(payback_years + 5, 5)))
    cash_flow = [(total_savings_monthly * 12 * y) - net_investment for y in years_plot]
    st.area_chart(cash_flow)
    st.caption("Visas cenas un aprēķini ir norādīti bez PVN.")
