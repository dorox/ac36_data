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
        if event not in os.listdir("raw"):
            os.mkdir(f"raw/{event}")
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
            df = l
        if "RaceNameA" in l:
            read_race(l, df, event)


def read_race(l, df, event):
    # Downloads stats.json and binary race data

    race = re.findall(r"Race.*\d+", l)[0]
    n = re.findall(r"\d+", race)[0]
    race_path = f"raw/{event}/{n}"

    if n not in os.listdir(f"raw/{event}"):
        os.mkdir(race_path)

    file = df.split("=")[1].strip()

    if file not in os.listdir(race_path):
        r = requests.get(
            f"https://dx6j99ytnx80e.cloudfront.net/racedata/{event}/{file}"
        )
        with open(f"{race_path}/{file}", "wb") as f:
            f.write(r.content)

    if "stats.json" not in os.listdir(race_path):
        n = int(n)
        if event=='prada2021' and n>15:
            event_long = 'AC36_PradaCup_Final'
            n = n-15
        elif event=='prada2021' and 8<n<16:
            event_long = 'AC36_PradaCup_SemiFinal'
            n = n-9
        else:
            event_long = race_stats[event]
        r = requests.get(
            f"https://www.americascup.com/AC_Stats/{event_long}/Race_{n}.json"
        )
        with open(f"{race_path}/stats.json", "wb") as f:
            f.write(r.content)


if __name__ == "__main__":
    update_events(events)