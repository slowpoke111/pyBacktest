from pyBacktest.tradeTypes import (
    TradeType, Holding, Transaction,
    InsufficientFundsError, InsufficientSharesError, ShortPositionError
)
import pandas as pd

class Backtest:
    # Placeholder for type hinting
    pass

def execute_buy(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp, trade_type: TradeType = TradeType.BUY) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    total_cost = numShares * price + commission

    if backtest.cash < total_cost:
        raise InsufficientFundsError(f"Need ${total_cost:,.2f}, have ${backtest.cash:,.2f}")

    backtest.cash -= total_cost

    holding = Holding(
        trade_type,
        backtest.ticker,
        commission,
        True,
        numShares,
        numShares * price,
    )
    backtest.holdings.append(holding)

    backtest.transactions.append(
        Transaction(
            tradeType=trade_type,
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

def execute_sell(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp, trade_type: TradeType = TradeType.SELL) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    shares_to_sell = numShares
    total_profit_loss = 0.0
    total_sell_value = 0.0

    for holding in backtest.holdings[:]:  # Use a copy to modify the list while iterating
        if shares_to_sell <= 0:
            break
        if holding.tradeType in [TradeType.BUY, TradeType.MARKET_BUY, TradeType.LIMIT_BUY]:
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
        raise InsufficientSharesError("Not enough shares to sell")

    backtest.cash += total_sell_value - commission

    backtest.transactions.append(
        Transaction(
            tradeType=trade_type,
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
        trade_type,
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
        raise InsufficientFundsError(f"Insufficient funds for market buy. Need {total_cost}, have {backtest.cash}")

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
        if holding.tradeType in [TradeType.BUY, TradeType.MARKET_BUY, TradeType.LIMIT_BUY]:
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
        raise InsufficientSharesError(f"Not enough shares for market sell. Still need {shares_to_sell} shares")

    sell_proceeds = total_sell_value - commission
    backtest.cash += sell_proceeds

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

def execute_short_sell(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    proceeds = numShares * price - commission

    backtest.cash += proceeds
    holding = Holding(
        tradeType=TradeType.SHORT_SELL,
        ticker=backtest.ticker,
        commission=commission,
        executedSuccessfully=True,
        numShares=numShares,
        totalCost=numShares * price,
    )
    backtest.holdings.append(holding)

    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.SHORT_SELL,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=price,
            totalCost=proceeds,
            date=valid_date,
            profitLoss=0.0,
        )
    )
    return holding

def execute_short_cover(backtest: Backtest, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
    commission = backtest.calculateCommision(price, numShares)
    shares_to_cover = numShares
    total_profit_loss = 0.0
    total_cover_cost = 0.0

    for holding in backtest.holdings[:]:
        if shares_to_cover <= 0:
            break
        if holding.tradeType == TradeType.SHORT_SELL:
            cover_shares = min(holding.numShares, shares_to_cover)
            sell_price_per_share = holding.totalCost / holding.numShares
            profit_loss = cover_shares * (sell_price_per_share - price)
            total_profit_loss += profit_loss
            total_cover_cost += cover_shares * price

            holding.numShares -= cover_shares
            holding.totalCost -= cover_shares * sell_price_per_share
            shares_to_cover -= cover_shares

            if holding.numShares == 0:
                backtest.holdings.remove(holding)

    if shares_to_cover > 0:
        raise ShortPositionError("Not enough short positions to cover")

    if backtest.cash < total_cover_cost + commission:
        raise InsufficientFundsError(f"Insufficient funds to cover short position. Need ${total_cover_cost + commission:,.2f}, have ${backtest.cash:,.2f}")

    backtest.cash -= total_cover_cost + commission

    backtest.transactions.append(
        Transaction(
            tradeType=TradeType.SHORT_COVER,
            ticker=backtest.ticker,
            commission=commission,
            executedSuccessfully=True,
            numShares=numShares,
            pricePerShare=price,
            totalCost=total_cover_cost,
            date=valid_date,
            profitLoss=total_profit_loss,
        )
    )
    return Holding(
        tradeType=TradeType.SHORT_COVER,
        ticker=backtest.ticker,
        commission=commission,
        executedSuccessfully=True,
        numShares=numShares,
        totalCost=total_cover_cost,
    )
