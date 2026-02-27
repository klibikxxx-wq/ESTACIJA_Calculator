import streamlit as st
import numpy as np

st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")

# --- VIRSRAKSTS ---
st.image("New_logo1.png", width=300)
st.title("Saules & Akumulatoru ROI Pro")
st.markdown("### Profesionāla ekonomiskā simulācija biznesa klientiem")

# --- 1. DATU IEVADE (BEZ FORMAS TŪLĪTĒJAI ATJAUNOŠANAI) ---
st.subheader("📊 1. Enerģijas dati")
col1, col2 = st.columns(2)
with col1:
    usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None, help="Klienta vidējais patēriņš mēnesī")
with col2:
    bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None)

st.divider()

st.subheader("🏦 2. Finansējuma dati (Kredīts)")
col3, col4, col5 = st.columns(3)
with col3:
    fin_type = st.radio("Finansējuma veids", ["Kredīts", "Pašu kapitāls"], horizontal=True)
with col4:
    # Noklusējuma 1.9%
    interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 1.9, disabled=(fin_type == "Pašu kapitāls")) / 100
with col5:
    # Noklusējuma 5 gadi
    loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5, disabled=(fin_type == "Pašu kapitāls"))

# --- SĀNU JOSLA: VALSTS ATBALSTS ---
st.sidebar.header("⚙️ Konfigurācija")
grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# --- 2. LOGIKA UN APRĒĶINI ---
# Datu validācija un automātiskā papildināšana
usage = usage_in if usage_in else (bill_in / 0.16 if bill_in else 0)
bill = bill_in if bill_in else (usage * 0.16 if usage else 0)

if usage > 0:
    # Sistēmas izmērs (Lineārs: 600kWh -> 6kW, 9000kWh -> 50kW)
    if usage <= 600:
        calc_solar = 6.0
    else:
        calc_solar = 6.0 + (usage - 600) * (44 / 8400)
    
    calc_battery = calc_solar * 2.0 

    # Cenu modelis kalibrēts biznesam (Bez PVN)
    if calc_solar < 20: sol_p, bat_p = 700, 250 # Aptuveni 14kW sistēma būs ap 13-14k EUR
    elif calc_solar < 50: sol_p, bat_p = 650, 220
    else: sol_p, bat_p = 600, 200

    total_cost = (calc_solar * sol_p) + (calc_battery * bat_p)
    net_inv = total_cost * (1 - grant_pct)

    # Ietaupījumi
    p_kwh = bill / usage if usage > 0 else 0.16
    solar_save_y1 = (calc_solar * 1050) * (p_kwh + 0.045)
    arb_save_y1 = (calc_battery * 300 * 0.10 * 0.88) 
    total_save_y1 = solar_save_y1 + arb_save_y1

    # Kredīta PMT
    if fin_type == "Kredīts" and net_inv > 0:
        m_rate = interest_rate / 12
        t_months = loan_years * 12
        pmt = net_inv * (m_rate * (1+m_rate)**t_months) / ((1+m_rate)**t_months-1)
    else:
        pmt = 0

    # --- 3. REZULTĀTU CILNES ---
    tab1, tab2, tab3 = st.tabs(["📋 Kopsavilkums", "⚖️ Salīdzinājums", "⚙️ Pieņēmumi"])

    with tab1:
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Saules stacija", f"{calc_solar:.1f} kW")
        c_m2.metric("Akumulatoru krātuve", f"{calc_battery:.1f} kWh")
        c_m3.metric("Atmaksāšanās", f"{net_inv/total_save_y1:.1f} Gadi")

        st.divider()
        res1, res2 = st.columns(2)
        with res1:
            st.write(f"**Investīcija:** {total_cost:,.0f} €")
            st.write(f"**Valsts atbalsts:** -{total_cost*grant_pct:,.0f} €")
            st.success(f"**Gala neto investīcija: {net_inv:,.0f} €**")
        with res2:
            st.info(f"**Ietaupījums 1. gadā:** {total_save_y1:,.0f} €")
            if fin_type == "Kredīts":
                st.write(f"**Mēneša kredīta maksājums:** {pmt:,.2f} €")
                cash_flow_m = (total_save_y1 / 12) - pmt
                st.write(f"**Mēneša Cash-flow:** {cash_flow_m:,.2f} €")

    with tab2:
        st.subheader("Salīdzināt ar 'Neko nedarīt'")
        st.write("Kumulatīvās izmaksas nākamo 20 gadu laikā (iekļaujot 3% elektrības inflāciju).")
        
        def calc_costs(years):
            inf = 0.03
            nothing = sum([(bill * 12) * ((1 + inf)**y) for y in range(years)])
            with_sys = net_inv if fin_type == "Pašu kapitāls" else 0
            for y in range(years):
                annual_bill = (bill * 12) * ((1 + inf)**y)
                annual_save = total_save_y1 * ((1 + inf)**y) * (0.995**y)
                loan_cost = (pmt * 12) if (fin_type == "Kredīts" and y < loan_years) else 0
                with_sys += (annual_bill - annual_save + loan_cost)
            return nothing, with_sys

        comparison_data = []
        for y in [5, 10, 20]:
            n, w = calc_costs(y)
            comparison_data.append({
                "Periods": f"{y} gadi",
                "Maksāt Latvenergo (€)": f"{n:,.0f}",
                "Ar ESTACIJA sistēmu (€)": f"{w:,.0f}",
                "IEGUVUMS (€)": f"{n-w:,.0f}"
            })
        
        st.table(comparison_data)
        
        st.error(f"Paliekot pie pašreizējā modeļa, Jūs nākamo 20 gadu laikā zaudēsiet aptuveni **{calc_costs(20)[0]-calc_costs(20)[1]:,.0f} €**.")

    with tab3:
        st.write("### Aprēķina pieņēmumi")
        st.write("- **Tūlītēja atjaunošanās:** Rezultāti tiek pārrēķināti brīdī, kad maināt jebkuru lauku.")
        st.write("- **Elektrības inflācija:** Salīdzinājuma tabulā pieņemts fiksēts 3% pieaugums gadā.")
        st.write("- **Degradācija:** Saules paneļu jaudas samazinājums par 0.5% gadā.")
        st.write("- **Arbitrāža:** Baterija pelna uz nakts/dienas cenu starpību (~0.10 €/kWh).")

else:
    st.info("👋 Ievadiet patēriņu vai rēķina summu, lai uzreiz redzētu aprēķinu.")