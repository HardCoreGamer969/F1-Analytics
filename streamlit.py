import streamlit as st
import fastf1
import fastf1.plotting
from fastf1 import get_session
import matplotlib.pyplot as plt
import pandas as pd

fastf1.plotting.setup_mpl(misc_mpl_mods=False, color_scheme='fastf1')

# Define available tracks per year (this needs to be updated for each year)
TRACKS_BY_YEAR = {
    2025: ['Monza', 'Bahrain', 'Jeddah', 'Australia', 'Azerbaijan', 'Miami', 'Monaco', 'Spain', 'Canada', 'Austria', 'Britain', 'Hungary', 'Belgium', 'Netherlands', 'Italy', 'Singapore', 'Japan', 'Qatar', 'United States', 'Mexico', 'Brazil', 'Abu Dhabi'],
    2024: ['Monza', 'Bahrain', 'Jeddah', 'Australia', 'Azerbaijan', 'Miami', 'Monaco', 'Spain', 'Canada', 'Austria', 'Britain', 'Hungary', 'Belgium', 'Netherlands', 'Italy', 'Singapore', 'Japan', 'Qatar', 'United States', 'Mexico', 'Brazil', 'Abu Dhabi'],
    # Add other years and their tracks as necessary
}

# Define track lengths for specific Grand Prix races (these need to be updated per year if track lengths change)
TRACK_LENGTHS = {
    'Monza': 5793,
    'Bahrain': 5412,
    'Jeddah': 6164,
    'Australia': 5309,
    'Azerbaijan': 6003,
    'Miami': 5413,
    'Monaco': 3337,
    'Spain': 4655,
    'Canada': 4316,
    'Austria': 4318,
    'Britain': 5891,
    'Hungary': 4381,
    'Belgium': 7004,
    'Netherlands': 4305,
    'Italy': 5793,
    'Singapore': 5063,
    'Japan': 5795,
    'Qatar': 5380,
    'United States': 5513,
    'Mexico': 4304,
    'Brazil': 4309,
    'Abu Dhabi': 5554,
    # Add more tracks as necessary
}


def get_user_input():
    # Get user input for year and track
    year = st.selectbox('Select the year you want to access data for:', list(TRACKS_BY_YEAR.keys()))
    available_tracks = TRACKS_BY_YEAR[year]
    gp = st.selectbox("Select the Grand Prix:", options=available_tracks)
    session_type = st.selectbox("Select session type", ['FP1', 'Qualifying', 'Race'])

    plot_choice = st.radio("Do you want to generate a graph?", ('yes', 'no'))

    graph_type = None
    driver = None
    if plot_choice == 'yes':
        graph_type = st.selectbox("Choose graph type", ['Tyre Strategy', 'Position During Race'])
        driver = st.text_input("Enter the 3-letter driver code (e.g., VER, LEC, HAM):").strip().upper()

    confirm_button = st.button("Load Session and Generate Data")
    if confirm_button:
        load_session(year, gp, session_type, driver, graph_type)


def load_session(year, gp, session_type, driver=None, graph_type=None):
    try:
        session = get_session(year, gp, session_type)
        session.load(laps=True, telemetry=True, weather=True, messages=True)
        st.write(f"🗓️ Session Loaded: {session.name}")
        print_basic_info(session, gp)

        if driver and graph_type:
            graph_type = graph_type.lower()
            if graph_type == 'tyre strategy':
                plot_tyre_strategy(session, driver)
            elif graph_type == 'position during race':
                plot_position(session, driver)
            else:
                st.write("Graph type not recognized 😬")
    except Exception as e:
        st.write(f"⚠️ Something went wrong: {e}")


def print_basic_info(session, gp):
    results = session.results
    results = results.sort_values('Position')

    st.write("\n🏆 Podium:")
    for i in range(3):
        pos = i + 1
        row = results.iloc[i]
        pos_label = f"{pos}st" if pos == 1 else f"{pos}nd" if pos == 2 else f"{pos}rd"
        driver_name = row['FullName']
        team = row['TeamName']
        st.write(f"{pos_label}: {driver_name} ({team})")

    # Fastest Lap
    laps = session.laps
    fastest_lap = laps.pick_fastest()
    fastest_driver = results[results['Abbreviation'] == fastest_lap['Driver']].iloc[0]
    fastest_lap_time = fastest_lap['LapTime'].total_seconds()
    track_length_km = TRACK_LENGTHS.get(gp, 5.0) / 1000  # Default to 5.0 km if track length is not found
    avg_speed = (track_length_km / fastest_lap_time) * 3600  # in km/h

    st.write(f"\n⚡ Fastest Lap: {fastest_driver['FullName']} - {str(fastest_lap['LapTime']).split(' ')[-1][:-3]}")
    st.write(f"🔴 Average Speed: {avg_speed:.2f} km/h (Achieved on Lap {fastest_lap['LapNumber']})")

    # Weather
    weather = session.weather_data.iloc[0]
    st.write(f"\n🌦️ Weather at race start: {weather['AirTemp']}°C, Track: {weather['TrackTemp']}°C, "
             f"Humidity: {weather['Humidity']}%, Rainfall: {weather['Rainfall']}")


def plot_tyre_strategy(session, driver):
    driver_laps = session.laps.pick_driver(driver)
    stints = driver_laps[['Stint', 'Compound', 'LapNumber']].drop_duplicates()

    st.write("\n🛞 Tyre Strategy:")

    # Identify starting tyre, lap of change, and final tyre
    start_tyres = stints.iloc[0]
    start_tyres_info = f"Started with {start_tyres['Compound']} tyres on lap {start_tyres['LapNumber']}"

    change_info = []
    for i in range(1, len(stints)):
        if stints.iloc[i]['Stint'] != stints.iloc[i - 1]['Stint']:  # A tyre change occurred
            change_info.append(f"Changed to {stints.iloc[i]['Compound']} on lap {stints.iloc[i]['LapNumber']}")

    final_tyre = stints.iloc[-1]
    end_info = f"Finished with {final_tyre['Compound']} tyres on lap {final_tyre['LapNumber']}"

    # Print summarized tyre strategy
    st.write(start_tyres_info)
    for change in change_info:
        st.write(change)
    st.write(end_info)

    # Visualize tyre strategy
    colors = {
        'SOFT': 'red',
        'MEDIUM': 'yellow',
        'HARD': 'white',
        'INTERMEDIATE': 'green',
        'WET': 'blue'
    }

    fig, ax = plt.subplots()
    for stint in stints.itertuples():
        color = colors.get(stint.Compound.upper(), 'gray')
        ax.plot([stint.LapNumber, stint.LapNumber + 5], [1, 1], color=color, linewidth=8)

    ax.set_title(f"{driver} - Tyre Strategy")
    ax.set_yticks([])
    plt.xlabel("Lap Number")
    st.pyplot(fig)


def plot_position(session, driver):
    driver_laps = session.laps.pick_driver(driver).sort_values(by='LapNumber')
    lap_nums = driver_laps['LapNumber']
    positions = driver_laps['Position']

    fig, ax = plt.subplots()
    ax.plot(lap_nums, positions, marker='o')
    ax.invert_yaxis()  # Lower position = better
    ax.set_title(f"{driver} - Position During Race")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Race Position")
    ax.grid(True)
    st.pyplot(fig)


def test_session():
    st.write("Test session functionality isn't supported yet 💀")


get_user_input()