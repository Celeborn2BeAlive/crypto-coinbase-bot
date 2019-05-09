import argparse, os, time, sys
import pandas as pd
from datetime import datetime, timezone, timedelta
import pprint as pp

path_to_data = r"D:\Developpement\cryptobigbro-coinbase-data"
delta = timedelta(days=1)

class CoinbaseBacktestExchange:
    def __init__(self, value_currency, instruments):
        self.instruments = instruments
        self.dataframes = {}
        self.first_timestamp = 0
        self.value_currency = value_currency
        self.assets = []
        self.assets.append(self.value_currency)
        for instr in instruments:
            base_currency, quote_currency = instr.split('-')
            path_to_csv_file = os.path.join(path_to_data, 'coinbasepro-' + instr + '-1d.csv')
            self.dataframes[instr] = pd.read_csv(path_to_csv_file, index_col='open_timestamp_utc')
            self.first_timestamp = max(self.first_timestamp, self.dataframes[instr].index[0])
            self.assets.append(base_currency)

    def fee_percentage(self):
        return 0.15

    def fee_factor(self):
        return self.fee_percentage() * 0.01

    def timestamp(self, idx):
        return self.first_timestamp + idx * delta.total_seconds()

    def price(self, idx, base_currency, quote_currency):
        return self.dataframes[base_currency + '-' + quote_currency].loc[self.timestamp(idx), 'open']

class Portfolio:
    def __init__(self, exchange):
        self.exchange = exchange
        self.positions = {}
        for asset in exchange.assets:
            self.positions[asset] = 0
    
    def positions(self):
        return self.positions

    def portfolio_value(self, idx):
        sum = 0
        for asset in self.exchange.assets:
            if asset == self.exchange.value_currency:
                sum = sum + self.positions[asset]
            else:
                sum = sum + self.positions[asset] * self.exchange.price(idx, asset, self.exchange.value_currency)
        return sum

def portfolio_compute_position_deltas(exchange, target_weights, idx):
    current_positions = exchange.positions()
    portfolio_value = exchange.portfolio_value()
    deltas = {}
    for asset in current_positions:
        required_position = target_weights[asset] * portfolio_value / exchange.price(idx, asset, exchange.value_currency)
        deltas[asset] = required_position - current_positions[asset]
    return deltas

def main():
    exchange = CoinbaseBacktestExchange('EUR', [ 'BTC-EUR', 'ETH-EUR', 'LTC-EUR' ])
    portfolio = Portfolio(exchange)

    backtest_period = 300 # number of days to backtest

    invest_period = 7 # number of days to wait before buying again
    invest_amount = 100 # EUR to invest each period

    strategy = "cost_averaging"

    total_invested = 0

    events = []

    if strategy == "cost_averaging":
        invest_amount_per_instrument = invest_amount / len(exchange.instruments)
        for i in range(backtest_period):
            if i % invest_period == 0:
                timestamp = exchange.timestamp(i)
                total_invested += invest_amount
                for instr in exchange.instruments:
                    asset =  instr.split('-')[0]
                    price = exchange.price(i, asset, exchange.value_currency)
                    qty_to_buy = invest_amount_per_instrument * (1 - exchange.fee_factor()) / price
                    portfolio.positions[asset] += qty_to_buy
        
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

                    events.append({
                        "action": "rebalance",
                        "epoch": i,
                        "timestamp": timestamp,
                        "portfolio_value": portfolio_value,
                        "position_values": position_values,
                        "positions_weights": positions_weights,
                        "return": 100 * (portfolio_value - total_invested) / total_invested
                    })

                    for instr in instruments_to_trade:
                        positions_weights[instr] = position_values[instr] / portfolio_value
                        if position_values[instr] > lowest_value:
                            instr_sell_amount = position_values[instr] - lowest_value
                            price = dataframes[instr].loc[timestamp, 'open']
                            qty_to_sell = instr_sell_amount / price
                            positions[instr] -= qty_to_sell
                            sell_amount += instr_sell_amount * (1 - fees)
                            events.append({
                                "action": "sell",
                                "epoch": i,
                                "timestamp": timestamp,
                                "instrument": instr,
                                "qty": qty_to_sell,
                                "sell_amount": instr_sell_amount,
                                "fee_amount": instr_sell_amount * fees
                            })
                    # for instr in instruments_to_trade:
                    #     price = dataframes[instr].loc[timestamp, 'open']
                    #     print(instr, positions[instr], positions[instr] * price)
                    # print("sell_amount ", sell_amount)

                events.append({
                    "action": "invest",
                    "epoch": i,
                    "timestamp": timestamp,
                    "invest_amount": invest_amount,
                    "reinvest_amount": sell_amount
                })

                invest_amount_per_instrument = (invest_amount + sell_amount) / len(instruments_to_trade)
                total_invested += invest_amount
                for instr in instruments_to_trade:
                    price = dataframes[instr].loc[timestamp, 'open']
                    qty_to_buy = invest_amount_per_instrument * (1 - fees) / price
                    positions[instr] += qty_to_buy
                    events.append({
                        "action": "buy",
                        "epoch": i,
                        "timestamp": timestamp,
                        "instrument": instr,
                        "qty": qty_to_buy,
                        "buy_amount": invest_amount_per_instrument * (1 - fees),
                        "fee_amount": invest_amount_per_instrument * fees
                    })

    print("total invested {}".format(total_invested))
    portfolio_value = portfolio.portfolio_value(backtest_period)
    print("portfolio value {}".format(portfolio_value))
    print("return {} %".format(100 * (portfolio_value - total_invested) / total_invested))
    pp.pprint(events)

if __name__ == "__main__":
    main()