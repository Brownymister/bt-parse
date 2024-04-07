import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import csv
import numpy as np
import pandas as pd
import seaborn as sns
import json
# import read_csv_to_dicts from main
import main
import sys

file_path = sys.argv[1]


def read_csv_file(file_path):
    data = []
    with open(file_path, 'r', newline='') as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            if "  " in row[0]:
                continue
            data.append(row)

    return data[1:]


voting_data = read_csv_file(file_path)


def main():
    sns.set_theme()
    plot_voting_data(voting_data)
    plot_voting_data_overtime(voting_data, "Ja")
    plot_voting_data_overtime(voting_data, "Nein")
    plot_voting_data_overtime(voting_data, "Nicht abg.")


def plot_voting_data(voting_data):
    my_data = {}

    for u in voting_data:
        my_data[u[2]] = my_data.get(u[2], 0) + 1

    data = sorted(my_data.items(), key=lambda x: x[1])
    print(data)

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    plt.xticks(rotation=45)
    ax.bar([t[0] for t in data], [t[1] for t in data],
           width=1,
           edgecolor="white")
    plt.savefig("./output/voting_plot.png")


def plot_voting_data_overtime(voting_data, voting_behavior):
    all_votes = {}
    vote_behavior = {}

    for u in voting_data:
        date = u[0][6:10]
        all_votes[date] = all_votes.get(date, 0) + 1
        if u[2] == voting_behavior:
            vote_behavior[date] = vote_behavior.get(date, 0) + 1

    data = get_average_voting(vote_behavior, all_votes)

    data = sorted(data.items(), key=lambda x: x[0])
    print(data)

    fig, ax = plt.subplots()

    x = [t[0] for t in data]
    y = [t[1] for t in data]

    ax.plot(x, y, linewidth=2.0)

    ax.set(xlabel='Date',
           ylabel='Number of votes',
           title='Number of votes over time (' + str(voting_behavior) + ')')

    ax.tick_params(axis='x', labelrotation=45)

    plt.savefig("./output/voting_plot_overtime" + str(voting_behavior) +
                ".png")


"""
voting_behavior i.e = {"2023": 10, "2023": 20}
all_votes = {"2023": 20, "2023": 30}
"""


def get_average_voting(voting_behavior, all_votes):
    avg = {}

    for u in voting_behavior:
        avg[u] =  voting_behavior[u] / all_votes[u]

    return avg


if __name__ == "__main__":
    main()
