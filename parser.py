import requests
from bs4 import *


def parse(name):
    url = 'https://w140.zona.plus/search/' + name
    response = requests.get(url)
    result = []
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('a')
    for div in divs:
        if div.get('class') == ['results-item']:
            result.append('https://w140.zona.plus' + div.get('href'))
    return result
