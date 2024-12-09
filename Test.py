import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
year = int(input("Enter a Valid Year:"))
race_number = int(input("Enter a Valid Race Number of that year:"))
session_type = input("Enter a Valid Session ID:")
session = fastf1.get_session(year, race_number, session_type)
session.load()
laps = session.laps
drivers = session.drivers
session.load(telemetry=False, weather=False)
fig, ax = plt.subplots(figsize=(8.0, 4.9))
for drv in session.drivers:
    drv_laps = session.laps.pick_driver(drv)

    abb = drv_laps['Driver'].iloc[0]
    style = fastf1.plotting.get_driver_style(identifier=abb,
                                            style=['color', 'linestyle'],
                                            session=session)

    ax.plot(drv_laps['LapNumber'], drv_laps['Position'],
            label=abb, **style)
ax.set_ylim([20.5, 0.5])
ax.set_yticks([1, 5, 10, 15, 20])
ax.set_xlabel('Lap')
ax.set_ylabel('Position')
ax.legend(bbox_to_anchor=(1.0, 1.02))
plt.tight_layout()

plt.show()