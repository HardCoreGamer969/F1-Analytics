import fastf1
import fastf1.plotting
from fastf1 import get_session
import matplotlib.pyplot as plt

fastf1.plotting.setup_mpl(misc_mpl_mods=False, color_scheme='fastf1')

# Define track lengths for all circuits that have hosted an F1 Grand Prix
TRACK_LENGTHS = {
    'monza': 5793,
    'albert park': 5303,
    'baku city circuit': 6003,
    'barcelona-catalunya': 4655,
    'silverstone': 5891,
    'spa-francorchamps': 7004,
    'circuit de la sarthe': 13850,
    'circuit gilles villeneuve': 4216,
    'interlagos': 4309,
    'suzuka': 5807,
    'circuit de monaco': 3337,
    'yas marina': 5281,
    'sepang': 5543,
    'shanghai': 5451,
    'sochi': 5848,
    'valencia': 5419,
    'watkins glen': 5435,
    'zeltweg': 3200,
    # Add other tracks as needed
}

def get_user_input():
    try:
        year = int(input('Enter the year you want to access data for: '))
    except ValueError:
        print("That’s not a number, try again 😭")
        return

    gp = input("Enter the Grand Prix name (e.g., 'Monza') or type 'Testing' for test sessions: ").strip().lower()  # Convert to lowercase
    if gp == "testing":
        test_session()
        return

    session_type = input("Enter the session type (e.g., 'FP1', 'Qualifying', 'Race'): ").strip().capitalize()
    plot_choice = input("Do you want to generate a graph? (yes/no): ").strip().lower()

    graph_type = None
    driver = None
    if plot_choice == 'yes':
        graph_type = input("Choose graph type - 'Tyre Strategy' or 'Position During Race': ").strip().lower()
        driver = input("Enter the 3-letter driver code (e.g., VER, LEC, HAM): ").strip().upper()

    load_session(year, gp, session_type, driver, graph_type)

def load_session(year, gp, session_type, driver=None, graph_type=None):
    try:
        session = get_session(year, gp, session_type)
        session.load(laps=True, telemetry=True, weather=True, messages=True)
        print(f"\n🗓️  Session Loaded: {session.name}")
        print_basic_info(session, gp)

        if driver and graph_type:
            graph_type = graph_type.lower()
            if graph_type == 'tyre strategy':
                plot_tyre_strategy(session, driver)
            elif graph_type == 'position during race':
                plot_position(session, driver)
            else:
                print("Graph type not recognized 😬")

    except Exception as e:
        print(f"⚠️ Something went wrong: {e}")

def print_basic_info(session, gp):
    results = session.results
    results = results.sort_values('Position')

    print("\n🏆 Podium:")
    for i in range(3):
        pos = i + 1
        row = results.iloc[i]
        pos_label = f"{pos}st" if pos == 1 else f"{pos}nd" if pos == 2 else f"{pos}rd"
        driver_name = row['FullName']
        team = row['TeamName']
        print(f"{pos_label}: {driver_name} ({team})")

    # Fastest Lap
    laps = session.laps
    fastest_lap = laps.pick_fastest()
    fastest_driver = results[results['Abbreviation'] == fastest_lap['Driver']].iloc[0]
    print(f"\n⚡ Fastest Lap: {fastest_driver['FullName']} - {str(fastest_lap['LapTime']).split(' ')[-1][:-3]}")

    # Weather
    weather = session.weather_data.iloc[0]
    print(f"\n🌦️  Weather at race start: {weather['AirTemp']}°C, Track: {weather['TrackTemp']}°C, "
          f"Humidity: {weather['Humidity']}%, Rainfall: {weather['Rainfall']}")

    # Top Speed (optional)
    print_top_speed(session, gp)

def print_top_speed(session, gp):
    laps = session.laps.pick_fastest()  # Pick the fastest lap
    telemetry = laps.get_car_data().add_distance()  # Add the distance column
    max_speed = telemetry['Speed'].max()  # Find max speed
    max_speed_lap_distance = telemetry['Distance'][telemetry['Speed'].idxmax()]  # Distance at max speed

    # Get the track length from the dictionary
    track_length = TRACK_LENGTHS.get(gp, None)
    if track_length is None:
        print(f"⚠️ Track length for {gp} is not defined!")
        return

    # Calculate the lap number based on cumulative distance and track length
    lap_number = (max_speed_lap_distance // track_length) + 1  # We add 1 because lap numbers start at 1

    # Print Top Speed and approximate lap number
    print(f"\n🏎️ Top Speed: {max_speed} km/h at approximately lap {round(lap_number)}")

def plot_tyre_strategy(session, driver):
    driver_laps = session.laps.pick_driver(driver)
    stints = driver_laps[['Stint', 'Compound', 'LapNumber']].drop_duplicates()

    print("\n🛞 Tyre Strategy:")

    # Identify starting tyre, lap of change, and final tyre
    start_tyres = stints.iloc[0]
    start_tyres_info = f"Started with {start_tyres['Compound']} tyres on lap {start_tyres['LapNumber']}"

    change_info = []
    for i in range(1, len(stints)):
        if stints.iloc[i]['Stint'] != stints.iloc[i-1]['Stint']:  # A tyre change occurred
            change_info.append(f"Changed to {stints.iloc[i]['Compound']} on lap {stints.iloc[i]['LapNumber']}")

    final_tyre = stints.iloc[-1]
    end_info = f"Finished with {final_tyre['Compound']} tyres on lap {final_tyre['LapNumber']}"

    # Print summarized tyre strategy
    print(start_tyres_info)
    for change in change_info:
        print(change)
    print(end_info)

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
    plt.show()

def plot_position(session, driver):
    driver_laps = session.laps.pick_driver(driver).sort_values(by='LapNumber')
    lap_nums = driver_laps['LapNumber']
    positions = driver_laps['Position']

    plt.plot(lap_nums, positions, marker='o')
    plt.gca().invert_yaxis()  # Lower position = better
    plt.title(f"{driver} - Position During Race")
    plt.xlabel("Lap")
    plt.ylabel("Race Position")
    plt.grid(True)
    plt.show()

def test_session():
    print("Test session functionality isn't supported yet, chief 💀")

get_user_input()
