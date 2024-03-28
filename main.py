import requests
import numpy as np
import pandas as pd
import sys
import csv
from bs4 import BeautifulSoup
from lxml import etree
import matplotlib.pyplot as plt
import seaborn as sns
import os.path


def main():
    # sns.pairplot(df, hue="species")
    sns.set_theme()
    parlament = []

    filename = 'output.csv'  # Replace with your CSV file name
    if os.path.exists(filename):
        parlament = read_csv_to_dicts(filename)
    else:
        url = "https://www.bundestag.de/static/appdata/sitzplan/data.json"

        # perfonm request
        r = requests.get(url)

        # parse
        json = r.json()
        # save
        for key, value in json.items():
            if key != "-1":
                print(key)
                value["job"], value["office"] = get_more_bio_info(
                    value["href"])
                parlament.append(value)

        df = pd.DataFrame(parlament)
        df.to_csv('output.csv', index=False)

    if len(sys.argv) > 1 and sys.argv[1] == "--job":
        search_job(parlament, sys.argv[2])
    else:
        plot_age_group(parlament)
        party_plot(parlament)
        plot_jobs(parlament)
        plot_gender_per_party(parlament)
        plot_job_per_party(parlament)


def get_more_bio_info(sub_url):
    url = "https://www.bundestag.de" + sub_url
    r = requests.get(url)
    t = r.text

    soup = BeautifulSoup(t, "lxml")
    dom = etree.HTML(str(soup))

    xpath_job = '/html/body/main/div[3]/div/div/div[1]/div[2]/div/p'
    job = dom.xpath(xpath_job)[0]

    xpath_office = '/html/body/main/div[3]/div/div/div[1]/div[5]/div/div[1]/p[1]'
    office = dom.xpath(xpath_office)
    if len(office) == 0:
        office = ["not found"]

    return (job.text, office[0])


def search_job(parlament, job):
    # print as csv

    print(
        "name; job; party; geschlecht; ageGroup; federalState; img; direct; href; id"
    )
    for u in parlament:
        if job in u["job"]:
            print(
                '{name};{job};{party};{geschlecht};{ageGroup};{federalState};{img};{direct};{href};{id}'
                .format(**u))


def plot_job_per_party(parlament):
    parties = {}

    for u in parlament:
        job = u["job"].replace("ä", "a")
        last_two_letters = job[-2:]
        if last_two_letters == "in":
            job = job[:-2]
        party = u["party"]
        parties[party] = parties.get(party, {})
        parties[party][job] = parties[party].get(job, 0) + 1

    # delet irrelevant data (jobs that only occur once)
    new_parties = {}
    for party in parties:
        for job in parties[party]:
            if parties[party][job] > 1:
                new_parties[party] = new_parties.get(party, {})
                new_parties[party][job] = parties[party][job]
    # sort data by number of occurences
    for party in new_parties:
        new_parties[party] = sorted(new_parties[party].items(),
                                    key=lambda x: x[1],
                                    reverse=True)

    print(new_parties)


def plot_gender_per_party(parlament):
    parties = {}

    for u in parlament:
        gender = u["geschlecht"]
        party = u["party"]
        parties[party] = parties.get(party, {})
        parties[party][gender] = parties[party].get(gender, 0) + 1

    # print(parties)

    barWidth = 0.35

    men = [i["männlich"] for i in [t for t in parties.values()]]
    women = [i["weiblich"] for i in [t for t in parties.values()]]

    bars1 = men
    bars2 = women

    r1 = np.arange(len(bars1))
    r2 = [x + barWidth for x in r1]

    # Create plot
    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    # Make the plot
    plt.bar(r1,
            bars1,
            color='purple',
            width=barWidth,
            edgecolor='white',
            label='männlich')
    plt.bar(r2,
            bars2,
            color='green',
            width=barWidth,
            edgecolor='white',
            label='weiblich')

    # Add xticks on the middle of the group bars
    # plt.xlabel('group', fontweight='bold')
    plt.xticks(rotation=90)
    plt.xticks([r + barWidth / 2 for r in range(len(bars1))],
               [t for t in parties.keys()])

    # Create legend & Show graphic
    plt.legend()
    plt.savefig("gender_plot.png")


def plot_jobs(parlament):
    jobs = {}

    for u in parlament:
        group = u["job"].replace("ä", "a")
        last_two_letters = group[-2:]
        if last_two_letters == "in":
            group = group[:-2]
        jobs[group] = jobs.get(group, 0) + 1

    jobs = sorted(jobs.items(), key=lambda x: x[1])
    sorted_jobs = []
    other = 0
    for key, value in jobs:
        if value < 10:
            other += value
        else:
            sorted_jobs.append((key, value))

    sorted_jobs.append(("andere", other))
    print(sorted_jobs)

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    plt.xticks(rotation=90)
    ax.bar([t[0] for t in sorted_jobs], [t[1] for t in sorted_jobs],
           width=1,
           edgecolor="white")

    plt.savefig("job_plot.png")


def plot_age_group(parlament):
    ageGroup = {}

    for u in parlament:
        group = u["ageGroup"]
        ageGroup[group] = ageGroup.get(group, 0) + 1

    ageGroup = sorted(ageGroup.items(), key=lambda x: x[0])
    print(ageGroup)

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    plt.xticks(rotation=45)
    ax.bar([t[0] for t in ageGroup], [t[1] for t in ageGroup],
           width=1,
           edgecolor="white")

    plt.savefig("age_plot.png")


def party_plot(parlament):
    parties = {}

    for u in parlament:
        group = u["party"].replace("Jahre", "")
        parties[group] = parties.get(group, 0) + 1

    parties = sorted(parties.items(), key=lambda x: x[1])
    print(parties)

    colorMatch = {
        "CDU/CSU": "black",
        "Gruppe Die Linke": "magenta",
        "Gruppe BSW": "orange",
        "Bündnis 90/Die Grünen": "green",
        "FDP": "yellow",
        "SPD": "red",
        "AfD": "blue",
        "fraktionslos": "grey"
    }

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    plt.xticks(rotation=45)

    color = [colorMatch[t[0]] for t in parties]

    ax.bar([t[0] for t in parties], [t[1] for t in parties],
           width=1,
           edgecolor="white",
           color=color)
    # linewidth=0.7)

    plt.savefig("party_plot.png")


def read_csv_to_dicts(filename):
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    return data


if __name__ == "__main__":
    main()
