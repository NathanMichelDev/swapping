import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

hours_in_day = 24
min_to_hour = 1 / 60
# Energy in
cols = st.columns(3)
with st.sidebar:
    st.header("Fleet size")
    cols = st.columns(2)
    with cols[0]:
        fasteners = st.number_input(
            "Number of fasteners", min_value=0, max_value=10000, value=200, step=1
        )
    with cols[1]:
        bikes = st.number_input(
            "Number of bikes", min_value=0, max_value=10000, value=1800, step=1
        )
    st.header("User demand modelling")
    mean_trips_per_bike_per_day = st.number_input(
        "Number of trips per bike per day",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=0.1,
    )
    cols = st.columns(2)
    with cols[0]:
        mean_distance_per_trip = st.number_input(
            "Mean distance per trip (km)",
            min_value=0.0,
            max_value=50.0,
            value=3.5,
            step=0.1,
        )
    with cols[1]:
        mean_trip_duration_min = st.number_input(
            "Average trip duration (min)",
            min_value=0.0,
            max_value=100.0,
            value=15.0,
            step=0.1,
        )
    st.header("Energy modelling")
    soc_per_km = st.number_input(
        "Soc per km (%)", min_value=-10.0, max_value=0.0, value=-2.5, step=0.1
    )
    cols = st.columns(2)
    with cols[0]:
        fast_charge_soc_per_hour = st.number_input(
            "Fast charge soc per hour (%/h)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=0.1,
        )
    with cols[1]:
        slow_charge_soc_per_hour = st.number_input(
            "Slow charge soc per hour (%/h)",
            min_value=0.0,
            max_value=100.0,
            value=2.0,
            step=0.1,
        )
    energy_per_swap = st.number_input(
        "Energy per swap (%)", min_value=0.0, max_value=100.0, value=80.0, step=1.0
    )

st.subheader("User demand modelling")
mean_trips_per_day = round(bikes * mean_trips_per_bike_per_day, 2)
mean_km_per_day = round(mean_trips_per_day * mean_distance_per_trip, 2)
mean_trip_duration_hour = round(
    mean_trips_per_day * mean_trip_duration_min * min_to_hour, 2
)
df_user_demand = pd.DataFrame(
    {
        "bikes": bikes,
        "fasteners": fasteners,
        "Mean trips per bike per day": mean_trips_per_bike_per_day,
        "Mean trips per day": mean_trips_per_day,
        "Mean km per day": mean_km_per_day,
        "Mean trip duration": mean_trip_duration_hour,
    },
    index=[0],
)
st.write(df_user_demand.set_index("bikes"))


st.subheader("Energy out")
mean_soc_per_trip = round(mean_distance_per_trip * soc_per_km, 2)
mean_soc_per_bike_per_day = round(mean_soc_per_trip * mean_trips_per_bike_per_day, 2)
energy_out_per_day = round(bikes * mean_soc_per_trip * mean_trips_per_bike_per_day, 2)
df_energy_out = pd.DataFrame(
    {
        "Soc per km (%)": soc_per_km,
        "Mean distance per trip (km)": mean_distance_per_trip,
        "Soc per trip (%)": mean_soc_per_trip,
        "Energy out per bike per day (%)": mean_soc_per_bike_per_day,
        "Total energy out per day (%)": energy_out_per_day,
    },
    index=[0],
)
st.write(df_energy_out.set_index("Soc per km (%)"))

st.subheader("Energy in")
mean_time_spent_in_station_per_bike_per_day = round(
    hours_in_day - mean_trip_duration_min * min_to_hour * mean_trips_per_bike_per_day, 2
)
mean_number_of_bikes_per_fastener_per_day = round(
    (mean_time_spent_in_station_per_bike_per_day / hours_in_day) * bikes / fasteners, 2
)
energy_in_per_day_per_fastener = round(
    hours_in_day
    * (
        (mean_number_of_bikes_per_fastener_per_day - 1) * slow_charge_soc_per_hour
        + 1 * fast_charge_soc_per_hour
    ),
    2,
)
energy_in_per_day = fasteners * energy_in_per_day_per_fastener
energy_in_per_day_per_bike = round(energy_in_per_day / bikes, 2)
df_energy_in = pd.DataFrame(
    {
        "Hours in station per bike per day": mean_time_spent_in_station_per_bike_per_day,
        "Average bikes per fastener per day": mean_number_of_bikes_per_fastener_per_day,
        "Energy in per day per fastener (%)": energy_in_per_day_per_fastener,
        "Energy in per day per bike (%)": energy_in_per_day_per_bike,
        "Total energy in per day (%)": energy_in_per_day,
    },
    index=[0],
)
st.write(df_energy_in.set_index("Hours in station per bike per day"))

st.subheader("Energy balance")
energy_balance = energy_in_per_day + energy_out_per_day
energy_balance_per_bike = round(energy_balance / bikes, 2)
df = pd.DataFrame(
    {
        "Per bike": [
            energy_in_per_day_per_bike,
            mean_soc_per_bike_per_day,
            energy_balance_per_bike,
        ],
        "Total": [energy_in_per_day, energy_out_per_day, energy_balance],
    },
    index=["Energy in per day", "Energy out per day", "Energy balance per day"],
)
st.write(df.transpose())

st.subheader("Swaps")
if energy_balance >= 0:
    st.success("Energy balance is positive!")
else:
    swaps_to_do_per_day = -energy_balance / energy_per_swap
    df_swaps = pd.DataFrame(
        {
            "Total energy balance per day (%)": energy_balance,
            "Energy per swap (%)": energy_per_swap,
            "Swaps to do per day": swaps_to_do_per_day,
        },
        index=[0],
    )
    st.write(df_swaps.set_index("Total energy balance per day (%)"))
