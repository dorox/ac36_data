import os
import requests
import re

events = ["acws2020", "prada2021", "ac2021"]
race_stats = {
    "acws2020": "AC36_ACWS_Auckland",
    "prada2021": "AC36_PradaCup_RoundRobins",
    "ac2021": None,
}


def update_events(events):
    for event in events:
        if event not in os.listdir():
            os.mkdir(event)
        update_event(event)


def update_event(event):
    path = f"raw/{event}/"
    r = requests.get(
        f"https://dx6j99ytnx80e.cloudfront.net/racedata/{event}/RacesList.dat"
    )
    with open(path + "RacesList.dat", "wb") as f:
        f.write(r.content)
    for l in r.text.splitlines():
        if "DataFile" in l:
            read_race(l, event)


def read_race(l, event):
    # Downloads stats.json and binary race data

    race = re.findall(r"Race_\d+", l)[0]
    n = re.findall(r"\d+", race)[0]
    race_path = f"raw/{event}/{n}"

    if n not in os.listdir(f"raw/{event}"):
        os.mkdir(race_path)

    file = l.split("=")[1].strip()

    if file not in os.listdir(race_path):
        r = requests.get(
            f"https://dx6j99ytnx80e.cloudfront.net/racedata/{event}/{file}"
        )
        with open(f"{race_path}/{file}", "wb") as f:
            f.write(r.content)

    if "stats.json" not in os.listdir(race_path):
        r = requests.get(
            f"https://www.americascup.com/AC_Stats/{race_stats[event]}/Race_{n}.json"
        )
        with open(f"{race_path}/stats.json", "wb") as f:
            f.write(r.content)


if __name__ == "__main__":
    update_events(events)