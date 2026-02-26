import streamlit as st
import numpy as np

st.set_page_config(page_title="Saules & Akumulatoru ROI", page_icon="☀️")

# --- LOGO UN VIRSRAKSTS ---
st.image("New_logo1.png", width=200) 
st.title("☀️ Saules un Akumulatoru ROI Kalkulators")

# --- KLIENTA TIPS ---
client_type = st.radio(
    "Izvēlieties klienta tipu:",
    ["Juridiska persona (Bez PVN)", "Privātpersona (Ar PVN 21%)"],
    horizontal=True
)

is_business = "Juridiska persona" in client_type

# --- IEVADES FORMA ---
with st.form("ievades_forma"):
    st.subheader("📊 Enerģijas dati")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        # Sākuma vērtība iestatīta uz 600 kWh
        usage = st.number_input("Mēneša patēriņš (kWh)", min_value=1, value=600 if not is_business else 9000)
    with col_input2:
        bill_label = "Mēneša rēķins (€ bez PVN)" if is_business else "Mēneša rēķins (€ ar PVN)"
        bill = st.number_input(bill_label, min_value=1.0, value=120.0 if not is_business else 1500.0)
    
    submit_button = st.form_submit_button("Aprēķināt risinājumu")

# --- SĀNU JOSLA: FINANSES ---
st.sidebar.header("⚙️ Finanšu iestatījumi")

if is_business:
    grant_pct = st.sidebar.slider("Valsts atbalsts uzņēmumam (%)", 0, 50, 30) / 100
    fixed_grant = 0
else:
    fixed_grant = st.sidebar.number_input("Valsts atbalsta summa (€)", value=6500)
    grant_pct = 0

interest_rate = st.sidebar.slider("Kredīta procenti (%)", 0.0, 15.0, 5.9) / 100
loan_years = st.sidebar.selectbox("Kredīta termiņš (Gadi)", [5, 7, 10, 15], index=1)

# --- JAUNĀ LINEĀRĀ OPTIMIZĀCIJAS LOĢIKA ---
# Sākumpunkts: 600 kWh -> 6 kW
# Punkts B: 9000 kWh -> 50 kW
# Formula aprēķina pieauguma koeficientu starp šiem punktiem
if usage <= 600:
    calc_solar = 6.0
else:
    # Lineārs pieaugums: 6kW + (papildus patēriņš * slīpums)
    # Slīpums = (50kW - 6kW) / (9000kWh - 600kWh) = 44 / 8400
    calc_solar = 6.0 + (usage - 600) * (44 / 8400)

# Baterijas izmērs (uzturam 1:1.5 vai 1:2 attiecību)
calc_battery = calc_solar * 1.5 

# Bāzes cenas (Bez PVN) - Cenas kļūst zemākas, sistēmai augot
if calc_solar < 15:
    sol_price_base, bat_price_base = 950, 480  # Mazajām sistēmām dārgāk
elif calc_solar < 50:
    sol_price_base, bat_price_base = 750, 320
else:
    sol_price_base, bat_price_base = 680, 245  # Lielajām (industriālajām) lētāk

# PVN piemērošana
vat_multiplier = 1.0 if is_business else 1.21
total_cost = ((calc_solar * sol_price_base) + (calc_battery * bat_price_base)) * vat_multiplier

# Atbalsta piemērošana
if is_business:
    grant_amount = total_cost * grant_pct
else:
    grant_amount = min(fixed_grant, total_cost * 0.5) 

net_investment = total_cost - grant_amount

# KREDĪTA APRĒĶINS
monthly_interest = interest_rate / 12
total_months = loan_years * 12
if interest_rate > 0:
    monthly_loan = net_investment * (monthly_interest * (1 + monthly_interest)**total_months) / ((1 + monthly_interest)**total_months - 1)
else:
    monthly_loan = net_investment / total_months

# IETAUPĪJUMA APRĒĶINS
elec_price_per_kwh = bill / usage
solar_savings_annual = (calc_solar * 1050) * (elec_price_per_kwh + 0.045)
battery_savings_annual = (calc_battery * 280 * 0.08 * 0.85)
total_savings_monthly = (solar_savings_annual + battery_savings_annual) / 12

payback_years = net_investment / (solar_savings_annual + battery_savings_annual) if (solar_savings_annual + battery_savings_annual) > 0 else 0
monthly_net_profit = total_savings_monthly - monthly_loan

# --- REZULTĀTU ATTĒLOŠANA ---
if submit_button or usage:
    st.divider()
    
    st.subheader(f"📊 Rezultāti ({'Privātpersona' if not is_business else 'Uzņēmums'})")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Saules Jauda", f"{calc_solar:.1f} kW")
    c2.metric("Baterija", f"{calc_battery:.1f} kWh")
    c3.metric("Atmaksāšanās", f"{payback_years:.1f} Gadi")

    f1, f2, f3 = st.columns(3)
    f1.metric("Kopējā Investīcija", f"€{total_cost:,.0f}")
    f2.metric("Ikmēneša kredīts", f"€{monthly_loan:,.2f}")
    f3.metric("Ietaupījums vs Kredīts", f"€{monthly_net_profit:,.2f}", delta=f"{monthly_net_profit:,.2f} €/mēn")

    st.write(f"**Valsts atbalsts: €{grant_amount:,.0f}** | **Gala investīcija: €{net_investment:,.0f}**")

    if monthly_net_profit > 0:
        st.success(f"✅ Ietaupījums pilnībā nosedz kredītu!")
    else:
        st.warning(f"ℹ️ Ietaupījums sedz { (total_savings_monthly/monthly_loan)*100 if monthly_loan > 0 else 0:.0f}% no kredīta maksājuma.")

    # Grafiks
    st.subheader("📈 Investīcijas atmaksas prognoze")
    years_plot = np.arange(0, int(max(payback_years + 3, 5)))
    cash_flow = [(total_savings_monthly * 12 * y) - net_investment for y in years_plot]
    st.area_chart(cash_flow)