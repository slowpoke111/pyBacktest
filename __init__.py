from .backtest import Backtest
from .strategy import Strategy
from .tradeTypes import TradeType, Holding, Transaction, Order
from .utils import (
    calculateSMA,
    calculateEMA,
    calculateRSI,
    calculateBollingerBands,
    calculateMACD,
    calculateDrawdown,
    calculateSharpeRatio,
    calculateVolatility,
    calculateBeta,
    calculateReturnStats,
    detectCrossover,
    detectCrossunder,
    getCrossSignals
)

__version__ = "1.0.1"
__author__ = "Ben Bell"

__all__ = [
    "Backtest",
    "Strategy",
    "TradeType",
    "Holding",
    "Transaction",
    "Order",
    "calculateSMA",
    "calculateEMA",
    "calculateRSI",
    "calculateBollingerBands",
    "calculateMACD",
    "calculateDrawdown",
    "calculateSharpeRatio",
    "calculateVolatility",
    "calculateBeta",
    "calculateReturnStats",
    "detectCrossover",
    "detectCrossunder",
    "getCrossSignals"
]
