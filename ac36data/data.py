import pickle
import os

events = ["acws2020", "prada2021", "ac2021"]


def get_races(event):
    path = os.path.split(__file__)[0]
    path += f"/{event}"
    races = [i for i in os.listdir(path) if i not in "RaceData"]
    return sorted(races, key=int)


def get_boats(event, i):
    path = os.path.split(__file__)[0]
    path += f"/{event}/{i}"
    with open(f"{path}/boats.bin", "rb") as f:
        b1 = pickle.load(f)
        b2 = pickle.load(f)
    return b1, b2


def get_stats(event, i):
    path = os.path.split(__file__)[0]
    path += f"/{event}/{i}"
    with open(f"{path}/stats.bin", "rb") as f:
        stats = pickle.load(f)
    return stats