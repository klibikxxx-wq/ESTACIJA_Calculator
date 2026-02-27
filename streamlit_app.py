import streamlit as st
import numpy as np

# =================================================================
# ⚙️ GLOBĀLIE KONFIGURĀCIJAS PARAMETRI (Maini šos, lai pielāgotu biznesa modeli)
# =================================================================

# Tehniskie pieņēmumi
TECHNICAL_PARAMS = {
    "solar_yield": 1050,      # kWh saražoti uz 1kW gadā (Latvijas vidējais)
    "grid_fee_save": 0.045,   # ST mainīgā daļa (ietaupījums par kWh)
    "bat_cycles": 300,        # Pilni cikli gadā baterijas arbitrāžai
    "arb_spread": 0.10,       # Vidējā cenu starpība (pirkt lēti / tērēt dārgi)
    "bat_eff": 0.88,          # Baterijas efektivitāte (round-trip efficiency)
    "degradation": 0.005,     # Paneļu efektivitātes zudums gadā (0.5%)
    "elec_inflation": 0.03    # Konservatīvs elektrības cenas pieaugums gadā (3%)
}

# Cenu līmeņi (EUR bez PVN)
PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

# =================================================================
# 🖥️ LIETOTNES INTERFEISS UN LOĢIKA
# =================================================================

st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")

st.title("☀️ ESTACIJA Saules & Akumulatoru ROI Pro")
st.markdown("### Profesionāla simulācija biznesa klientiem")

# --- 1. IEVADES SADAĻA ---
st.subheader("📊 1. Klienta un Finansējuma dati")
col1, col2 = st.columns(2)

with col1:
    usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None, help="Ievadiet klienta vidējo mēneša patēriņu")
    bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None, help="Vidējais rēķins bez PVN")

with col2:
    fin_type = st.radio("Finansējuma veids", ["Kredīts", "Pašu kapitāls"], horizontal=True)
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# Kredīta specifika
if fin_type == "Kredīts":
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 1.9) / 100
    with c_f2:
        loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)
else:
    interest_rate, loan_years = 0.0, 0

# --- 2. APRĒĶINU MOTORS ---
# Automātiskā datu aizpilde, ja trūkst viens no parametriem
usage = usage_in if usage_in else (bill_in / 0.16 if bill_in else 0)
bill = bill_in if bill_in else (usage * 0.16 if usage else 0)

if usage > 0:
    # Sistēmas jaudas lineārā loģika (600kWh -> 6kW, 9000kWh -> 50kW)
    calc_solar = 6.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 6.0
    calc_battery = calc_solar * 2.0 

    # Cenas noteikšana pēc kW jaudas
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

    # Gada ietaupījums
    p_kwh = bill / usage if usage > 0 else 0.16
    solar_save_y1 = (calc_solar * TECHNICAL_PARAMS["solar_yield"]) * (p_kwh + TECHNICAL_PARAMS["grid_fee_save"])
    arb_save_y1 = (calc_battery * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"])
    total_save_y1 = solar_save_y1 + arb_save_y1

    # Kredīta ikmēneša maksājums (PMT)
    if fin_type == "Kredīts" and net_inv > 0:
        m_rate = interest_rate / 12
        t_months = loan_years * 12
        pmt = net_inv * (m_rate * (1+m_rate)**t_months) / ((1+m_rate)**t_months-1)
    else:
        pmt = 0

    # --- 3. REZULTĀTU CILNES ---
    tab1, tab2, tab3 = st.tabs(["📋 Kopsavilkums", "⚖️ Neko nedarīt vs ESTACIJA", "⚙️ Konfigurācija"])

    with tab1:
        st.write("### Rekomendētais risinājums")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saules Paneļi", f"{calc_solar:.1f} kW")
        m2.metric("Bateriju Krātuve", f"{calc_battery:.1f} kWh")
        m3.metric("Atmaksāšanās laiks", f"{net_inv/total_save_y1:.1f} Gadi")

        st.divider()
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.write(f"**Projekta tāme:** {total_cost:,.0f} €")
            st.write(f"**Valsts atbalsts:** -{total_cost*grant_pct:,.0f} €")
            st.success(f"**Gala investīcija: {net_inv:,.0f} €**")
        with res_col2:
            st.info(f"**Ietaupījums 1. gadā:** {total_save_y1:,.0f} €")
            if fin_type == "Kredīts":
                st.write(f"**Mēneša kredīta maksājums:** {pmt:,.2f} €")
                cash_flow = (total_save_y1 / 12) - pmt
                st.write(f"**Mēneša Cash-flow:** {cash_flow:,.2f} €")

    with tab2:
        st.subheader("Salīdzinājums 20 gadu griezumā")
        
        def simulate_20y():
            inf = TECHNICAL_PARAMS["elec_inflation"]
            deg = TECHNICAL_PARAMS["degradation"]
            nothing_total = []
            sys_total = []
            
            c_nothing = 0
            c_sys = net_inv if fin_type == "Pašu kapitāls" else 0
            
            for y in range(21):
                nothing_total.append(c_nothing)
                sys_total.append(c_sys)
                
                # Gada pieaugums
                annual_bill = (bill * 12) * ((1 + inf)**y)
                annual_save = total_save_y1 * ((1 + inf)**y) * ((1 - deg)**y)
                loan_cost = (pmt * 12) if (fin_type == "Kredīts" and y < loan_years) else 0
                
                c_nothing += annual_bill
                c_sys += (annual_bill - annual_save + loan_cost)
            return nothing_total, sys_total

        n_data, s_data = simulate_20y()
        st.line_chart({"Palikt pie esošā (Rēķini)": n_data, "Ar ESTACIJA sistēmu": s_data})
        
        
        st.error(f"**Zaudētā nauda 20 gadu laikā, neinvestējot šodien:** {n_data[-1] - s_data[-1]:,.0f} €")

    with tab3:
        st.write("### Pašreizējie sistēmas iestatījumi")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("**Tehniskie mainīgie:**")
            st.json(TECHNICAL_PARAMS)
        with col_c2:
            st.write("**Cenu matrica (EUR):**")
            st.json(PRICING_CONFIG)

else:
    st.info("👋 Ievadiet datus, lai uzreiz redzētu rezultātus.")