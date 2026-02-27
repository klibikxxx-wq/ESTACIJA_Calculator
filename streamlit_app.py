import streamlit as st
import numpy as np

st.set_page_config(page_title="ESTACIJA Saules & Akumulatoru ROI", page_icon="☀️")

# --- VIRSRAKSTS ---
st.image("New_logo1.png", width=200) 
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")
st.subheader("Biznesa klientu analīze (Bez PVN)")

# --- GALVENĀ IEVADES FORMA ---
with st.form("galvena_forma"):
    st.subheader("📊 1. Enerģijas dati")
    col1, col2 = st.columns(2)
    with col1:
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=9000)
    with col2:
        bill = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=1.0, value=1500.0)
    
    st.divider()
    
    st.subheader("🏦 2. Finansējuma dati (Kredīts)")
    col3, col4 = st.columns(2)
    with col3:
        # Procentu likme no 1.9% līdz 15%
        interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 5.9) / 100
    with col4:
        # Termiņš no 1 līdz 10 gadiem
        loan_years = st.select_slider("Kredīta termiņš (Gadi)", options=list(range(1, 11)), value=7)
    
    submit_button = st.form_submit_button("Aprēķināt pilnu atskaiti")

# --- SĀNU JOSLA: VALSTS ATBALSTS ---
st.sidebar.header("⚙️ Konfigurācija")
grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# --- LINEĀRĀ JAUDAS LOĢIKA ---
if usage <= 600:
    calc_solar = 6.0
else:
    # Lineārs pieaugums no 600kWh/6kW līdz 9000kWh/50kW
    calc_solar = 6.0 + (usage - 600) * (44 / 8400)

# Baterijas izmērs 
calc_battery = calc_solar * 2.0 

# DINAMISKĀS CENAS (Bez PVN)
if calc_solar < 20:
    sol_price_base, bat_price_base = 800, 350
elif calc_solar < 50:
    sol_price_base, bat_price_base = 750, 280
else:
    sol_price_base, bat_price_base = 650, 240

# Finanšu aprēķini
total_cost = (calc_solar * sol_price_base) + (calc_battery * bat_price_base)
grant_amount = total_cost * grant_pct
net_investment = total_cost - grant_amount

# KREDĪTA MAKSĀJUMS (PMT)
monthly_interest = interest_rate / 12
total_months = loan_years * 12
if interest_rate > 0 and net_investment > 0:
    monthly_loan = net_investment * (monthly_interest * (1 + monthly_interest)**total_months) / ((1 + monthly_interest)**total_months - 1)
else:
    monthly_loan = net_investment / (total_months if total_months > 0 else 1)

# IETAUPĪJUMS
elec_price_per_kwh = bill / usage if usage > 0 else 0
solar_savings_annual = (calc_solar * 1050) * (elec_price_per_kwh + 0.045)
battery_savings_annual = (calc_battery * 280 * 0.08 * 0.85)
total_savings_monthly = (solar_savings_annual + battery_savings_annual) / 12

payback_years = net_investment / (solar_savings_annual + battery_savings_annual) if (solar_savings_annual + battery_savings_annual) > 0 else 0
monthly_net_profit = total_savings_monthly - monthly_loan

# --- REZULTĀTU ATTĒLOŠANA ---
if submit_button or usage:
    st.divider()
    
    st.subheader("💡 Sistēmas un ROI kopsavilkums")
    
    # Tehniskie dati
    t1, t2, t3 = st.columns(3)
    t1.metric("Ieteicamā Saules Jauda", f"{calc_solar:.1f} kW")
    t2.metric("Ieteicamā Baterija", f"{calc_battery:.1f} kWh")
    t3.metric("Atmaksāšanās", f"{payback_years:.1f} Gadi")

    # Finanšu dati
    f1, f2, f3 = st.columns(3)
    f1.metric("Kopējā Investīcija", f"€{total_cost:,.0f}")
    f2.metric("Mēneša kredīts", f"€{monthly_loan:,.2f}")
    f3.metric("Mēneša peļņa (Cash-flow)", f"€{monthly_net_profit:,.2f}", delta=f"{monthly_net_profit:,.2f} €")

    # Papildus info
    st.write(f"**Valsts atbalsts ({int(grant_pct*100)}%): €{grant_amount:,.0f}** | **Neto investīcija: €{net_investment:,.0f}**")

    if monthly_net_profit > 0:
        st.success(f"✅ Projekts ir pašfinansējošs! Ietaupījums ir lielāks nekā bankas maksājums.")
    else:
        st.warning(f"⚠️ Ikmēneša maksājums pārsniedz tiešo ietaupījumu.")

    # Grafiks
    st.subheader("📈 Investīcijas atmaksas līkne")
    years_plot = np.arange(0, int(max(payback_years + 3, loan_years + 1)))
    cash_flow = [(total_savings_monthly * 12 * y) - net_investment for y in years_plot]
    st.area_chart(cash_flow)
    st.caption("Aprēķini veikti biznesa klientam bez PVN. Iekļauts ST tarifs 0.045 €/kWh un enerģijas arbitrāža.")