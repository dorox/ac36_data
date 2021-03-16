import os
import numpy as np
import json
import pickle
import struct
from datetime import datetime
from collections import namedtuple
from pyproj import CRS, Transformer

compress = False
events = ["acws2020", "prada2021", "ac2021"]
stats = {
    "heading": "headingIntep",
    "heel": "heelInterp",
    "pitch": "pitchInterp",
    "speed": "speedInterp",
    "tws": "twsInterp",
    "twd": "twdInterp",
    "port foil": "leftFoilPosition",
    "stbd foil": "rightFoilPosition",
    "both foils": "both foils",
    "vmg": "vmg",
    "cvmg": "cvmg",
    "twa": "twa",
    "twa_abs": "twa_abs",
    "vmg/tws": "tws/vmg",
}
Packets = namedtuple(
    "packet_ids",
    "boat penalty course_info course_boundary wind windpoint buoy roundingtime audio stats",
)
Course_info = namedtuple(
    "course_Info",
    "raceId startTime numLegs courseAngle raceStatus boattype liveDelaySecs",
)

packets_id = Packets(179, 182, 177, 185, 178, 190, 181, 180, 186, 183)

with open("raw/yt_videos.json", "rb") as f:
    yt_videos = json.load(f)
with open("raw/yt_video_offsets.json", "rb") as f:
    yt_offsets = json.load(f)


def read_videos(date):
    selected = dict()
    for yt_title, v in yt_videos.items():
        yt_id = v["contentDetails"]["videoId"]
        yt_date = v["contentDetails"]["videoPublishedAt"]
        yt_date = yt_date.replace("Z", "+00:00")
        yt_date = datetime.fromisoformat(yt_date)
        if yt_date.date() == date.date():
            if yt_id not in yt_offsets:
                continue
            if "Port Entry" in yt_title:
                selected["PRT"] = v["contentDetails"]
                selected["PRT"]["offset"] = yt_offsets[yt_id]
            elif "Starboard Entry" in yt_title:
                selected["STBD"] = v["contentDetails"]
                selected["STBD"]["offset"] = yt_offsets[yt_id]
            elif (
                "Full Race" in yt_title
                or "The 36th America’s Cup Presented by PRADA | 🔴 LIVE Day" in yt_title
                or "🔴 LIVE Day" in yt_title
                or "🔴LIVE Day" in yt_title
                and not "Eye" in yt_title
            ):
                selected["TV"] = v["contentDetails"]
                selected["TV"]["offset"] = yt_offsets[yt_id]
    return selected


def read_packets(path):
    with open(path, "rb") as f:
        b = bytearray(f.read()).split(b"\x10\x03\x10")
    data = {i: [] for i in packets_id}
    packets = []
    for i, p in enumerate(b):
        packets.append(p)
        if p[0] == packets_id.course_info:
            data[p[0]].append(read_course_info(p))
        # elif p[0] == packets_id.course_boundary:
        #     data[p[0]].append(read_course_boundary(p))
    return data, packets


def get_course_info(path):
    for file in os.listdir(f"raw/{path}"):
        if file.endswith(".bin"):
            path_bin = f"raw/{path}/{file}"
    data, packets = read_packets(path_bin)
    d = data[packets_id.course_info][-1]
    return dict(zip(d._fields, d))


def read_course_info(p):
    p_id = p[0]
    n = p[1]
    p = p[2:]
    return Course_info(*struct.unpack("!HIBHBBB", p))


def read_course_boundary(p):
    data = struct.unpack(f"!BBHIB{p[8]*2}I", p)
    # 16 repeats increasing the n of bytes
    points = [(i - 2147483648) / 1e7 for i in data[5:]]
    points = zip(points[0::2], points[1::2])
    # data = Course_boundary(*data[2:5], tuple(points))
    return data


def read_events(events):
    events_data = dict().fromkeys(events)
    for event in events:
        print(f"Reading event {event}")
        if event in os.listdir("raw"):
            events_data[event] = read_races(event)
    return events_data


def read_races(event):
    races = dict()
    for i in os.listdir(f"raw/{event}"):
        print(f"Reading race {i}")
        if "RacesList" in i:
            continue
        path = f"{event}/{i}"
        if "stats.json" not in os.listdir(f"raw/{path}"):
            raise FileNotFoundError(f"{path}/stats.json not found")
        races[str(i)] = read_race(i, event)
    return races


def read_race(i, event):
    path = f"{event}/{i}"
    with open(f"raw/{path}/stats.json", "rb") as f:
        race = json.load(f)
    boats = read_boats(race, f"raw/{path}")
    race["course_info"] = get_course_info(path)
    date = datetime.fromtimestamp(race["course_info"]["startTime"])
    race["course_info"]["startTime"] = date.hour * 3600 + date.minute * 60 + date.second
    race["yt_videos"] = read_videos(date)
    race_no = int(i)

    def get_dt(race_no, this_date, dt=0):
        if race_no == 1:
            return 0
        elif os.path.exists(f"raw/{event}/{race_no-1}"):
            prev_race = get_course_info(f"{event}/{race_no-1}")
            prev_date = datetime.fromtimestamp(prev_race["startTime"])
            if prev_date.date() == this_date.date():
                dt += this_date.timestamp() - prev_date.timestamp()
                dt += get_dt(race_no - 1, prev_date)
                return dt
            else:
                return 0
        else:
            return 0

    dt = get_dt(race_no, date)
    print(f"race {i}, dt {dt}")
    for k in race["yt_videos"]:
        race["yt_videos"][k]["offset"] += dt
    if compress:
        b1 = interpolate_boat(boats[0], race)
        b2 = interpolate_boat(boats[1], race)
        save_stats(race, path)
        save_boats((b1, b2), path)
    return race


def read_boats(race, path):
    print("Reading boats")
    if not "boat1.json" in os.listdir(path) and not "boat2.json" in os.listdir(path):
        raise FileNotFoundError
    with open(f"{path}/boat1.json", "rb") as f:
        boat1 = json.load(f)
    with open(f"{path}/boat2.json", "rb") as f:
        boat2 = json.load(f)
    return boat1, boat2


def interpolate_boat(boat_data, race):
    boat = dict()
    x = stat("heading", boat_data, race)
    x = x["x"]
    x = np.linspace(x[0], x[-1], int(x[-1] - x[0]) * 2)
    for s in stats:
        data = stat(s, boat_data, race)
        y = np.interp(x, data["x"], data["y"])
        boat[s] = y
    # ----coordinates----
    # UTM zone 60S
    crs_utm = CRS.from_epsg(27260)
    # Web mercator
    crs_wm = CRS.from_epsg(3857)
    tr = Transformer.from_crs(crs_utm, crs_wm)
    lon_y_raw = [i[0] for i in boat_data["coordIntep"]["xCerp"]["valHistory"]]
    lat_y_raw = [i[0] for i in boat_data["coordIntep"]["yCerp"]["valHistory"]]
    boat_data["lon"] = []
    boat_data["lat"] = []
    boat_data["lonx"] = [i[1] for i in boat_data["coordIntep"]["xCerp"]["valHistory"]]
    boat_data["latx"] = [i[1] for i in boat_data["coordIntep"]["yCerp"]["valHistory"]]
    for i, (lon, lat) in enumerate(zip(lon_y_raw, lat_y_raw)):
        lon, lat = tr.transform(lon, lat)
        boat_data["lon"].append(lon)
        boat_data["lat"].append(lat)
    boat["lon"] = np.interp(x, boat_data["lonx"], boat_data["lon"])
    boat["lat"] = np.interp(x, boat_data["latx"], boat_data["lat"])
    # ----end of coord interp-----
    race_start = boat_data["legInterp"]["valHistory"][1][1] * 1000
    boat["legs"] = np.array([i[1] for i in boat_data["legInterp"]["valHistory"]])
    boat["legs"] = np.array(boat["legs"] * 1000, dtype="timedelta64[ms]")
    boat["x"] = np.array(x * 1000, dtype="timedelta64[ms]")
    color, name = get_boat_info(boat_data, race)
    boat["color"] = color
    boat["name"] = name
    return boat


def save_boats(boats, path):
    path = "ac36data/" + path
    # if path not in os.listdir():
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    with open(f"{path}/boats.bin", "wb") as f:
        for b in boats:
            pickle.dump(b, f)


def save_stats(race, path):
    path = "ac36data/" + path
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    with open(f"{path}/stats.bin", "wb") as f:
        pickle.dump(race, f)


# --------Returning individual properties--------


def get_twa(boat, race):
    twd = stat("twd", boat, race)
    cog = stat("heading", boat, race)
    x = cog["x"]
    x = np.linspace(x[0], x[-1], int(x[-1] - x[0]))
    twd = np.interp(x, twd["x"], twd["y"])
    cog = np.interp(x, cog["x"], cog["y"])
    y = twd - cog
    y[y < 0] += 360
    y[y > 180] -= 360
    return dict(x=x, y=y)


def get_twa_abs(boat, race):
    d = get_twa(boat, race)
    x = np.abs(d["x"])
    y = np.abs(d["y"])
    return dict(x=x, y=y)


def get_vmg(boat, race):
    twa = get_twa_abs(boat, race)
    sog = stat("speed", boat, race)
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


def get_cvmg(boat, race):
    # VMG to course axis
    course_axis = race["course_info"]["courseAngle"]
    sog = stat("speed", boat, race)
    y = np.cos(np.deg2rad(course_axis)) * sog["y"]
    x = sog["x"]
    legs = boat["legInterp"]["valHistory"]
    for i, leg in enumerate(legs[1:], 1):
        if not leg[0] % 2 and i != len(legs) - 1:
            mask = np.logical_and(x < legs[i + 1][1], x > legs[i][1])
            y[mask] *= -1
    return dict(x=x, y=y)


def get_both_foils(boat, race):
    stbd = stat("stbd foil", boat, race)
    port = stat("port foil", boat, race)
    x = np.concatenate((stbd["x"], port["x"]))
    y = np.concatenate((stbd["y"], port["y"]))
    return dict(x=x, y=y)


def get_vmgtws(boat, race):
    vmg = get_vmg(boat, race)
    tws = stat("tws", boat, race)
    tws = np.interp(vmg["x"], tws["x"], tws["y"])
    return dict(x=vmg["x"], y=vmg["y"] / tws)


def get_datetime(dic, boat, race):
    race_start = boat["legInterp"]["valHistory"][1][1]
    x = dic["x"]
    x = np.array(x - race_start, dtype="timedelta64[s]")
    return dict(x=x, y=dic["y"])


funcs = {
    "vmg": get_vmg,
    "cvmg": get_cvmg,
    "twa": get_twa,
    "twa_abs": get_twa_abs,
    "both foils": get_both_foils,
    "vmg/tws": get_vmgtws,
}


def stat(key, boat, race):
    if key in funcs:
        return funcs[key](boat, race)
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
