import streamlit as st
import numpy as np
import numpy_financial as npf # Nepieciešams pip install numpy-financial

st.set_page_config(page_title="ESTACIJA Business ROI Pro", page_icon="📈", layout="wide")

# --- STILS UN VIRSRAKSTS ---
st.image("New_logo1.png", width=300)
st.title("☀️ ESTACIJA Saules & Akumulatoru ROI Pro")
st.markdown("### Profesionāla ekonomiskā simulācija biznesa klientiem")

# --- 1. DATU IEVADE (Cilne: Iestatījumi) ---
with st.expander("📊 Pamata dati un Finansējums", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        usage_in = st.number_input("Mēneša patēriņš (kWh)", min_value=0.0, value=None, help="Klienta vidējais patēriņš mēnesī")
        bill_in = st.number_input("Mēneša rēķins (€ bez PVN)", min_value=0.0, value=None)
    with col2:
        fin_type = st.radio("Finansējuma veids", ["Kredīts", "Pašu kapitāls"])
        grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100
    with col3:
        elec_inflation = st.slider("Elektrības inflācija (%/gadā)", 0.0, 10.0, 3.0) / 100
        discount_rate = st.slider("Diskontēšanas likme (WACC %)", 1.0, 15.0, 8.0) / 100

    if fin_type == "Kredīts":
        c_loan1, c_loan2 = st.columns(2)
        with c_loan1:
            interest_rate = st.slider("Kredīta procenti (%)", 1.9, 15.0, 5.9) / 100
        with c_loan2:
            loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=7)
    else:
        interest_rate = 0.0
        loan_years = 0

# --- 2. LOGIKA UN APRĒĶINI ---
# Noklusējuma vērtības, ja dati ir tukši
usage = usage_in if usage_in else (bill_in / 0.16 if bill_in else 0)
bill = bill_in if bill_in else (usage * 0.16 if usage else 0)

if usage > 0:
    # Sistēmas izmērs
    calc_solar = 6.0 + (max(0, usage - 600) * (44 / 8400)) if usage > 600 else 6.0
    calc_battery = calc_solar * 2.0 

    # Cenu modelis (Bez PVN)
    if calc_solar < 20: sol_p, bat_p = 800, 350
    elif calc_solar < 50: sol_p, bat_p = 750, 280
    else: sol_p, bat_p = 650, 240

    total_cost = (calc_solar * sol_p) + (calc_battery * bat_p)
    net_inv = total_cost * (1 - grant_pct)

    # Ietaupījumi (Gada)
    p_kwh = bill / usage
    solar_save_y1 = (calc_solar * 1050) * (p_kwh + 0.045)
    
    # Detalizēta Arbitrāža
    arb_spread = 0.10 # Starpība starp nakts un dienas biržas cenu
    arb_save_y1 = (calc_battery * 300 * arb_spread * 0.88) # 300 cikli, 88% efektivitāte
    
    total_save_y1 = solar_save_y1 + arb_save_y1

    # Naudas plūsmas 25 gadiem (NPV/IRR)
    cash_flows = [-net_inv]
    for y in range(1, 26):
        # Ietaupījums aug ar inflāciju, sistēma degradē par 0.5%/gadā
        save_t = total_save_y1 * ((1 + elec_inflation)**y) * (0.995**y)
        
        # Ja ir kredīts, atņemam maksājumu pirmajos gados
        if fin_type == "Kredīts" and y <= loan_years:
            m_rate = interest_rate / 12
            pmt = net_inv * (m_rate * (1+m_rate)**(loan_years*12)) / ((1+m_rate)**(loan_years*12)-1)
            save_t -= (pmt * 12)
            
        cash_flows.append(save_t)

    npv = npf.npv(discount_rate, cash_flows)
    irr = npf.irr(cash_flows)

    # --- 3. REZULTĀTU CILNES (Tabs) ---
    tab1, tab2, tab3 = st.tabs(["📋 Kopsavilkums", "📈 Finanšu analīze", "⚙️ Pieņēmumi"])

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
                st.write(f"**Gada kredīta maksājums:** {pmt*12:,.0f} €")
                st.write(f"**Cash-flow pozitīvs:** {'JĀ ✅' if (total_save_y1 > pmt*12) else 'NĒ ⚠️'}")

    with tab2:
        st.subheader("Ilgtermiņa vērtība (25 gadi)")
        col_f1, col_f2 = st.columns(2)
        col_f1.metric("NPV (Tīrā pašreizējā vērtība)", f"{npv:,.0f} €", help="Projekta vērtība šodienas naudā.")
        col_f2.metric("IRR (Iekšējā peļņas likme)", f"{irr*100:.1f} %", help="Projekta rentabilitātes procents.")

        # Grafiks
        st.subheader("Kumulatīvā naudas plūsma (€)")
        cum_cf = np.cumsum(cash_flows)
        st.area_chart(cum_cf)
        

    with tab3:
        st.write("### Aprēķina algoritma parametri")
        st.write(f"- **Saules ražība:** 1050 kWh / kW gadā")
        st.write(f"- **Baterijas arbitrāža:** 300 pilni cikli gadā ar 10 centu spread.")
        st.write(f"- **ST tarifs:** Ietaupījums 0.045 €/kWh (mainīgā daļa).")
        st.write(f"- **Degradācija:** Sistēmas efektivitāte krītas par 0.5% gadā.")

else:
    st.info("Lūdzu, ievadiet datus, lai ģenerētu analīzi.")