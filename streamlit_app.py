import streamlit as st
import numpy as np

# ==========================================
# ⚙️ KONFIGURĀCIJAS PARAMETRI (Maini šeit)
# ==========================================
PRICING_CONFIG = {
    "small": {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large": {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

TECHNICAL_PARAMS = {
    "solar_yield": 1050,      # kWh saražoti uz 1kW gadā
    "grid_fee_save": 0.045,   # ST mainīgā daļa (ietaupījums)
    "bat_cycles": 300,        # Pilni cikli gadā arbitrāžai
    "arb_spread": 0.10,       # Cenas starpība (nakts/diena)
    "bat_eff": 0.88,          # Baterijas efektivitāte (round-trip)
    "degradation": 0.005,     # Paneļu jaudas zudums gadā (0.5%)
    "elec_inflation": 0.03    # Elektrības cenas pieaugums gadā (3%)
}

# ==========================================
# 🖥️ LIETOTNES IESTATĪJUMI
# ==========================================
st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")
st.image("New_logo1.png", width=300)
st.title("Saules & Akumulatoru ROI Pro")

# --- 1. IEVADES DATI ---
st.subheader("📊 1. Klienta un Finansējuma dati")
col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])

with col1:
    usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None)
with col2:
    bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None)
with col3:
    fin_type = st.radio("Finansējums", ["Kredīts", "Pašu kapitāls"], horizontal=True)
with col4:
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# Kredīta specifika (parādās tikai ja izvēlēts kredīts)
if fin_type == "Kredīts":
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 1.9) / 100
    with c_f2:
        loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)
else:
    interest_rate, loan_years = 0.0, 0

# --- 2. APRĒĶINU LOĢIKA ---
usage = usage_in if usage_in else (bill_in / 0.16 if bill_in else 0)
bill = bill_in if bill_in else (usage * 0.16 if usage else 0)

if usage > 0:
    # Sistēmas jaudas noteikšana (Lineāra loģika)
    calc_solar = 6.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 6.0
    calc_battery = calc_solar * 2.0 

    # Cenu piemērošana no konfigurācijas
    if calc_solar < PRICING_CONFIG["small"]["max_kw"]:
        s_price = PRICING_CONFIG["small"]["solar_eur_kw"]
        b_price = PRICING_CONFIG["small"]["bat_eur_kwh"]
    elif calc_solar < PRICING_CONFIG["medium"]["max_kw"]:
        s_price = PRICING_CONFIG["medium"]["solar_eur_kw"]
        b_price = PRICING_CONFIG["medium"]["bat_eur_kwh"]
    else:
        s_price = PRICING_CONFIG["large"]["solar_eur_kw"]
        b_price = PRICING_CONFIG["large"]["bat_eur_kwh"]

    total_cost = (calc_solar * s_price) + (calc_battery * b_price)
    net_inv = total_cost * (1 - grant_pct)

    # Ietaupījumu aprēķins izmantojot TECHNICAL_PARAMS
    p_kwh = bill / usage if usage > 0 else 0.16
    solar_save_y1 = (calc_solar * TECHNICAL_PARAMS["solar_yield"]) * (p_kwh + TECHNICAL_PARAMS["grid_fee_save"])
    arb_save_y1 = (calc_battery * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"])
    total_save_y1 = solar_save_y1 + arb_save_y1

    # Kredīta PMT
    if fin_type == "Kredīts" and net_inv > 0:
        m_rate = interest_rate / 12
        t_months = loan_years * 12
        pmt = net_inv * (m_rate * (1+m_rate)**t_months) / ((1+m_rate)**t_months-1)
    else:
        pmt = 0

    # --- 3. REZULTĀTU ATTĒLOŠANA ---
    tab1, tab2, tab3 = st.tabs(["📋 Piedāvājums", "⚖️ Salīdzinājums", "⚙️ Tehniskie dati"])

    with tab1:
        m1, m2, m3 = st.columns(3)
        m1.metric("Saules Jauda", f"{calc_solar:.1f} kW")
        m2.metric("Baterijas Ietilpība", f"{calc_battery:.1f} kWh")
        m3.metric("Atmaksāšanās", f"{net_inv/total_save_y1:.1f} Gadi")

        st.divider()
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"**Kopējā sistēmas cena:** {total_cost:,.0f} €")
            st.markdown(f"**Valsts atbalsts:** -{total_cost*grant_pct:,.0f} €")
            st.success(f"**Gala neto investīcija: {net_inv:,.0f} €**")
        with col_res2:
            st.info(f"**Ietaupījums gadā:** {total_save_y1:,.0f} €")
            if fin_type == "Kredīts":
                st.write(f"**Mēneša kredīts:** {pmt:,.2f} €")
                st.write(f"**Mēneša peļņa (Cash-flow):** {(total_save_y1/12)-pmt:,.2f} €")

    with tab2:
        st.subheader("Kumulatīvais 20 gadu ietaupījums")
        
        def run_20y_sim():
            inf = TECHNICAL_PARAMS["elec_inflation"]
            deg = TECHNICAL_PARAMS["degradation"]
            nothing_cost = []
            with_sys_cost = []
            
            curr_nothing = 0
            curr_sys = net_inv if fin_type == "Pašu kapitāls" else 0
            
            for y in range(21):
                nothing_cost.append(curr_nothing)
                with_sys_cost.append(curr_sys)
                
                # Nākamā gada pieaugums
                annual_bill = (bill * 12) * ((1 + inf)**y)
                annual_save = total_save_y1 * ((1 + inf)**y) * ((1 - deg)**y)
                loan_cost = (pmt * 12) if (fin_type == "Kredīts" and y < loan_years) else 0
                
                curr_nothing += annual_bill
                curr_sys += (annual_bill - annual_save + loan_cost)
            return nothing_cost, with_sys_cost

        n_costs, w_costs = run_20y_sim()
        st.line_chart({"Maksāt Latvenergo": n_costs, "Ar ESTACIJA sistēmu": w_costs})
        
        
        st.error(f"Zaudējumi pēc 20 gadiem neinvestējot: **{n_costs[-1] - w_costs[-1]:,.0f} €**")

    with tab3:
        st.write("Visi aprēķini balstīti uz šādiem konfigurācijas parametriem:")
        st.json(TECHNICAL_PARAMS)
        st.write("Cenu līmeņi (EUR/vienība):")
        st.json(PRICING_CONFIG)

else:
    st.info("Ievadiet datus, lai sāktu!")