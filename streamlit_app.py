import streamlit as st

st.set_page_config(page_title="Solar & Battery Optimizer", page_icon="☀️")

st.title("☀️ Solar & Battery ROI Optimizer")
st.write("Enter the client's current energy data to see the optimal system.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Current Energy Profile")
bill = st.sidebar.number_input("Monthly Bill (€)", value=3100)
usage = st.sidebar.number_input("Monthly Usage (kWh)", value=19000)

st.sidebar.header("Financial Settings")
grant = st.sidebar.slider("State Grant (%)", 0, 50, 30) / 100
interest = st.sidebar.slider("Loan Interest (%)", 0.0, 10.0, 5.0) / 100
years = st.sidebar.selectbox("Loan Term (Years)", [5, 7, 10, 15], index=1)

# --- SMART LOGIC ENGINE ---
# 1. Optimize Solar (40% coverage rule)
calc_solar = (usage * 12 * 0.4) / 1000

# 2. Optimize Battery (1.5x ratio rule)
calc_battery = calc_solar * 1.5

# 3. Dynamic Pricing (Economy of Scale)
sol_price = 1100 if calc_solar < 15 else (900 if calc_solar < 40 else 750)
bat_price = 500 if calc_battery < 20 else (380 if calc_battery < 100 else 245)

total_cost = (calc_solar * sol_price) + (calc_battery * bat_price)
net_investment = total_cost * (1 - grant)

# 4. Savings Logic
solar_savings = (calc_solar * 1000) * ((bill/usage) + 0.045)
battery_savings = (calc_battery * 280 * 0.08 * 0.85)
total_annual_savings = solar_savings + battery_savings
payback = net_investment / total_annual_savings

# --- DISPLAY RESULTS ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Recommended Solar", f"{calc_solar:.1f} kW")
    st.metric("Recommended Battery", f"{calc_battery:.1f} kWh")

with col2:
    st.metric("Total Investment", f"€{total_cost:,.0f}")
    st.success(f"Payback: {payback:.1f} Years")

st.divider()

# --- SENSITIVITY ANALYSIS ---
st.subheader("Price Sensitivity Analysis")
st.write("How payback time changes if electricity prices fluctuate:")
changes = [-0.2, -0.1, 0, 0.1, 0.2]
scenarios = {}
for c in changes:
    label = f"{int(c*100):+}% Price"
    scenarios[label] = net_investment / (total_annual_savings * (1 + c))

st.bar_chart(scenarios)

st.info(f"Monthly Savings: €{total_annual_savings/12:,.2f} | Grant amount: €{total_cost * grant:,.0f}")
