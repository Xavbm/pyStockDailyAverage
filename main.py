#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sched, time
import requests 
from rgbDict import rgb_dict
from stockAndQuantity import stock_quantity_dict

SERVER_LED_URL = "http://192.168.1.66/all/color?color="

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
YAHOO_URL = "https://finance.yahoo.com/quote/{}?p={}"

total_by_stock = []
weights = []

def __compute_weights():
    print("Start computing weights")
    for key, value in stock_quantity_dict.items():

        # anchor to know where to start looking to get previous close value
        anchor = 'Previous Close'
        
        # Get html text
        html = requests.get(YAHOO_URL.format(key, key), headers=HEADERS).text
        soup = BeautifulSoup(html, 'html.parser')
        soup_text = soup.get_text()

        # Set index after anchor
        anchor_index = soup_text.find(anchor)

        # Trim text after anchor to reduce text and only have one ( to find
        trimmed_text = soup_text[anchor_index + 14 : anchor_index + 21]

        # Find ( to get start of percentage
        end_index = trimmed_text.find('O')

        if end_index != -1:
            trimmed_text = trimmed_text[:end_index]

        stock_price = trimmed_text
        print(stock_price)

        total_by_stock.append(float(stock_price) * value)
        
    total = sum(total_by_stock)

    for i in range(len(stock_quantity_dict)):
        weights.append(total_by_stock[i]/total)

    print(weights)
    print("Finish computing weights")

## START LOOP FOR EACH STOCK
def __compute_values():
    total_value = 0.00
    total = 0.00

    for stock in stock_quantity_dict.keys():

        # anchor to know where to start looking to get current value
        anchor = 'Add to watchlist'
        
        # Get html text
        html = requests.get(YAHOO_URL.format(stock, stock), headers=HEADERS).text
        soup = BeautifulSoup(html, 'html.parser')
        soup_text = soup.get_text()

        # Set index after anchor
        anchor_index = soup_text.find(anchor)

        # Trim text after anchor to reduce text and only have one ( to find
        trimmed_text = soup_text[anchor_index + 16 : anchor_index + 40]

        # Find ( to get start of percentage
        percentageStartIndex = trimmed_text.find('(') 

        # Get percentage value
        percentage = trimmed_text[percentageStartIndex + 1 : percentageStartIndex + 7]

        # Remove ) if present when 0.00%
        if percentage[-1:] == ')':
            percentage = percentage[:-1]

        # Remove % if present
        if percentage[-1:] == '%':
            percentage = percentage[:-1]

        # Let crash and restart container
        value = float(percentage)* weights[stock.index(stock)]

        print("{:9}".format(stock) + "{:.2f}".format(value))

        # Round 0 to keep 2 decimals
        if value == 0.0:
            value = round(value, 3)

        total_value = total_value + value
        total = total_value

    # Round to 0.5 
    total_value = round(total_value * 2) / 2

    # Adapt value if out of dictionary's keys
    if total_value > 5.00:
        total_value = 5.00
    elif total_value < -5.00:
        total_value = -5.00

    rgb = rgb_dict[total_value]
    
    requests.post(url = SERVER_LED_URL + rgb)

    print("{:9}".format("Total") + "{:.2f}".format(total))

## END LOOP FOR EACH STOCK
print("Hello, welcome to the stock fetcher!")
__compute_weights()

print("Start rolling")
s = sched.scheduler(time.time, time.sleep)
def run_main_loop(sc): 
    print("Enter chronos")
    __compute_values()
    s.enter(30, 1, run_main_loop, (sc,))

s.enter(1, 1, run_main_loop, (s,))
s.run()