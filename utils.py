from typing import List, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pyBacktest.results import BacktestResult
import yfinance as yf

def calculateSMA(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()

def calculateEMA(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

def calculateRSI(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculateBollingerBands(data: pd.Series, period: int = 20, stdDev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = calculateSMA(data, period)
    std = data.rolling(window=period).std()
    upperBand = sma + (std * stdDev)
    lowerBand = sma - (std * stdDev)
    return upperBand, sma, lowerBand

def calculateMACD(data: pd.Series, fastPeriod: int = 12, slowPeriod: int = 26, signalPeriod: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    fastEMA = calculateEMA(data, fastPeriod)
    slowEMA = calculateEMA(data, slowPeriod)
    macd = fastEMA - slowEMA
    signal = calculateEMA(macd, signalPeriod)
    histogram = macd - signal
    return macd, signal, histogram

def calculateDrawdown(data: pd.Series) -> Tuple[float, float]:
    rolling_max = data.expanding().max()
    drawdown = data / rolling_max - 1.0
    maxDrawdown = drawdown.min()
    currentDrawdown = drawdown.iloc[-1]
    return maxDrawdown, currentDrawdown

def calculateSharpeRatio(returns: pd.Series, riskFreeRate: float = 0.01) -> float:
    excessReturns = returns - riskFreeRate/252
    return np.sqrt(252) * (excessReturns.mean() / excessReturns.std())

def calculateVolatility(returns: pd.Series, annualized: bool = True) -> float:
    vol = returns.std()
    return vol * np.sqrt(252) if annualized else vol

def calculateBeta(returns: pd.Series, marketReturns: pd.Series) -> float:
    covariance = returns.cov(marketReturns)
    marketVariance = marketReturns.var()
    return covariance / marketVariance

def calculateReturnStats(returns: pd.Series) -> dict:
    return {
        "totalReturn": (returns + 1).prod() - 1,
        "annualizedReturn": (1 + returns).prod() ** (252/len(returns)) - 1,
        "volatility": calculateVolatility(returns),
        "sharpeRatio": calculateSharpeRatio(returns),
        "maxDrawdown": calculateDrawdown(returns)[0]
    }

def calculateSortinoRatio(returns: pd.Series, riskFreeRate: float = 0.01) -> float:
    downside_returns = returns[returns < 0]
    expected_return = returns.mean() - riskFreeRate / 252
    downside_deviation = downside_returns.std()
    return np.sqrt(252) * (expected_return / downside_deviation)

def calculateTreynorRatio(returns: pd.Series, marketReturns: pd.Series, riskFreeRate: float = 0.01) -> float:
    beta = calculateBeta(returns, marketReturns)
    excess_return = returns.mean() - riskFreeRate / 252
    return excess_return / beta

def calculateVaR(returns: pd.Series, confidence_level: float = 0.95) -> float:
    return np.percentile(returns, (1 - confidence_level) * 100)

def getPreviousRows(data: pd.DataFrame, date: datetime, periods: int) -> pd.DataFrame:
    date = pd.Timestamp(date)
    if date not in data.index:
        date = data.index[data.index.get_indexer([date], method="nearest")[0]]
    return data.loc[:date].tail(periods)

def analyzeResults(results1: BacktestResult, results2: BacktestResult, initial_investment: float = 10000) -> dict:
    final_value1 = results1.final_value
    final_value2 = results2.final_value
    total_return1 = ((final_value1 - initial_investment) / initial_investment) * 100
    total_return2 = ((final_value2 - initial_investment) / initial_investment) * 100

    start_date1 = results1.transactions[0].date
    end_date1 = results1.strategy.backtest.date
    days_held1 = (end_date1 - start_date1).days

    start_date2 = results2.transactions[0].date
    end_date2 = results2.strategy.backtest.date
    days_held2 = (end_date2 - start_date2).days

    annualized_return1 = (total_return1 / (days_held1 / 365)) if days_held1 > 0 else 0
    annualized_return2 = (total_return2 / (days_held2 / 365)) if days_held2 > 0 else 0

    comparison = {
        "initial_investment": initial_investment,
        "final_value1": final_value1,
        "final_value2": final_value2,
        "total_return1": total_return1,
        "total_return2": total_return2,
        "annualized_return1": annualized_return1,
        "annualized_return2": annualized_return2,
        "start_date1": start_date1,
        "end_date1": end_date1,
        "days_held1": days_held1,
        "start_date2": start_date2,
        "end_date2": end_date2,
        "days_held2": days_held2,
        "transactions1": len(results1.transactions),
        "transactions2": len(results2.transactions)
    }

    print("\nStrategy Comparison Results:")
    print(f"{'Metric':<20} {'Strategy 1':<20} {'Strategy 2':<20}")
    print(f"{'Initial Investment':<20} ${initial_investment:<20,.2f} ${initial_investment:<20,.2f}")
    print(f"{'Final Value':<20} ${final_value1:<20,.2f} ${final_value2:<20,.2f}")
    print(f"{'Total Return':<20} {total_return1:<20.2f}% {total_return2:<20.2f}%")
    print(f"{'Annualized Return':<20} {annualized_return1:<20.2f}% {annualized_return2:<20.2f}%")
    print(f"{'Start Date':<20} {start_date1.strftime('%Y-%m-%d'):<20} {start_date2.strftime('%Y-%m-%d'):<20}")
    print(f"{'End Date':<20} {end_date1.strftime('%Y-%m-%d'):<20} {end_date2.strftime('%Y-%m-%d'):<20}")
    print(f"{'Days Held':<20} {days_held1:<20} {days_held2:<20}")
    print(f"{'Transactions':<20} {len(results1.transactions):<20} {len(results2.transactions):<20}")

    return comparison

def compareBacktests(results1: BacktestResult, results2: BacktestResult) -> dict:
    comparison = {
        "final_value_diff": results1.final_value - results2.final_value,
        "total_return_diff": ((results1.final_value - 10000) / 10000) - ((results2.final_value - 10000) / 10000),
        "num_transactions_diff": len(results1.transactions) - len(results2.transactions),
        "better_strategy": "Strategy 1" if results1.final_value > results2.final_value else "Strategy 2"
    }
    return comparison

def getSP500Returns(start_date: datetime, end_date: datetime) -> pd.Series:
    sp500 = yf.Ticker('^GSPC')
    sp500_data = sp500.history(start=start_date, end=end_date)
    return sp500_data['Close'].pct_change().dropna()