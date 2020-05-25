from flask import Flask, request, jsonify
import yfinance as yf
import requests
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
import json

app = Flask(__name__)
app.config["DEBUG"] = True

error = {
    "errorCode": -1,
    "errorDesc": ""
}


@app.route('/')
def index():
    return 'this is Flask'


@app.route('/yf', methods=['GET'])
def get_yf_data():

    if 'symbol' in request.args:
        symbol = request.args['symbol']
    else:
        return "Error: No symbol provided. Please specify symbol."

    ticker = yf.Ticker(symbol)

    print(ticker.info)
    ticker_dict = ticker.info
    return ticker_dict


@app.route('/is')
def get_incomestatement():
    if 'symbol' in request.args:
        symbol = request.args['symbol']
    else:
        return "Error: No symbol provided. Please specify symbol."

    incsta_list = requests.get('https://financialmodelingprep.com/api/v3/income-statement/'+symbol+'?apikey=0ee048fea75d0f7205b64b8bb6723608')
    return incsta_list[0]


@app.route('/info', methods=['GET'])
def get_info():

    if 'symbol' in request.args:
        symbol = request.args['symbol']

        if symbol_check(symbol):
            symbol = symbol.upper()
            value_dict = {
                          'ticker': symbol,
                          'price': get_curr_price(symbol),
                          'dividendInfo': get_dividend_info(symbol)[0],
                          'companyName': get_dividend_info(symbol)[1]['companyName'],
                          'peRatio': get_dividend_info(symbol)[1]['peRatio'],
                          'earningsPerShare': get_dividend_info(symbol)[1]['earningsPerShare'],
                          'balanceSheetInfo': get_balancesheet(symbol)
                          }
            return value_dict
        else:
            return error_message(100, 'Symbol cannot be empty')
    else:
        return error_message(100, 'Symbol cannot be empty')


def get_dividend_info(symbol):
    if symbol_check(symbol):
        ticker = yf.Ticker(symbol)
        print(type(ticker.actions))
        ticker_dict = ticker.info
        dividend_info = {
            'dividend': ticker_dict['dividendRate'],
            'divYield': "{:.2%}".format(ticker_dict['dividendYield']),
            'fiveYearAvgDivYield': str(ticker_dict['fiveYearAvgDividendYield']) + '%',
            'payoutRatio': "{:.2%}".format(ticker_dict['payoutRatio'])
        }
        general_info = {
            'companyName': ticker_dict['shortName'],
            'peRatio': "{:.2f}".format(ticker_dict['trailingPE']),
            'earningsPerShare': "{:.2f}".format(ticker_dict['trailingEps'])
        }

        return [dividend_info, general_info]
    else:
        return -1


def get_curr_price(symbol):
    if symbol_check(symbol):
        api_resp_dict = requests.get(
            'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + symbol + '&apikey=6RMZ8WSEVBLUP511').json()
        return "{:0,.2f}".format(float(api_resp_dict['Global Quote']['05. price']))
    else:
        return -1


@app.route('/bs')
def get_balancesheet(symbol):
    if symbol_check(symbol):
        balance_sheet_list = requests.get(
            'https://financialmodelingprep.com/api/v3/balance-sheet-statement/' + symbol + '?apikey=0ee048fea75d0f7205b64b8bb6723608').json()

        current_asset_to_liab_ratio = balance_sheet_list[0]['totalCurrentAssets'] / balance_sheet_list[0]['totalCurrentLiabilities']
        total_asset_to_liab_ratio = balance_sheet_list[0]['totalAssets'] / balance_sheet_list[0]['totalLiabilities']

        sum_total_asset_to_liab_history = 0
        past_five_year_list = balance_sheet_list[1:6]
        for bs in past_five_year_list:
            sum_total_asset_to_liab_history += bs['totalAssets']/bs['totalLiabilities']

        avg_total_asset_to_liab = sum_total_asset_to_liab_history / 5
        balance_sheet_info = {
            "currentAssetToLiabRatio": "{:.2f}".format(current_asset_to_liab_ratio),
            "totalAssetToLiabRatio": "{:.2f}".format(total_asset_to_liab_ratio),
            "past5YearAvgAssetToLiabRatio": "{:.2f}".format(avg_total_asset_to_liab)
        }
        # totalCurrentAssets
        # totalCurrentLiabilities
        # totalAssets
        # totalLiabilities
        return balance_sheet_info
    else:
        return -1


def symbol_check(symbol):
    symbol_validation = False if (symbol is None or not symbol) else True
    return symbol_validation


def error_message(code, desc):
    error['errorCode'] = 100
    error['errorDesc'] = 'Symbol cannot be empty'
    return error


app.run()
