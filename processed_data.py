import os
import numpy as np
import json
import pickle

compress = False
events = ["acws2020", "prada2021", "ac2021"]
stats = {
    "heading": "headingIntep",
    "heel": "heelInterp",
    "pitch": "pitchInterp",
    "height": "elevInterp",
    "speed": "speedInterp",
    "tws": "twsInterp",
    "twd": "twdInterp",
    "port foil": "leftFoilPosition",
    "stbd foil": "rightFoilPosition",
    "both foils": "both foils",
    "vmg": "vmg",
    "twa": "twa",
    "twa_abs": "twa_abs",
    "vmg/tws": "tws/vmg",
}


def read_events(events):
    events_data = dict().fromkeys(events)
    for event in events:
        if event in os.listdir():
            events_data[event] = read_races(event)
    return events_data


def read_races(event):
    races = dict()
    for i in os.listdir(event):
        if "RacesList" in i:
            continue
        path = f"{event}/{i}"
        with open(f"{path}/stats.json", "rb") as f:
            race = json.load(f)
        races[str(i)] = race
        boats = read_boats(race, path)
        if compress:
            save_stats(race, path)
        return races, boats


def read_boats(race, path):
    if not "boat1.json" in os.listdir(path) and not "boat2.json" in os.listdir(path):
        raise FileNotFoundError
    with open(f"{path}/boat1.json", "rb") as f:
        boat1 = json.load(f)
    with open(f"{path}/boat2.json", "rb") as f:
        boat2 = json.load(f)
    if compress:
        boat1 = interpolate_boat(boat1, race)
        boat1 = interpolate_boat(boat2, race)
        save_boats((boat1, boat2), path)
    return boat1, boat2


def interpolate_boat(boat_data, race):
    boat = dict()
    x = stat("heading", boat_data)
    x = x["x"]
    x = np.linspace(int(x[0]), int(x[-1]), int(x[-1] - x[0]), dtype=int)
    for s in stats:
        data = stat(s, boat_data)
        y = np.interp(x, data["x"], data["y"])
        boat[s] = y
    race_start = boat_data["legInterp"]["valHistory"][1][1]
    boat["legs"] = np.array([i[1] for i in boat_data["legInterp"]["valHistory"]])
    boat["legs"] = np.array(boat["legs"] - race_start, dtype="timedelta64[s]")
    boat["x"] = np.array(x - race_start, dtype="timedelta64[s]")
    color, name = get_boat_info(boat_data, race)
    boat["color"] = color
    boat["name"] = name
    return boat


def save_boats(boats, path):
    with open(f"{path}/boats.bin", "wb") as f:
        for b in boats:
            pickle.dump(b, f)


def save_stats(race, path):
    with open(f"{path}/stats.bin", "wb") as f:
        pickle.dump(race, f)


def get_twa(boat):
    twd = stat("twd", boat)
    cog = stat("heading", boat)
    x = cog["x"]
    x = np.linspace(x[0], x[-1], int(x[-1] - x[0]))
    twd = np.interp(x, twd["x"], twd["y"])
    cog = np.interp(x, cog["x"], cog["y"])
    y = twd - cog
    y[y < 0] += 360
    y[y > 180] -= 360
    return dict(x=x, y=y)


# --------Returning individual properties--------


def get_twa_abs(boat):
    d = get_twa(boat)
    x = np.abs(d["x"])
    y = np.abs(d["y"])
    return dict(x=x, y=y)


def get_vmg(boat):
    twa = get_twa_abs(boat)
    sog = stat("speed", boat)
    x = twa["x"]
    x = np.linspace(x[0], x[-1], len(x))
    sog = np.interp(x, sog["x"], sog["y"])
    twa = twa["y"]
    y = np.cos(np.deg2rad(twa)) * sog
    legs = boat["legInterp"]["valHistory"]
    for i, leg in enumerate(legs[1:], 1):
        if not leg[0] % 2 and i != len(legs) - 1:
            mask = np.logical_and(x < legs[i + 1][1], x > legs[i][1])
            y[mask] *= -1
    return dict(x=x, y=y)


def get_both_foils(boat):
    stbd = stat("stbd foil", boat)
    port = stat("port foil", boat)
    x = np.concatenate((stbd["x"], port["x"]))
    y = np.concatenate((stbd["y"], port["y"]))
    return dict(x=x, y=y)


def get_vmgtws(boat):
    vmg = get_vmg(boat)
    tws = stat("tws", boat)
    tws = np.interp(vmg["x"], tws["x"], tws["y"])
    return dict(x=vmg["x"], y=vmg["y"] / tws)


def get_datetime(dic, boat):
    race_start = boat["legInterp"]["valHistory"][1][1]
    x = dic["x"]
    x = np.array(x - race_start, dtype="timedelta64[s]")
    return dict(x=x, y=dic["y"])


funcs = {
    "vmg": get_vmg,
    "twa": get_twa,
    "twa_abs": get_twa_abs,
    "both foils": get_both_foils,
    "vmg/tws": get_vmgtws,
}


def stat(key, boat):
    if key in funcs:
        return funcs[key](boat)
    unit = 1
    if key == "tws":
        unit = 1.94384
    s = boat[stats[key]]["valHistory"]
    s = np.array(s)
    x = s[:, 1]
    y = s[:, 0] * unit
    return dict(x=x, y=y)


def get_boat_info(b, race):
    if str(b["teamId"]) == race["LegStats"][0]["Boat"][0]["TeamID"]:
        c = race["LegStats"][0]["Boat"][0]["TeamColour"]
        n = race["LegStats"][0]["Boat"][0]["Country"]
    else:
        c = race["LegStats"][0]["Boat"][1]["TeamColour"]
        n = race["LegStats"][0]["Boat"][1]["Country"]
    return c, n


if __name__ == "__main__":
    compress = True
    read_events(events)