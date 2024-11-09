from pyBacktest.types import TradeType, Holding, Transaction
import pandas as pd

class Backtest:
    # Placeholder for type hinting
    pass

def execute_buy(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    total_cost = numShares * price + commission

    if backtest.cash < total_cost:
        raise Exception("Insufficient funds")

    backtest.cash -= total_cost
    holding = Holding(
        TradeType.BUY,
        backtest.ticker,
        commission,
        True,
        numShares,
        numShares * price,
    )
    backtest.holdings.append(holding)

    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.BUY,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=price,
            totalCost=numShares * price,
            date=valid_date,
            profitLoss=0.0,
        )
    )
    return holding

def execute_sell(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    shares_to_sell = numShares
    total_profit_loss = 0.0
    total_sell_value = 0.0

    for holding in backtest.holdings[:]:  # Use a copy to modify the list while iterating
        if shares_to_sell <= 0:
            break
        if holding.tradeType == TradeType.BUY:
            sell_shares = min(holding.numShares, shares_to_sell)
            buy_price_per_share = holding.totalCost / holding.numShares
            profit_loss = sell_shares * (price - buy_price_per_share)
            total_profit_loss += profit_loss
            total_sell_value += sell_shares * price

            holding.numShares -= sell_shares
            holding.totalCost -= sell_shares * buy_price_per_share
            shares_to_sell -= sell_shares

            if holding.numShares == 0:
                backtest.holdings.remove(holding)

    if shares_to_sell > 0:
        raise Exception("Not enough shares to sell")

    backtest.cash += total_sell_value - commission

    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.SELL,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=price,
            totalCost=total_sell_value,
            date=valid_date,
            profitLoss=total_profit_loss,
        )
    )
    return Holding(
        TradeType.SELL,
        backtest.ticker,
        commission,
        True,
        numShares,
        total_sell_value,
    )

def execute_market_buy(backtest: Backtest, numShares: int, valid_date: pd.Timestamp) -> Holding:
    current_price = backtest.hist.loc[valid_date].Open
    commission = backtest.calculateCommision(current_price, numShares)
    total_cost = numShares * current_price + commission

    if backtest.cash < total_cost:
        raise Exception("Insufficient funds for market buy")

    backtest.cash -= total_cost
    holding = Holding(
        TradeType.MARKET_BUY,
        backtest.ticker,
        commission,
        True,
        numShares,
        numShares * current_price
    )
    backtest.holdings.append(holding)
    
    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.MARKET_BUY,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=current_price,
            totalCost=numShares * current_price,
            date=valid_date,
            profitLoss=0.0,
            notes="Market order"
        )
    )
    return holding

def execute_market_sell(backtest: Backtest, numShares: int, valid_date: pd.Timestamp) -> Holding:
    current_price = backtest.hist.loc[valid_date].Open
    commission = backtest.calculateCommision(current_price, numShares)
    shares_to_sell = numShares
    total_profit_loss = 0.0
    total_sell_value = 0.0

    for holding in backtest.holdings[:]:
        if shares_to_sell <= 0:
            break
        if holding.tradeType in [TradeType.BUY, TradeType.MARKET_BUY]:
            sell_shares = min(holding.numShares, shares_to_sell)
            buy_price_per_share = holding.totalCost / holding.numShares
            profit_loss = sell_shares * (current_price - buy_price_per_share)
            total_profit_loss += profit_loss
            total_sell_value += sell_shares * current_price

            holding.numShares -= sell_shares
            holding.totalCost -= sell_shares * buy_price_per_share
            shares_to_sell -= sell_shares

            if holding.numShares == 0:
                backtest.holdings.remove(holding)

    if shares_to_sell > 0:
        raise Exception("Not enough shares for market sell")

    backtest.cash += total_sell_value - commission

    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.MARKET_SELL,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=current_price,
            totalCost=total_sell_value,
            date=valid_date,
            profitLoss=total_profit_loss,
            notes="Market order"
        )
    )
    return Holding(
        TradeType.MARKET_SELL,
        backtest.ticker,
        commission,
        True,
        numShares,
        total_sell_value
    )
