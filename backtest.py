import yfinance as yf
from yfinance import Ticker
from typing import *
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pandas.tseries.offsets import DateOffset
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyBacktest.strategy import Strategy

class TradeType(Enum):
    BUY = 1
    SELL = 2
    SHORT = 3
    STOP = 4
    COVER = 5
    LIMIT = 6
    GTC = 7
    Cancel = 8
    MARKET_BUY = 9
    MARKET_SELL = 10


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


@dataclass
class Order:
    tradeType: TradeType
    ticker: str
    numShares: int
    targetPrice: float
    duration: str  # 'DAY' or 'GTC'
    orderDate: datetime
    active: bool = True


class Backtest:
    def __init__(
        self,
        ticker: str,
        cash: float | int,
        strategy: 'Strategy',
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
        self.pending_orders: List[Order] = []
        self.strategy = strategy
        self.strategy.initialize(self)

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

    def cancelOrder(self, order_index: int) -> bool:
        if 0 <= order_index < len(self.pending_orders):
            order = self.pending_orders[order_index]
            order.active = False
            self.transactions.append(
                Transaction(
                    tradeType=TradeType.Cancel,
                    ticker=order.ticker,
                    commission=0,
                    executedSuccessfully=True,
                    numShares=order.numShares,
                    pricePerShare=order.targetPrice,
                    totalCost=0,
                    date=self.date,
                    notes="Order canceled"
                )
            )
            return True
        return False

    def submitGTCOrder(self, tradeType: TradeType, numShares: int, targetPrice: float) -> Order:
        order = Order(
            tradeType=tradeType,
            ticker=self.ticker,
            numShares=numShares,
            targetPrice=targetPrice,
            duration='GTC',
            orderDate=self.date
        )
        self.pending_orders.append(order)
        return order

    def _check_pending_orders(self, current_price: float):
        for order in self.pending_orders[:]:
            if not order.active:
                self.pending_orders.remove(order)
                continue
                
            if order.tradeType in [TradeType.BUY, TradeType.COVER] and current_price <= order.targetPrice:
                self._execute_buy(current_price, order.numShares, self.date)
                order.active = False
            elif order.tradeType in [TradeType.SELL, TradeType.SHORT] and current_price >= order.targetPrice:
                self._execute_sell(current_price, order.numShares, self.date)
                order.active = False

    def next(self):
        self.date += self.interval
        valid_date = self.formatDate(self.date)
        current_price = self.hist.loc[valid_date].Close
        self._check_pending_orders(current_price)
        row = self.hist.loc[valid_date]
        self.strategy.next(row)
        return row

    def run(self) -> Dict[str, Any]:
        while self.date < self.endDate:
            self.next()
        return {
            "final_value": self.totalValue(),
            "transactions": self.transactions,
        }

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

    def _execute_sell(self, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
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

    def _execute_market_buy(self, numShares: int, valid_date: pd.Timestamp) -> Holding:
        current_price = self.hist.loc[valid_date].Open
        commission = self.calculateCommision(current_price, numShares)
        total_cost = numShares * current_price + commission

        if self.cash < total_cost:
            raise Exception("Insufficient funds for market buy")

        self.cash -= total_cost
        holding = Holding(
            TradeType.MARKET_BUY,
            self.ticker,
            commission,
            True,
            numShares,
            numShares * current_price
        )
        self.holdings.append(holding)
        
        self.transactions.append(
            Transaction(
                tradeType=TradeType.MARKET_BUY,
                ticker=self.ticker,
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

    def _execute_market_sell(self, numShares: int, valid_date: pd.Timestamp) -> Holding:
        current_price = self.hist.loc[valid_date].Open
        commission = self.calculateCommision(current_price, numShares)
        
        for holding in self.holdings:
            if holding.tradeType in [TradeType.BUY, TradeType.MARKET_BUY] and holding.numShares >= numShares:
                self.holdings.remove(holding)
                self.cash += (numShares * current_price) - commission
                
                profit_loss = (numShares * current_price) - (numShares * (holding.totalCost / holding.numShares))
                
                sell_holding = Holding(
                    TradeType.MARKET_SELL,
                    self.ticker,
                    commission,
                    True,
                    numShares,
                    numShares * current_price
                )
                
                self.transactions.append(
                    Transaction(
                        tradeType=TradeType.MARKET_SELL,
                        ticker=self.ticker,
                        commission=commission,
                        executedSuccessfully=True,
                        numShares=numShares,
                        pricePerShare=current_price,
                        totalCost=numShares * current_price,
                        date=valid_date,
                        profitLoss=profit_loss,
                        notes="Market order"
                    )
                )
                return sell_holding
        raise Exception("Not enough shares for market sell")

    def trade(self, tradeType: TradeType, numShares: int, price: float = None) -> Holding:
        validDate = self.formatDate(self.date)
        
        trade_handlers = {
            TradeType.BUY: lambda p, n, d: self._execute_buy(p, n, d),
            TradeType.SELL: lambda p, n, d: self._execute_sell(p, n, d),
            TradeType.MARKET_BUY: lambda p, n, d: self._execute_market_buy(n, d),
            TradeType.MARKET_SELL: lambda p, n, d: self._execute_market_sell(n, d),
            TradeType.SHORT: NotImplemented,
            TradeType.STOP: NotImplemented,
            TradeType.COVER: NotImplemented,
            TradeType.LIMIT: NotImplemented,
        }

        if tradeType in [TradeType.MARKET_BUY, TradeType.MARKET_SELL]:
            return trade_handlers[tradeType](None, numShares, validDate)

        price = self.hist.loc[validDate].Close
        return trade_handlers[tradeType](price, numShares, validDate)

    def totalValue(self) -> float:
        total_value = self.cash
        valid_date = self.formatDate(self.date)
        for holding in self.holdings:
            price = self.hist.loc[valid_date].Close
            total_value += holding.numShares * price
        return total_value
