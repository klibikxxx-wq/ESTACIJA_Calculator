import streamlit as st
import numpy as np

# =================================================================
# ⚙️ IEKŠĒJIE KONFIGURĀCIJAS PARAMETRI (Nav redzami lietotnē kā kods)
# =================================================================

TECHNICAL_PARAMS = {
    "solar_yield": 1050,      # kWh saražoti uz 1kW gadā
    "grid_fee_save": 0.045,   # ST mainīgā daļa (€/kWh)
    "bat_cycles": 300,        # Pilni cikli gadā arbitrāžai
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
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

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
    calc_solar = 6.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 6.0
    calc_battery = calc_solar * 2.0 

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
    solar_save_y1 = (calc_solar *