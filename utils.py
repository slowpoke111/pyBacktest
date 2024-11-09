from typing import List, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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

def detectCrossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    previousDiff = (series1 - series2).shift(1)
    currentDiff = series1 - series2
    return (previousDiff < 0) & (currentDiff > 0)

def detectCrossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    previousDiff = (series1 - series2).shift(1)
    currentDiff = series1 - series2
    return (previousDiff > 0) & (currentDiff < 0)

def getCrossSignals(fastMA: pd.Series, slowMA: pd.Series) -> pd.Series:
    crossovers = detectCrossover(fastMA, slowMA)
    crossunders = detectCrossunder(fastMA, slowMA)
    signals = pd.Series(0, index=fastMA.index)
    signals[crossovers] = 1
    signals[crossunders] = -1
    return signals
