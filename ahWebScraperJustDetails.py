#! /user/bin/evn python3

import requests
from bs4 import BeautifulSoup
import pandas as pd
import html5lib
import glob
import argparse
import os

URL = 'https://srdata.nist.gov/xps/WagnerPlotData.aspx?Elm=Cu&Compound=Cu&PEline=2p3%2f2&Aline=L3M45M45(1G)'


def scrape(url_arg):
    fileName = "wagnerPlotData.xlsx"
    URL = url_arg
    detailURL = os.path.dirname(URL) + '/'
    with requests.Session() as s:
        
        s.headers.update({
            'user-agent': 'Mozilla/5.0'
        })

        if glob.glob(fileName):
            print(fileName + " already exists. Returning....")
            return

        pageCurrent = 1
        totalPages = 1
        soup = None
        results = None
        dataFrame = pd.DataFrame()
        detailLinks = []
        while pageCurrent <= totalPages:
            if pageCurrent == 1:
                page = s.get(URL)
            else:
                viewState = soup.find('input', {'id': '__VIEWSTATE'})['value']
                viewStateGenerator = soup.find(
                    'input', {'id': '__VIEWSTATEGENERATOR'})['value']
                validation = soup.find(
                    'input', {'id': '__EVENTVALIDATION'})['value']

                page = s.post(url=URL, data={
                    '__EVENTTARGET': 'ctl00$MainContentPlaceHolder$GridView1',
                    '__EVENTARGUMENT': 'Page$' + str(pageCurrent),
                    '__VIEWSTATE': viewState,
                    '__VIEWSTATEGENERATOR': viewStateGenerator,
                    '__EVENTVALIDATION': validation
                })
            soup = BeautifulSoup(page.content, 'lxml')
            results = soup.find(id='MainContentPlaceHolder_GridView1')
            

            if pageCurrent == 1:
                tempDataFrame = pd.read_html(io=str(results))[0]
                totalPages = len((tempDataFrame.iloc[-1:]).iat[0, 0])

            for link in results.find_all('a'):
                if not '__doPostBack' in link.get('href'):
                    detailLinks.append(link.get('href'))

            for i in range(len(detailLinks)):
                string = detailURL+detailLinks[i]
                detailPage = s.get(string.replace(' ', ''))
                detailSoup = BeautifulSoup(detailPage.content, 'lxml')
                for table in detailSoup.find_all('table'):
                    if table.has_attr('summary') and not table.has_attr('border'):
                        tempDataFrame = pd.read_html(io=str(table))[0]
                        tempDataFrame = tempDataFrame.drop(
                            [0, 7, 10, 21, 29, 35])
                        tempDataFrame.set_index(0,inplace=True)
                        dataFrame = dataFrame.append(tempDataFrame.T)
            pageCurrent += 1
        dataFrame.to_excel(fileName,index=False)
    


def main():
    parser = argparse.ArgumentParser(
        add_help=True, description='Add url to scrap for details')
    parser.add_argument('--scrape', nargs=1,
                        help='takes a url and converts gets the details')
    args = parser.parse_args()

    if args.scrape:
        URL = args.scrape[0]
        scrape(URL)
    else:
        print("Add argument")


if __name__ == '__main__':
    main()
