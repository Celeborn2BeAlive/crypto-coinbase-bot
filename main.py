import argparse, os, time, sys
import pandas as pd
from datetime import datetime, timezone, timedelta

class BacktestExchange:
    def __init__(self):
        pass

def main():
    path_to_data = r"D:\Developpement\cryptobigbro-coinbase-data"
    instruments_to_trade = [ 'BTC-EUR', 'ETH-EUR', 'LTC-EUR' ]
    positions = {}
    fees = 0.15 / 100

    dataframes = {}
    first_timestamp = 0

    for instr in instruments_to_trade:
        path_to_csv_file = os.path.join(path_to_data, 'coinbasepro-' + instr + '-1d.csv')
        dataframes[instr] = pd.read_csv(path_to_csv_file, index_col='open_timestamp_utc')
        positions[instr] = 0
        first_timestamp = max(first_timestamp, dataframes[instr].index[0])
    
    first_date = datetime.fromtimestamp(first_timestamp, timezone.utc)
    delta = timedelta(days=1)

    backtest_period = 300 # number of days to backtest

    invest_period = 7 # number of days to wait before buying again
    invest_amount = 100 # EUR to invest each period

    strategy = "cost_averaging_rebalance_equal_weights"

    total_invested = 0

    if strategy == "cost_averaging":
        invest_amount_per_instrument = invest_amount / len(instruments_to_trade)
        for i in range(backtest_period):
            if i % invest_period == 0:
                timestamp = first_timestamp + i * delta.total_seconds()
                total_invested += invest_amount
                for instr in instruments_to_trade:
                    price = dataframes[instr].loc[timestamp, 'open']
                    qty_to_buy = invest_amount_per_instrument * (1 - fees) / price
                    positions[instr] += qty_to_buy
        
    if strategy == "cost_averaging_rebalance_equal_weights":
        for i in range(backtest_period):
            if i % invest_period == 0:
                timestamp = first_timestamp + i * delta.total_seconds()
                #print(timestamp)
                sell_amount = 0
                if total_invested > 0:
                    position_values = {}
                    portfolio_value = 0
                    lowest_value = sys.float_info.max
                    for instr in instruments_to_trade:
                        price = dataframes[instr].loc[timestamp, 'open']
                        position_values[instr] = price * positions[instr]
                        lowest_value = min(lowest_value, position_values[instr])
                        portfolio_value += position_values[instr]
                    positions_weights = {}
                    # for instr in instruments_to_trade:
                    #     price = dataframes[instr].loc[timestamp, 'open']
                    #     print(instr, positions[instr], positions[instr] * price)
                    for instr in instruments_to_trade:
                        positions_weights[instr] = position_values[instr] / portfolio_value
                        if position_values[instr] > lowest_value:
                            instr_sell_amount = position_values[instr] - lowest_value
                            price = dataframes[instr].loc[timestamp, 'open']
                            qty_to_sell = instr_sell_amount / price
                            positions[instr] -= qty_to_sell
                            sell_amount += instr_sell_amount * (1 - fees)
                    # for instr in instruments_to_trade:
                    #     price = dataframes[instr].loc[timestamp, 'open']
                    #     print(instr, positions[instr], positions[instr] * price)
                    # print("sell_amount ", sell_amount)

                invest_amount_per_instrument = (invest_amount + sell_amount) / len(instruments_to_trade)
                total_invested += invest_amount
                for instr in instruments_to_trade:
                    price = dataframes[instr].loc[timestamp, 'open']
                    qty_to_buy = invest_amount_per_instrument * (1 - fees) / price
                    positions[instr] += qty_to_buy

    print("total invested {}".format(total_invested))
    portfolio_value = 0
    for instr in instruments_to_trade:
        timestamp = first_timestamp + backtest_period * delta.total_seconds()
        price = dataframes[instr].loc[timestamp, 'open']
        portfolio_value += price * positions[instr]
    print("portfolio value {}".format(portfolio_value))
    print("return {} %".format(100 * (portfolio_value - total_invested) / total_invested))

if __name__ == "__main__":
    main()