import requests
import numpy as np
import json
import asyncio
from pyppeteer import launch
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

    filename = './output/output.csv'  # Replace with your CSV file name
    if os.path.exists(filename):
        parlament = read_csv_to_dicts(filename)
    else:
        url = "https://www.bundestag.de/static/appdata/sitzplan/data.json"

        # perfonm request
        r = requests.get(url)

        # parse
        json_str = r.json()
        # save
        for key, value in json_str.items():
            if key != "-1":
                print(key)
                value["job"], value["office"], value[
                    "socials"] = get_more_bio_info(value["href"])
                parlament.append(value)

        df = pd.DataFrame(parlament)
        df.to_csv('output.csv', index=False)

    for u in parlament:
        u["socials"] = json.loads(u["socials"].replace("'", "\""))

    if len(sys.argv) > 1:
        if sys.argv[1] == "--job":
            search_job(parlament, sys.argv[2])
        elif sys.argv[1] == "--debug":
            for i in parlament:
                if i["name"] == sys.argv[2]:
                    b = get_more_bio_info(i["href"])
                    v = asyncio.get_event_loop().run_until_complete(
                        get_voting_data(i["href"]))
                    # print(b)
                    print("date;title;vote")
                    for j in v:
                        print("{date};{title};{vote}".format(**j))

    else:
        plot_age_group(parlament)
        party_plot(parlament)
        plot_jobs(parlament)
        plot_gender_per_party(parlament)
        plot_job_per_party(parlament)
        plot_socials_by_field(
            parlament, "ageGroup",
            "Social Media Accounts (Prozentanteile) pro Altersgruppe im Bundestag (BtW 2021)"
        )
        plot_socials_by_field(
            parlament, "party",
            "Social Media Accounts (Prozentanteile) pro Fraktion im Bundestag (BtW 2021)"
        )
        plot_socials_by_field(parlament, "geschlecht")
        plot_socials_by_field(parlament, "federalState")
        filter_for_https(parlament)
        print(get_all_socials(parlament))


def get_more_bio_info(sub_url):
    url = "https://www.bundestag.de" + sub_url
    r = requests.get(url)
    t = r.text

    soup = BeautifulSoup(t, "lxml")
    dom = etree.HTML(str(soup))

    xpath_job = '/html/body/main/div[3]/div/div/div[1]/div[2]/div/p'
    job = dom.xpath(xpath_job)[0]

    xpath_office = '/html/body/main/div[3]/div/div/div[1]/div[5]/div/div[1]/p'
    office = dom.xpath(xpath_office)
    if len(office) == 0:
        office = ["not found"]
    else:
        office = [dom.xpath(xpath_office)[0].text]

    xpath_socials = '/html/body/main/div[3]/div/div/div[1]/div[5]/div/div[3]/ul/li'
    socials_elements = dom.xpath(xpath_socials)
    socials = []
    for social_element in socials_elements:
        socials.append({
            social_element.find("a").text.replace(" ", "").replace("\n", ""):
            social_element.find("a").get("href")
        })

    return (job.text, office[0], socials)


async def get_voting_data(sub_url):
    url = "https://www.bundestag.de" + sub_url + "?subview=na"
    # print(url)
    xpath_button = '/html/body/main/div[3]/div/div/div[2]/nav[1]/div/button[2]'

    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    # Your code here
    content = await page.content()
    elements = await page.xpath(xpath_button)
    # Do something with the elements, e.g., print the text content of the first element
    data_url = ""
    if elements:
        data_url = await page.evaluate(
            '(element) => element.getAttribute("data-url")', elements[0])
        # print(data_url)
        data_url = data_url[:-2]
    await browser.close()

    offset = 0

    voting_data = []

    while offset != -1:
        url = "https://www.bundestag.de" + data_url + str(offset)
        r = requests.get(url)
        t = r.text

        soup = BeautifulSoup(t, "html.parser")

        tr_elements = soup.find_all('tr')
        if len(tr_elements) <= 1:
            offset = -1
            break

        for tr in tr_elements:
            # Find all <td> elements inside the current <tr> element
            td_elements = tr.find_all('td')

            if len(td_elements) == 0:
                continue

            date = td_elements[0].find("p").text
            title = td_elements[1].find("p").text
            vote = td_elements[2].find("p").text
            my_voting_data = {}
            my_voting_data["date"] = date
            my_voting_data["title"] = title
            my_voting_data["vote"] = vote
            voting_data.append(my_voting_data)

        offset = offset + 10

    return voting_data


def search_job(parlament, job):
    # print as csv

    print(
        "name; job; party; geschlecht; ageGroup; federalState; img; direct; href; id; socials"
    )
    for u in parlament:
        if job in u["job"]:
            print(
                '{name};{job};{party};{geschlecht};{ageGroup};{federalState};{img};{direct};{href};{id};{socials}'
                .format(**u))


def plot_socials_by_field(parlament, group_name, title=""):
    age_groups = {}

    # order parlament by age
    parlament = sorted(parlament, key=lambda x: x["ageGroup"])

    for u in parlament:
        age = u[group_name]
        socials = u["socials"]
        for social in socials:
            age_groups[age] = age_groups.get(age, {})
            age_groups[age][list(social.keys())[0]] = age_groups[age].get(
                list(social.keys())[0], 0) + 1

    # percentage shares b
    for age in age_groups:
        total = 0
        for u in parlament:
            if u[group_name] == age:
                total += 1
        for social in age_groups[age]:
            age_groups[age][social] = (age_groups[age][social] / total) * 100

    homepage = [i.get("Homepage", 0) for i in [t for t in age_groups.values()]]
    facebook = [i.get("Facebook", 0) for i in [t for t in age_groups.values()]]
    x = [i.get("X", 0) for i in [t for t in age_groups.values()]]
    linkedin = [
        i.get("LinkedIn", 0) or i.get("Linkedin", 0)
        for i in [t for t in age_groups.values()]
    ]
    instagram = [
        i.get("Instagram", 0) for i in [t for t in age_groups.values()]
    ]
    youtube = [
        i.get("Youtube", 0) or i.get("Youtube", 0)
        for i in [t for t in age_groups.values()]
    ]
    tiktok = [
        i.get("TikTok", 0) or i.get("Tiktok", 0)
        for i in [t for t in age_groups.values()]
    ]

    data = {
        "Homepage": homepage,
        "Facebook": facebook,
        "X": x,
        "LinkedIn": linkedin,
        "Instagram": instagram,
        "Youtube": youtube,
        "TikTok": tiktok
    }

    fig, ax = plt.subplots()
    fig.set_size_inches(20, 10)
    plt.title(title)
    bar_plot(ax,
             data,
             list(age_groups.keys()),
             colors=[
                 "tab:green", "tab:olive", "tab:blue", "tab:cyan",
                 "tab:orange", "tab:red", "tab:purple"
             ])
    plt.savefig("./output/socials_by_" + group_name + ".png")


def get_all_socials(parlament):
    all_socials = {}
    for u in parlament:
        socials = u["socials"]
        for social in socials:
            all_socials[list(social.keys())[0]] = all_socials.get(
                list(social.keys())[0], 0) + 1

    return all_socials


def filter_for_https(parlament):
    protocolls = {}
    for u in parlament:
        if len(u["socials"]) == 0:
            continue

        homepage_url = ""
        for social in u["socials"]:
            if list(social.keys())[0] == "Homepage":
                homepage_url = list(social.values())[0]

        if homepage_url == "":
            continue

        homepage_protocol = homepage_url.split("://")[0]
        protocolls[homepage_protocol] = protocolls.get(homepage_protocol,
                                                       0) + 1

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 8)
    plt.xticks(rotation=45)
    ax.bar([t[0] for t in protocolls.items()],
           [t[1] for t in protocolls.items()],
           width=1,
           edgecolor="white")
    
    plt.title("Number of ssl uses on the homepages of members of parliament")
    plt.savefig("./output/protocolls_plot.png")


def bar_plot(ax,
             data,
             group_labels=None,
             colors=None,
             total_width=0.8,
             single_width=1,
             legend=True):
    if colors is None:
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    n_bars = len(data)
    bar_width = total_width / n_bars
    bars = []

    for i, (name, values) in enumerate(data.items()):
        x_offset = (i - n_bars / 2) * bar_width + bar_width / 2
        for x, y in enumerate(values):
            bar = ax.bar(x + x_offset,
                         y,
                         width=bar_width * single_width,
                         color=colors[i % len(colors)])
            # label=list(data.keys())[i])
        bars.append(bar[0])

    if legend:
        ax.legend(bars, data.keys())

    if group_labels:
        ax.set_xticks(range(len(group_labels)))
        ax.set_xticklabels(group_labels, rotation=90, ha='center')


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
    plt.savefig("./output/gender_plot.png")


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

    plt.savefig("./output/job_plot.png")


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

    plt.savefig("./output/age_plot.png")


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

    plt.savefig("./output/party_plot.png")


def read_csv_to_dicts(filename):
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    return data


if __name__ == "__main__":
    main()
