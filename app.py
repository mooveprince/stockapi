from flask import Flask, request, jsonify
import yfinance as yf
import requests

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


def get_dividend_info(symbol):
    if symbol_check(symbol):
        ticker = yf.Ticker(symbol)
        print(type(ticker.actions))
        ticker_dict = ticker.info
        dividend_info = {
            'dividend': 'NA' if('dividendRate' not in ticker_dict or ticker_dict['dividendRate'] is None)
                else ticker_dict['dividendRate'],
            'divYield': 'NA' if('dividendYield'not in ticker_dict or ticker_dict['dividendYield'] is None)
                else "{:.2%}".format(ticker_dict['dividendYield']),
            'fiveYearAvgDivYield': 'NA' if('fiveYearAvgDividendYield' not in ticker_dict or ticker_dict['fiveYearAvgDividendYield'] is None)
                else str(ticker_dict['fiveYearAvgDividendYield']) + '%',
            'payoutRatio': 'NA' if('payoutRatio' not in ticker_dict or ticker_dict['payoutRatio'] is None)
                else "{:.2%}".format(ticker_dict['payoutRatio'])
        }

        return dividend_info
    else:
        return -1


def get_general_info(symbol):
    if symbol_check(symbol):
        general_info_list = requests.get('https://financialmodelingprep.com/api/v3/quote/'+ symbol +'?apikey=0ee048fea75d0f7205b64b8bb6723608').json()
        general_info = {
            'companyName': general_info_list[0]['name'],
            'peRatio': 'NA' if ('pe' not in general_info_list[0] or general_info_list[0]['pe'] is None)
            else "{:.2f}".format(general_info_list[0]['pe']),
            'price': general_info_list[0]['price'],
            'earningsPerShare': general_info_list[0]['eps']

        }
        return general_info
    else:
        return -1


def get_balance_sheet_info(symbol):
    if symbol_check(symbol):
        balance_sheet_list = requests.get(
            'https://financialmodelingprep.com/api/v3/balance-sheet-statement/' + symbol + '?apikey=0ee048fea75d0f7205b64b8bb6723608').json()

        if len(balance_sheet_list) != 0:
            current_asset_to_liab_ratio = balance_sheet_list[0]['totalCurrentAssets'] / balance_sheet_list[0]['totalCurrentLiabilities']
            total_asset_to_liab_ratio = balance_sheet_list[0]['totalAssets'] / balance_sheet_list[0]['totalLiabilities']

            sum_total_asset_to_liab_history = 0
            past_ten_year_list = balance_sheet_list[1:11]
            for bs in past_ten_year_list:
                sum_total_asset_to_liab_history += bs['totalAssets']/bs['totalLiabilities']

            avg_total_asset_to_liab = sum_total_asset_to_liab_history / 10
            balance_sheet_info = {
                "currentAssetToLiabRatio": "{:.2f}".format(current_asset_to_liab_ratio),
                "totalAssetToLiabRatio": "{:.2f}".format(total_asset_to_liab_ratio),
                "past10YearAvgAssetToLiabRatio": "{:.2f}".format(avg_total_asset_to_liab)
            }
            return balance_sheet_info
    else:
        return -1


def get_income_sheet_info(symbol):
    if symbol_check(symbol):
        income_sheet_list = requests.get(
            'https://financialmodelingprep.com/api/v3/income-statement/' + symbol + '?apikey=0ee048fea75d0f7205b64b8bb6723608').json()

        if len(income_sheet_list) != 0:
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

            income_sheet_info = {
                "operatingIncomeRatio": "{:.2%}".format(operating_income_ratio),
                "past10YAvgOperatingIncomeRatio": "{:.2%}".format(avg_operating_income_ratio),
                "operatingIncomeGrowth":"{:.2%}".format(one_y_growth),
                "fiveYOperatingIncomeGrowth": "{:.2%}".format(five_y_growth),
                "tenYOperatingIncomeGrowth": "{:.2%}".format(ten_y_growth)
            }
            return income_sheet_info
    else:
        return -1


def get_cash_flow_info(symbol):
    if symbol_check(symbol):
        cash_flow_list = requests.get(
            'https://financialmodelingprep.com/api/v3/cash-flow-statement/' + symbol + '?apikey=0ee048fea75d0f7205b64b8bb6723608').json()

        if len(cash_flow_list) != 0 :
            operating_cash_flow = cash_flow_list[0]['operatingCashFlow']
            investment_cash_flow = cash_flow_list[0]['netCashUsedForInvestingActivites']
            financial_cash_flow = cash_flow_list[0]['netCashUsedProvidedByFinancingActivities']

            cash_flow_info = {
                "operatingCashFlow": "${:,.2f}".format(operating_cash_flow),
                "investmentCashFlow": "${:,.2f}".format(investment_cash_flow),
                "financialCashFlow": "${:,.2f}".format(financial_cash_flow)
            }
            return cash_flow_info
    else:
        return -1


def symbol_check(symbol):
    symbol_validation = False if (symbol is None or not symbol) else True
    return symbol_validation


def error_message(code, desc):
    error['errorCode'] = 100
    error['errorDesc'] = 'Symbol cannot be empty'
    return error


#app.run()
