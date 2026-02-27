import streamlit as st
import numpy as np

st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")

# --- STILS UN VIRSRAKSTS ---
st.image("New_logo1.png", width=300)
st.title("Saules & Akumulatoru ROI Pro")
st.markdown("### Profesionāla ekonomiskā simulācija biznesa klientiem")

# --- 1. DATU IEVADE ---
with st.expander("📊 Pamata dati un Finansējums", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None, help="Klienta vidējais patēriņš mēnesī")
        bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None)
    with col2:
        fin_type = st.radio("Finansējuma veids", ["Kredīts", "Pašu kapitāls"])
        grant_pct = st.sidebar.slider("Valsts atbalsts (%)", 0, 50, 30) / 100
    with col3:
        if fin_type == "Kredīts":
            interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 1.9) / 100
            loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)
        else:
            interest_rate = 0.0
            loan_years = 0
        discount_rate = 0.08 # Fiksēta diskontēšanas likme fonā

# --- 2. LOGIKA UN APRĒĶINI ---
usage = usage_in if usage_in else (bill_in / 0.16 if bill_in else 0)
bill = bill_in if bill_in else (usage * 0.16 if usage else 0)

if usage > 0:
    # Sistēmas izmērs un izmaksas
    calc_solar = 6.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 6.0
    calc_battery = calc_solar * 2.0 

    if calc_solar < 20: sol_p, bat_p = 800, 350
    elif calc_solar < 50: sol_p, bat_p = 750, 280
    else: sol_p, bat_p = 650, 240

    total_cost = (calc_solar * sol_p) + (calc_battery * bat_p)
    net_inv = total_cost * (1 - grant_pct)

    # Ietaupījumi
    p_kwh = bill / usage
    solar_save_y1 = (calc_solar * 1050) * (p_kwh + 0.045)
    arb_save_y1 = (calc_battery * 300 * 0.10 * 0.88) 
    total_save_y1 = solar_save_y1 + arb_save_y1

    # Kredīta PMT
    if fin_type == "Kredīts":
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
                cash_flow = (total_save_y1 / 12) - pmt
                st.write(f"**Mēneša Cash-flow:** {cash_flow:,.2f} €")

    with tab2:
        st.subheader("Salīdzināt ar 'Neko nedarīt'")
        st.write("Analīze parāda kumulatīvās izmaksas par elektroenerģiju nākamo 20 gadu laikā.")
        
        # Aprēķins tabulai (pieņemot konservatīvu 3% vidējo elektrības cenas pieaugumu gadā)
        def calc_costs(years):
            inf = 0.03
            # Neko nedarīt: rēķinu summa ar inflāciju
            nothing = sum([(bill * 12) * ((1 + inf)**y) for y in range(years)])
            # Ar sistēmu: (jaunais rēķins + kredīts) - ietaupījums
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
        
        st.write("### 📉 Zaudētā iespēja")
        st.error(f"Paliekot pie pašreizējā modeļa, Jūs nākamo 20 gadu laikā 'atdosiet' energo uzņēmumiem aptuveni **{calc_costs(20)[0]:,.0f} €**.")

    with tab3:
        st.write("- **Elektrības cena:** Aprēķināts no Jūsu ievadītajiem datiem.")
        st.write("- **Salīdzinājuma inflācija:** Pieņemts fiksēts 3% pieaugums gadā 'Neko nedarīt' scenārijam.")
        st.write("- **Saules ražība:** 1050 kWh / kW gadā.")
        st.write("- **Arbitrāža:** 300 cikli gadā, pērkot par 0.10 € lētāk nekā tērējot.")

else:
    st.info("👋 Sveicināti! Ievadiet enerģijas datus, lai sāktu analīzi.")