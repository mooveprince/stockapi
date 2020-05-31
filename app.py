from flask import Flask, request, jsonify
import yfinance as yf
import requests
import configparser

app = Flask(__name__)
app.config["DEBUG"] = True

FINANCE_MODEL_URL = 'https://financialmodelingprep.com/api/v3'

config = configparser.RawConfigParser()
config.read('config.properties')
details_dict = dict(config.items('ENV_VARIABLE'))
API_KEY = '?apikey='+details_dict['api_key']
API_CALL = details_dict['api_call']

print(API_KEY)
print(API_CALL)

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


@app.route('/info', methods=['GET'])
def get_info():

    if 'symbol' in request.args:
        symbol = request.args['symbol']

        if symbol_check(symbol):
            symbol = symbol.upper()
            value_dict = {
                          'ticker': symbol,
                          'price': get_general_info(symbol)['price'],
                          'companyName': get_general_info(symbol)['companyName'],
                          'peRatio': get_general_info(symbol)['peRatio'],
                          'earningsPerShare': get_general_info(symbol)['earningsPerShare'],
                          'dividendInfo': get_dividend_info(symbol),
                          'balanceSheetInfo': get_balance_sheet_info(symbol),
                          'incomeSheetInfo': get_income_sheet_info(symbol),
                          'cashFlowInfo': get_cash_flow_info(symbol)
                          }
            return value_dict
        else:
            return error_message(100, 'Symbol cannot be empty')
    else:
        return error_message(100, 'Symbol cannot be empty')

def get_general_info(symbol):
    general_info = {
        'companyName': 'NA',
        'peRatio': 'NA',
        'price': 'NA',
        'earningsPerShare': 'NA'
    }
    if symbol_check(symbol) and API_CALL:
        general_info_list = requests.get(FINANCE_MODEL_URL+'/quote/'+symbol+API_KEY).json()
        if general_info_list.get('Error Message') is None:
            general_info['companyName'] = general_info_list[0]['name']
            general_info['peRatio'] = 'NA' if ('pe' not in general_info_list[0] or general_info_list[0]['pe'] is None) else "{:.2f}".format(general_info_list[0]['pe'])
            general_info['price'] = general_info_list[0]['price'],
            general_info['earningsPerShare'] = general_info_list[0]['eps']
    return general_info


def get_dividend_info(symbol):
    dividend_info = {
        'dividend': 'NA',
        'divYield': 'NA',
        'fiveYearAvgDivYield': 'NA',
        'payoutRatio': 'NA'
    }
    if symbol_check(symbol):
        ticker = yf.Ticker(symbol)
        print(type(ticker.actions))
        ticker_dict = ticker.info
        dividend_info['dividend'] = 'NA' if('dividendRate' not in ticker_dict or ticker_dict['dividendRate'] is None) else ticker_dict['dividendRate']
        dividend_info['divYield'] = 'NA' if('dividendYield'not in ticker_dict or ticker_dict['dividendYield'] is None) else "{:.2%}".format(ticker_dict['dividendYield'])
        dividend_info['fiveYearAvgDivYield'] = 'NA' if('fiveYearAvgDividendYield' not in ticker_dict or ticker_dict['fiveYearAvgDividendYield'] is None) else str(ticker_dict['fiveYearAvgDividendYield']) + '%'
        dividend_info['payoutRatio'] = 'NA' if('payoutRatio' not in ticker_dict or ticker_dict['payoutRatio'] is None) else "{:.2%}".format(ticker_dict['payoutRatio'])

    return dividend_info



def get_balance_sheet_info(symbol):
    balance_sheet_info = {
        "currentAssetToLiabRatio": 'NA',
        "totalAssetToLiabRatio": 'NA',
        "past10YearAvgAssetToLiabRatio": 'NA'
    }

    if symbol_check(symbol) and API_CALL:
        balance_sheet_list = requests.get(FINANCE_MODEL_URL+'/balance-sheet-statement/'+symbol+API_KEY).json()

        if balance_sheet_list.get('Error Message') is None and len(balance_sheet_list) != 0:
            current_asset_to_liab_ratio = balance_sheet_list[0]['totalCurrentAssets'] / balance_sheet_list[0]['totalCurrentLiabilities']
            total_asset_to_liab_ratio = balance_sheet_list[0]['totalAssets'] / balance_sheet_list[0]['totalLiabilities']

            sum_total_asset_to_liab_history = 0
            past_ten_year_list = balance_sheet_list[1:11]
            for bs in past_ten_year_list:
                sum_total_asset_to_liab_history += bs['totalAssets']/bs['totalLiabilities']

            avg_total_asset_to_liab = sum_total_asset_to_liab_history / 10
            balance_sheet_info["currentAssetToLiabRatio"]= "{:.2f}".format(current_asset_to_liab_ratio),
            balance_sheet_info["totalAssetToLiabRatio"]= "{:.2f}".format(total_asset_to_liab_ratio),
            balance_sheet_info["past10YearAvgAssetToLiabRatio"]= "{:.2f}".format(avg_total_asset_to_liab)

    return balance_sheet_info


def get_income_sheet_info(symbol) :
    income_sheet_info = {
        "operatingIncomeRatio": "NA",
        "past10YAvgOperatingIncomeRatio": "NA",
        "operatingIncomeGrowth": "NA",
        "fiveYOperatingIncomeGrowth": "NA",
        "tenYOperatingIncomeGrowth": "NA"
    }

    if symbol_check(symbol) and API_CALL:
        income_sheet_list = requests.get(FINANCE_MODEL_URL+'/income-statement/'+symbol+API_KEY).json()

        if income_sheet_list.get('Error Message') is None and len(income_sheet_list) != 0:
            operating_income_ratio = income_sheet_list[0]['operatingIncomeRatio']

            sum_operating_income_ratio_history = 0
            past_ten_year_list = income_sheet_list[1:11]
            for income_statement in past_ten_year_list:
                sum_operating_income_ratio_history += income_statement['operatingIncomeRatio']

            avg_operating_income_ratio = sum_operating_income_ratio_history / 10

            current_operating_income = income_sheet_list[0]['operatingIncome']
            prev_operating_income = income_sheet_list[1]['operatingIncome']
            past_fifth_year_operating_income = income_sheet_list[4]['operatingIncome']
            past_tenth_year_operating_income = income_sheet_list[9]['operatingIncome']

            one_y_growth = (current_operating_income - prev_operating_income)/prev_operating_income
            five_y_growth = (current_operating_income - past_fifth_year_operating_income)/past_fifth_year_operating_income
            ten_y_growth = (current_operating_income - past_tenth_year_operating_income)/past_tenth_year_operating_income

            income_sheet_info["operatingIncomeRatio"] = "{:.2%}".format(operating_income_ratio)
            income_sheet_info["past10YAvgOperatingIncomeRatio"] = "{:.2%}".format(avg_operating_income_ratio)
            income_sheet_info["operatingIncomeGrowth"] = "{:.2%}".format(one_y_growth)
            income_sheet_info["fiveYOperatingIncomeGrowth"] = "{:.2%}".format(five_y_growth)
            income_sheet_info["tenYOperatingIncomeGrowth"] = "{:.2%}".format(ten_y_growth)

    income_sheet_info



def get_cash_flow_info(symbol):
    cash_flow_info = {
        "operatingCashFlow": "NA",
        "investmentCashFlow": "NA",
        "financialCashFlow": "NA"
    }

    if symbol_check(symbol) and API_CALL:
        cash_flow_list = requests.get(FINANCE_MODEL_URL+'/cash-flow-statement/'+symbol+API_KEY).json()

        if cash_flow_list.get('Error Message') is None and len(cash_flow_list) != 0:
            operating_cash_flow = cash_flow_list[0]['operatingCashFlow']
            investment_cash_flow = cash_flow_list[0]['netCashUsedForInvestingActivites']
            financial_cash_flow = cash_flow_list[0]['netCashUsedProvidedByFinancingActivities']

            cash_flow_info["operatingCashFlow"] = "${:,.2f}".format(operating_cash_flow)
            cash_flow_info["investmentCashFlow"] = "${:,.2f}".format(investment_cash_flow)
            cash_flow_info["financialCashFlow"] = "${:,.2f}".format(financial_cash_flow)

    return cash_flow_info



def symbol_check(symbol):
    symbol_validation = False if (symbol is None or not symbol) else True
    return symbol_validation


def error_message(code, desc):
    error['errorCode'] = 100
    error['errorDesc'] = 'Symbol cannot be empty'
    return error


app.run()
