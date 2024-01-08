#!/usr/bin/env python3

import argparse
import multiprocessing
import re
import sys
from datetime import datetime
from typing import List, Iterable

import bs4
import pandas as pd
import requests
from bs4 import BeautifulSoup


def load_dates(fakulta: str) -> List[str]:
    url = 'https://is.muni.cz/studium/statistika'
    params = {
        'fakulta': fakulta
    }
    response = requests.get(url, params=params)
    html = response.text
    return scrape_dates(html)


def scrape_dates(html):
    soup = BeautifulSoup(html, 'html.parser')
    # noinspection PyTypeChecker
    select: Iterable[bs4.Tag] = soup.find('select', {'name': 'datv'}).children
    return [c['value'].replace(' ', '+') for c in select]


def load(fakulta: str, datum: str) -> pd.DataFrame:
    url = 'https://is.muni.cz/studium/statistika'
    params = {
        'fakulta': fakulta
    }
    data = {
        'fakulta': fakulta,
        'datv': datum,
        'tabv': '1',
        'zobraz': 'Zobrazit'
    }
    response = requests.post(url, params=params, data=data)
    df = scrape(response.text)
    df['date'] = datetime.strptime(datum, '%d+%m+%Y').strftime('%Y-%m-%d')
    return df


def scrape(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, 'html.parser')
    semesters = scrape_semesters(soup)
    return scrape_programs(semesters, soup)


def scrape_semesters(soup: BeautifulSoup):
    semesters = []
    for s in soup.find_all('tr', {'bgcolor': '#dadada'})[1].children:
        semesters.append(s.text)
    for e in soup.find_all('tr', {'bgcolor': '#dadada'}):
        e.decompose()
    return semesters


def scrape_programs(semesters, soup):
    bs_rows = soup.find('table', {'class': 'data1'}).find_all('tr', recursive=False)

    rows = []
    curr_program = None
    for bs_row in bs_rows:
        cols = [col.text.strip() for col in bs_row.children]
        (program, obor, smer), sem_cols = cols[:3], cols[3:]

        if program:
            curr_program = program
            continue

        row = {'program': curr_program, 'obor': obor}
        for i in range(len(semesters)):
            row['sem_' + semesters[i]] = cols[i + 3]
        rows.append(row)

    return pd.DataFrame(rows)


def load_to_df(fakulta: str):
    dates = load_dates(fakulta)[1:]
    with multiprocessing.Pool() as pool:
        dfs = list(pool.map(load_mp, [(fakulta, datum) for datum in dates]))
    df = pd.concat(dfs, ignore_index=True)
    df = df.reindex(sorted(df.columns, key=natural_keys), axis=1)
    return df


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def load_mp(args) -> pd.DataFrame:
    fakulta, datum = args
    return load(fakulta, datum)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('FACULTY_CODE', help="Numerical faculty code")
    args = parser.parse_args()
    df = load_to_df(args.FACULTY_CODE)
    df.to_csv(sys.stdout, index=False)


if __name__ == '__main__':
    main()
