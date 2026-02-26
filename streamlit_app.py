import streamlit as st
import numpy as np

st.set_page_config(page_title="Saules & Akumulatoru ROI", page_icon="☀️")

# --- LOGO UN VIRSRAKSTS ---
st.logo("New_logo1.png", size="large")
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")

# --- IEVADES FORMA ---
with st.form("ievades_forma"):
    st.subheader("📊 Klienta Enerģijas Dati")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=1500)
    with col_input2:
        bill = st.number_input("Mēneša rēķins (€ ar PVN)", min_value=1.0, value=250)
    
    submit_button = st.form_submit_button("Aprēķināt risinājumu")

# --- SĀNU JOSLA: FINANSES ---
st.sidebar.header("⚙️ Finanšu Iestatījumi")
grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100
interest_rate = st.sidebar.slider("Kredīta procenti (%)", 0.0, 15.0, 2) / 100
loan_years = st.sidebar.selectbox("Kredīta termiņš (Gadi)", [2, 3, 4, 5], index=1)

# --- LINEĀRĀ OPTIMIZĀCIJAS LOĢIKA ---
# Aprēķinām saules jaudu lineāri: 1500kWh -> 14kW; 9000kWh -> 50kW.
# Formula: jauda = 14 + (patēriņš - 1500) * ( (50-14) / (9000-1500) )
calc_solar = 14 + (max(0, usage - 1500) * (36 / 7500))
calc_battery = calc_solar * 2.0  # Vidēji 2kWh baterija uz 1kW saules industriāliem

# Cenu slīde (lētāk, ja sistēma lielāka)
if calc_solar < 20:
    sol_price, bat_price = 750, 350
elif calc_solar < 50:
    sol_price, bat_price = 700, 300
else:
    sol_price, bat_price = 650, 230 # Tava industriālā cena

total_cost = (calc_solar * sol_price) + (calc_battery * bat_price)
net_investment = total_cost * (1 - grant_pct)

# KREDĪTA APRĒĶINS (PMT formula)
monthly_interest = interest_rate / 12
total_months = loan_years * 12
if interest_rate > 0:
    monthly_loan = net_investment * (monthly_interest * (1 + monthly_interest)**total_months) / ((1 + monthly_interest)**total_months - 1)
else:
    monthly_loan = net_investment / total_months

# IETAUPĪJUMA APRĒĶINS
# 1. Tiešais ietaupījums (pašpatēriņš + ST sadale)
elec_price_per_kwh = bill / usage
solar_savings_annual = (calc_solar * 1050) * (elec_price_per_kwh + 0.045)
# 2. Baterijas arbitrāža (280 cikli, 0.08 starpība, 85% efektivitāte)
battery_savings_annual = (calc_battery * 280 * 0.08 * 0.85)
total_savings_monthly = (solar_savings_annual + battery_savings_annual) / 12

# ROI un ATM_LAIKS
payback_years = net_investment / (solar_savings_annual + battery_savings_annual)
monthly_net_profit = total_savings_monthly - monthly_loan

# --- REZULTĀTU ATTĒLOŠANA ---
if submit_button or usage:
    st.divider()
    
    # 1. Rindā galvenie tehniskie dati
    c1, c2, c3 = st.columns(3)
    c1.metric("Optimālā Saules Jauda", f"{calc_solar:.1f} kW")
    c2.metric("Optimālā Baterija", f"{calc_battery:.1f} kWh")
    c3.metric("Atmaksāšanās", f"{payback_years:.1f} Gadi")

    # 2. Rindā finanšu dati
    f1, f2, f3 = st.columns(3)
    f1.metric("Kopējā Investīcija", f"€{total_cost:,.0f}")
    f2.metric("Ikmēneša maksājums", f"€{monthly_loan:,.2f}")
    f3.metric("Tīrā peļņa mēnesī", f"€{monthly_net_profit:,.2f}", delta=f"{monthly_net_profit:,.2f}")

    st.write(f"**Gala investīcija pēc valsts atbalsta: €{net_investment:,.0f}**")

    # Paskaidrojums par naudas plūsmu
    if monthly_net_profit > 0:
        st.success(f"✅ Sistēma sevi atpelna no pirmā mēneša! Ietaupījums ir par {monthly_net_profit:.2f} € lielāks nekā kredīta maksājums.")
    else:
        st.warning(f"⚠️ Ikmēneša kredīta maksājums pārsniedz tiešo ietaupījumu par {abs(monthly_net_profit):.2f} €. Sistēma atmaksāsies ilgtermiņā.")

    # Grafiks: Kumulatīvā naudas plūsma
    st.subheader("📈 Investīcijas atmaksas grafiks")
    years_plot = np.arange(0, int(payback_years + 5))
    cash_flow = [(total_savings_monthly * 12 * y) - net_investment for y in years_plot]
    st.line_chart(cash_flow)
    st.caption("Grafiks parāda laiku (gados), kad ietaupījums pilnībā nosedz investīciju.")
