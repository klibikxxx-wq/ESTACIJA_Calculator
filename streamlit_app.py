import streamlit as st
import numpy as np

# =================================================================
# ⚙️ IEKŠĒJIE KONFIGURĀCIJAS PARAMETRI (Nav redzami lietotnē kā kods)
# =================================================================

TECHNICAL_PARAMS = {
    "solar_yield": 800,      # kWh saražoti uz 1kW gadā
    "grid_fee_save": 0.045,   # ST mainīgā daļa (€/kWh)
    "bat_cycles": 365,        # Pilni cikli gadā arbitrāžai
    "arb_spread": 0.10,       # Cenu starpība (€/kWh)
    "bat_eff": 0.88,          # Baterijas lietderība
    "degradation": 0.005,     # Paneļu jaudas zudums gadā
    "elec_inflation": 0.03    # Elektrības cenas pieaugums gadā
}

PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

# =================================================================
# 🖥️ LIETOTNES INTERFEISS
# =================================================================

st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")

# Logo un Virsraksts
st.image("New_logo1.png", width=300)
st.title("Saules un Akumulatoru ROI Kalkulators")
st.markdown("---")

# --- 1. IEVADES SADAĻA ---
st.subheader("📊 1. Enerģijas dati un Finansējums")
col1, col2 = st.columns(2)

with col1:
    usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None)
    bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None)

with col2:
    fin_type = st.radio("Finansējuma veids", ["Kredīts", "Pašu kapitāls"], horizontal=True)
    grant_pct = st.slider("Valsts atbalsts (%)", 10, 60, 30) / 100

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
    calc_solar = 8.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 8.0
    calc_battery = calc_solar * 1.4 

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

    p_kwh = bill / usage if usage > 0 else 0.16
    solar_save_y1 = (calc_solar * TECHNICAL_PARAMS["solar_yield"]) * (p_kwh + TECHNICAL_PARAMS["grid_fee_save"])
    arb_save_y1 = (calc_battery * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"])
    total_save_y1 = solar_save_y1 + arb_save_y1

    if fin_type == "Kredīts" and net_inv > 0:
        m_rate = interest_rate / 12
        t_months = loan_years * 12
        pmt = net_inv * (m_rate * (1+m_rate)**t_months) / ((1+m_rate)**t_months-1)
    else:
        pmt = 0

    # --- 3. REZULTĀTU CILNES ---
    tab1, tab2, tab3 = st.tabs(["📋 Kopsavilkums", "⚖️ Salīdzinājums", "📄 Pieņemtie dati"])

    with tab1:
        st.markdown("### Rekomendētā sistēmas jauda")
        m1, m2, m3 = st.columns(3)
        m1.metric("Saules Paneļi", f"{calc_solar:.1f} kWp")
        m2.metric("Bateriju Krātuve", f"{calc_battery:.1f} kWh")
        m3.metric("Atmaksāšanās", f"{net_inv/total_save_y1:.1f} Gadi")

        st.divider()
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.write(f"**Kopējā projekta tāme:** {total_cost:,.0f} € bez PVN")
            st.write(f"**Valsts atbalsts ({int(grant_pct*100)}%):** -{total_cost*grant_pct:,.0f} €")
            st.success(f"**Gala investīcija: {net_inv:,.0f} €**")
        with res_col2:
            st.info(f"**Ietaupījums 1. gadā:** {total_save_y1:,.0f} €")
            if fin_type == "Kredīts":
                st.write(f"**Mēneša kredīta maksājums:** {pmt:,.2f} €")
                m_profit = (total_save_y1 / 12) - pmt
                st.write(f"**Mēneša ieguvums (Cash-flow):** {m_profit:,.2f} €")

    with tab2:
        st.subheader("Finansiālais ieguvums 20 gadu laikā")
        def simulate_20y():
            inf, deg = TECHNICAL_PARAMS["elec_inflation"], TECHNICAL_PARAMS["degradation"]
            n_list, s_list = [], []
            c_n, c_s = 0, (net_inv if fin_type == "Pašu kapitāls" else 0)
            for y in range(21):
                n_list.append(c_n)
                s_list.append(c_s)
                annual_bill = (bill * 12) * ((1 + inf)**y)
                annual_save = total_save_y1 * ((1 + inf)**y) * ((1 - deg)**y)
                loan_cost = (pmt * 12) if (fin_type == "Kredīts" and y < loan_years) else 0
                c_n += annual_bill
                c_s += (annual_bill - annual_save + loan_cost)
            return n_list, s_list

        n_data, s_data = simulate_20y()
        st.line_chart({"Maksāt Latvenergo": n_data, "Ar ESTACIJA risinājumu": s_data})
        st.error(f"**Zaudējumi pēc 20 gadiem neinvestējot: {n_data[-1] - s_data[-1]:,.0f} €**")

    with tab3:
        st.subheader("Kā mēs aprēķinām Jūsu ieguvumus?")
        st.write("Lai aprēķins būtu maksimāli precīzs jāveic individuāla objekta apsekošana un simulācijas izveide")
        st.write("Šis aprēķins ir provizorisks, taču mēs izmantojam sekojošus pieņēmumus")
                 
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"☀️ **Saules ražība:** {TECHNICAL_PARAMS['solar_yield']} kWh gadā uz katru uzstādīto kWp.")
            st.info(f"📉 **Sistēmas nolietojums:** Aprēķinā iekļauts paneļu efektivitātes zudums {TECHNICAL_PARAMS['degradation']*100}% gadā.")
            st.info(f"⚡ **ST tarifs:** Mainīgā Sadales tīkla tarifa ietaupījums {TECHNICAL_PARAMS['grid_fee_save']} €/kWh.")
        with c2:
            st.info(f"🔋 **Enerģijas arbitrāža:** Baterija tiek uzlādēta lētajās stundās un izmantota dārgajās.")
            st.info(f"📊 **Cenu starpība:** Vidējā peļņa no enerģijas cenas svārstības pieņemta {TECHNICAL_PARAMS['arb_spread']} €/kWh.")
            st.info(f"📈 **Elektrības inflācija:** Konservatīvs tirgus cenas pieauguma pieņēmums {TECHNICAL_PARAMS['elec_inflation']*100}% gadā.")

else:
    st.info("👋 Sveicināti! Ievadiet patēriņa vai rēķina datus, lai ģenerētu analīzi.")