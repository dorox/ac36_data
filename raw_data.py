import os
import requests
import re
import json
import pyyoutube

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
        if event == "prada2021" and n > 15:
            event_long = "AC36_PradaCup_Final"
            n = n - 16
        elif event == "prada2021" and 8 < n < 16:
            event_long = "AC36_PradaCup_SemiFinal"
            n = n - 9
        else:
            event_long = race_stats[event]
        r = requests.get(
            f"https://www.americascup.com/AC_Stats/{event_long}/Race_{n}.json"
        )
        with open(f"{race_path}/stats.json", "wb") as f:
            f.write(r.content)


def update_youtube():
    api = pyyoutube.Api(api_key="AIzaSyARgDd1Uj4u6ayc4zTWI58WjfRwASlj5nY")
    all_videos = api.get_playlist_items(
        playlist_id="UUo15ZYO_XDRU9LI30OPtxAg", count=None
    )
    data = dict()
    for video in all_videos.items:
        video = video.to_dict()
        snippet = video["snippet"]
        title = snippet["title"]
        if "Entry Stern" in title or "Full Race" in title:
            data[title] = video
    with open("raw/yt_videos.json", "w") as f:
        f.write(json.dumps(data))


if __name__ == "__main__":
    update_events(events)
    update_youtube()