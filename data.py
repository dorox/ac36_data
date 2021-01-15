import pickle


def get_race(event, i):
    path = f"{event}/{i}"
    with open(f"{path}/stats.bin", "rb") as f:
        stats = pickle.load(f)
    with open(f"{path}/boats.bin", "rb") as f:
        b1 = pickle.load(f)
        b2 = pickle.load(f)
    return stats, (b1, b2)