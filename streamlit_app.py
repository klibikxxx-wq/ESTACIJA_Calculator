import streamlit as st
import numpy as np

st.set_page_config(page_title="ESTACIJA Saules & Akumulatoru ROI", page_icon="☀️")

# --- VIRSRAKSTS ---
st.image("New_logo1.png", width=300)
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")
st.subheader("Biznesa klientu analīze (Bez PVN)")

# --- GALVENĀ IEVADES FORMA ---
with st.form("galvena_forma"):
    st.subheader("📊 1. Enerģijas dati")
    st.write("Ievadiet vismaz vienu no rādītājiem:")
    col1, col2 = st.columns(2)
    with col1:
        # Sākumā tukšs lauks
        usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None, step=100.0)
    with col2:
        # Sākumā tukšs lauks
        bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None, step=50.0)
    
    st.divider()
    
    st.subheader("🏦 2. Finansējuma dati (Kredīts)")
    col3, col4 = st.columns(2)
    with col3:
        interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 5.9) / 100
    with col4:
        loan_years = st.select_slider("Kredīta termiņš (Gadi)", options=list(range(1, 11)), value=7)
    
    submit_button = st.form_submit_button("Aprēķināt pilnu atskaiti")

# --- DATU APSTRĀDE (Ja aizpildīts tikai viens) ---
usage = 0.0
bill = 0.0

if usage_in is not None and bill_in is not None:
    usage = usage_in
    bill = bill_in
elif usage_in is not None:
    usage = usage_in
    bill = usage * 0.16  # Pieņemtā vidējā cena uzņēmumiem 2026. gadā
elif bill_in is not None:
    bill = bill_in
    usage = bill / 0.16

# --- APRĒĶINI (Tikai ja ir dati) ---
if usage > 0:
    # SĀNU JOSLA: VALSTS ATBALSTS
    st.sidebar.header("⚙️ Konfigurācija")
    grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

    # Lineārā jaudas loģika
    if usage <= 600:
        calc_solar = 6.0
    else:
        calc_solar = 6.0 + (usage - 600) * (44 / 8400)

    calc_battery = calc_solar * 2.0 

    # Cenu loģika
    if calc_solar < 20:
        sol_price_base, bat_price_base = 800, 350
    elif calc_solar < 50:
        sol_price_base, bat_price_base = 750, 280
    else:
        sol_price_base, bat_price_base = 650, 240

    total_cost = (calc_solar * sol_price_base) + (calc_battery * bat_price_base)
    grant_amount = total_cost * grant_pct
    net_investment = total_cost - grant_amount

    # Kredīta PMT
    monthly_interest = interest_rate / 12
    total_months = loan_years * 12
    if interest_rate > 0 and net_investment > 0:
        monthly_loan = net_investment * (monthly_interest * (1 + monthly_interest)**total_months) / ((1 + monthly_interest)**total_months - 1)
    else:
        monthly_loan = net_investment / (total_months if total_months > 0 else 1)

    # Ietaupījums
    elec_price_per_kwh = bill / usage if usage > 0 else 0.16
    solar_savings_annual = (calc_solar * 1050) * (elec_price_per_kwh + 0.045)
    battery_savings_annual = (calc_battery * 280 * 0.08 * 0.85)
    total_savings_monthly = (solar_savings_annual + battery_savings_annual) / 12

    payback_years = net_investment / (solar_savings_annual + battery_savings_annual) if (solar_savings_annual + battery_savings_annual) > 0 else 0
    monthly_net_profit = total_savings_monthly - monthly_loan

    # --- REZULTĀTI ---
    st.divider()
    st.subheader("💡 Sistēmas un ROI kopsavilkums")
    
    t1, t2, t3 = st.columns(3)
    t1.metric("Ieteicamā Saules Jauda", f"{calc_solar:.1f} kW")
    t2.metric("Ieteicamā Baterija", f"{calc_battery:.1f} kWh")
    t3.metric("Atmaksāšanās", f"{payback_years:.1f} Gadi")

    f1, f2, f3 = st.columns(3)
    f1.metric("Kopējā Investīcija", f"€{total_cost:,.0f}")
    f2.metric("Mēneša kredīts", f"€{monthly_loan:,.2f}")
    f3.metric("Mēneša peļņa (Cash-flow)", f"€{monthly_net_profit:,.2f}", delta=f"{monthly_net_profit:,.2f} €")

    st.write(f"**Valsts atbalsts ({int(grant_pct*100)}%): €{grant_amount:,.0f}** | **Neto investīcija: €{net_investment:,.0f}**")

    # Grafiks
    years_plot = np.arange(0, int(max(payback_years + 3, loan_years + 1)))
    cash_flow = [(total_savings_monthly * 12 * y) - net_investment for y in years_plot]
    st.area_chart(cash_flow)
    
    if usage_in is None or bill_in is None:
        st.caption("ℹ️ Aprēķins veikts, balstoties uz vidējo tirgus cenu 0.16 €/kWh, jo viens no datu laukiem bija tukšs.")
else:
    st.info("👋 Sveicināti! Lai sāktu aprēķinu, lūdzu, ievadiet klienta mēneša patēriņu vai vidējo rēķina summu.")