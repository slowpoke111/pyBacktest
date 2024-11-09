import yfinance as yf
from yfinance import Ticker
from typing import *
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pandas.tseries.offsets import DateOffset


class TradeType(Enum):
    BUY = 1
    SELL = 2
    SHORT = 3
    STOP = 4
    COVER = 5
    LIMIT = 6


@dataclass
class Holding:
    tradeType: TradeType
    ticker: str
    commission: float
    executedSuccessfully: bool
    numShares: int
    totalCost: float


@dataclass
class Transaction:
    tradeType: TradeType
    ticker: str
    commission: float
    executedSuccessfully: bool
    numShares: int
    pricePerShare: float
    totalCost: float
    date: datetime
    profitLoss: float = 0.0
    notes: str = ""


class Backtest:
    def __init__(
        self,
        ticker: str,
        cash: float | int,
        commision: float | int = 0.0,
        commisionType: str = "flat",
        timePeriod: str = "1mo",
        interval: str = "1d",
        startDate: datetime = datetime(2024, 1, 1),
        endDate: datetime = datetime(2024, 2, 1),
    ) -> None:

        self.ticker: str = ticker.upper()
        self.commision: float = commision
        self.commisionType: float = commisionType

        self.timePeriod: str = timePeriod

        interval_value = int(interval[:-1])
        interval_unit = interval[-1]

        self.interval = pd.DateOffset(
            minutes=interval_value if interval_unit == "m" else 0,
            hours=interval_value if interval_unit == "h" else 0,
            days=interval_value if interval_unit == "d" else 0,
            weeks=interval_value if interval_unit == "w" else 0,
            months=interval_value if interval_unit == "mo" else 0,
        )

        self.date = pd.Timestamp(startDate).tz_localize("America/New_York")
        self.endDate = pd.Timestamp(endDate).tz_localize("America/New_York")

        self.data: Ticker = yf.Ticker(self.ticker)
        self.hist: DataFrame = self.data.history(
            start=self.date, end=self.endDate, interval=interval
        )
        self.transactions: List[Holding] = []

        self.cash: float = cash
        self.holdings: List[Holding] = []

    def getValidDate(self, target_date: pd.Timestamp) -> pd.Timestamp:
        if target_date in self.hist.index:
            return target_date
        return self.hist.index[
            self.hist.index.get_indexer([target_date], method="nearest")[0]
        ]

    def formatDate(self, date: datetime) -> pd.Timestamp:
        if not isinstance(date, pd.Timestamp):
            date = pd.Timestamp(date)
        if date.tz is None:
            date = date.tz_localize("America/New_York")
        return self.getValidDate(date)

    def calculateCommision(self, price: float, numShares: int) -> float:
        if self.commisionType == "flat":
            return self.commision
        elif self.commisionType == "percentage":
            return price * self.commision * numShares
        elif self.commisionType == "percentage_per_share":
            return self.commision * numShares
        else:
            raise Exception("Invalid commision type")

    def next(self):
        self.date += self.interval
        valid_date = self.formatDate(self.date)
        return self.hist.loc[valid_date]

    def _execute_buy(
        self, price: float, numShares: int, valid_date: pd.Timestamp
    ) -> Holding:
        commission = self.calculateCommision(price, numShares)
        total_cost = numShares * price + commission

        if self.cash < total_cost:
            raise Exception("Insufficient funds")

        self.cash -= total_cost
        holding = Holding(
            TradeType.BUY,
            self.ticker,
            commission,
            True,
            numShares,
            numShares * price,
        )
        self.holdings.append(holding)

        self.transactions.append(
            Transaction(
                tradeType=TradeType.BUY,
                ticker=self.ticker,
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

    def _execute_sell(
        self, price: float, numShares: int, valid_date: pd.Timestamp
    ) -> Holding:
        commission = self.calculateCommision(price, numShares)
        for holding in self.holdings:
            if holding.tradeType == TradeType.BUY and holding.numShares >= numShares:
                self.holdings.remove(holding)
                self.cash += (numShares * price) - commission

                sell_holding = Holding(
                    TradeType.SELL,
                    self.ticker,
                    commission,
                    True,
                    numShares,
                    numShares * price,
                )

                profit_loss = (numShares * price) - (
                    numShares * (holding.totalCost / holding.numShares)
                )
                self.transactions.append(
                    Transaction(
                        tradeType=TradeType.SELL,
                        ticker=self.ticker,
                        commission=commission,
                        executedSuccessfully=True,
                        numShares=numShares,
                        pricePerShare=price,
                        totalCost=numShares * price,
                        date=valid_date,
                        profitLoss=profit_loss,
                    )
                )
                return sell_holding
        raise Exception("Not enough shares to sell")

    def trade(self, tradeType: TradeType, numShares: int) -> Holding:
        valid_date = self.formatDate(self.date)
        price = self.hist.loc[valid_date].Close

        trade_handlers = {
            TradeType.BUY: self._execute_buy,
            TradeType.SELL: self._execute_sell,
            TradeType.SHORT: NotImplemented,
            TradeType.STOP: NotImplemented,
            TradeType.COVER: NotImplemented,
            TradeType.LIMIT: NotImplemented,
        }

        handler = trade_handlers.get(tradeType)
        if handler is None:
            raise ValueError(f"Unsupported trade type: {tradeType}")
        elif handler is NotImplemented:
            raise NotImplementedError(f"Trade type not implemented yet: {tradeType}")

        return handler(price, numShares, valid_date)

    def totalValue(self) -> float:
        total_value = self.cash
        valid_date = self.formatDate(self.date)
        for holding in self.holdings:
            price = self.hist.loc[valid_date].Close
            total_value += holding.numShares * price
        return total_value


if __name__ == "__main__":
    x = Backtest(
        "GOOG",
        10_000.0,
    )

    for _ in range(5):
        x.trade(TradeType.BUY, 5)
        x.next()

    print(f"Total portfolio value: {x.totalValue()}")
