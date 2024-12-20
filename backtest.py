import yfinance as yf
from yfinance import Ticker
from typing import *
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import TYPE_CHECKING
from pyBacktest.trades import execute_buy, execute_sell, execute_market_buy, execute_market_sell, execute_short_sell, execute_short_cover
from pyBacktest.tradeTypes import TradeType, Holding, Order, InvalidOrderError
from pyBacktest.commissions import calculate_commission
from pyBacktest.orders import cancel_order, submit_gtc_order
from pyBacktest.utils import calculateVaR
from pyBacktest.results import BacktestResult
from dataclasses import dataclass

if TYPE_CHECKING:
    from pyBacktest.strategy import Strategy

class Backtest:
    def __init__(
        self,
        ticker: str,
        cash: float | int,
        strategy: 'Strategy',
        commision: float | int = 0.0,
        commisionType: str = "FLAT",
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
        return calculate_commission(self.commisionType, self.commision, price, numShares)

    def cancelOrder(self, order_index: int) -> bool:
        return cancel_order(self, order_index)

    def submitGTCOrder(self, tradeType: TradeType, numShares: int, targetPrice: float) -> Order:
        return submit_gtc_order(self, tradeType, numShares, targetPrice)

    def calculate_trade_cost(self, tradeType: TradeType, numShares: int, price: float = None) -> float:
        validDate = self.formatDate(self.date)
        current_price = price if price is not None else self.hist.loc[validDate].Close

        if tradeType in [TradeType.BUY, TradeType.MARKET_BUY, TradeType.LIMIT_BUY]:
            commission = self.calculateCommision(current_price, numShares)
            total_cost = numShares * current_price + commission
        elif tradeType in [TradeType.SELL, TradeType.MARKET_SELL, TradeType.LIMIT_SELL, TradeType.SHORT_COVER]:
            commission = self.calculateCommision(current_price, numShares)
            total_cost = numShares * current_price - commission
        elif tradeType == TradeType.SHORT_SELL:
            commission = self.calculateCommision(current_price, numShares)
            total_cost = numShares * current_price - commission
        else:
            raise InvalidOrderError(f"Unsupported trade type: {tradeType}")

        return total_cost

    def _check_pending_orders(self, current_price: float):
        for order in self.pending_orders[:]:  # Use slice copy to modify safely
            if not order.active:
                self.pending_orders.remove(order)
                continue

            # Cancel DAY orders that have expired
            if order.duration == 'DAY' and order.orderDate < self.date:
                order.active = False
                self.cancelOrder(self.pending_orders.index(order))
                continue

            try:
                executed = False
                if order.tradeType == TradeType.LIMIT_BUY and current_price <= order.targetPrice:
                    result = self._execute_buy(order.targetPrice, order.numShares, self.date, TradeType.LIMIT_BUY)
                    executed = True
                elif order.tradeType == TradeType.LIMIT_SELL and current_price >= order.targetPrice:
                    result = self._execute_sell(order.targetPrice, order.numShares, self.date, TradeType.LIMIT_SELL)
                    executed = True

                if executed:
                    order.active = False
                    self.pending_orders.remove(order)
                    if hasattr(self.strategy, 'on_order_filled'):
                        self.strategy.on_order_filled(order)
            except Exception as e:
                print(f"Order execution error: {e}")
                order.active = False
                self.pending_orders.remove(order)

    def next(self):
        self.date += self.interval
        valid_date = self.getValidDate(self.date)
        current_price = self.hist.loc[valid_date].Close
        self._check_pending_orders(current_price)
        row = self.hist.loc[valid_date]
        self.strategy.step(row)  
        return row

    def run(self) -> BacktestResult:
        while self.date < self.endDate:
            self.next()
        return BacktestResult(
            final_value=self.totalValue(),
            transactions=self.transactions,
            strategy=self.strategy
        )

    def _execute_buy(self, price: float, numShares: int, valid_date: pd.Timestamp, trade_type: TradeType = TradeType.BUY) -> Holding:
        return execute_buy(self, price, numShares, valid_date, trade_type)

    def _execute_sell(self, price: float, numShares: int, valid_date: pd.Timestamp, trade_type: TradeType = TradeType.SELL) -> Holding:
        return execute_sell(self, price, numShares, valid_date, trade_type)

    def _execute_market_buy(self, numShares: int, valid_date: pd.Timestamp) -> Holding:
        return execute_market_buy(self, numShares, valid_date)

    def _execute_market_sell(self, numShares: int, valid_date: pd.Timestamp) -> Holding:
        return execute_market_sell(self, numShares, valid_date)

    def _execute_short_sell(self, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
        holding = execute_short_sell(self, price, numShares, valid_date)
        holding.shortPosition = True
        return holding

    def _execute_short_cover(self, price: float, numShares: int, valid_date: pd.Timestamp) -> Holding:
        holding = execute_short_cover(self, price, numShares, valid_date)
        holding.shortPosition = False
        return holding

    def trade(self, tradeType: TradeType, numShares: int, price: float = None, duration: str = 'DAY') -> Optional[Holding]:
        validDate = self.formatDate(self.date)
        current_price = price if price is not None else self.hist.loc[validDate].Close

        if tradeType == TradeType.BUY:
            return self._execute_buy(current_price, numShares, validDate)
        elif tradeType == TradeType.SELL:
            return self._execute_sell(current_price, numShares, validDate)
        elif tradeType == TradeType.MARKET_BUY:
            return self._execute_market_buy(numShares, validDate)
        elif tradeType == TradeType.MARKET_SELL:
            return self._execute_market_sell(numShares, validDate)
        elif tradeType == TradeType.SHORT_SELL:
            return self._execute_short_sell(current_price, numShares, validDate)
        elif tradeType == TradeType.SHORT_COVER:
            return self._execute_short_cover(current_price, numShares, validDate)
        elif tradeType in [TradeType.LIMIT_BUY, TradeType.LIMIT_SELL]:
            if price is None:
                raise ValueError("Price must be specified for limit orders")
            order = Order(
                tradeType=tradeType,
                ticker=self.ticker,
                numShares=numShares,
                targetPrice=price,
                duration=duration,
                orderDate=self.date
            )
            self.pending_orders.append(order)
            return None
        else:
            raise InvalidOrderError(f"Unsupported trade type: {tradeType}")

    def totalValue(self) -> float:
        total_value = self.cash
        valid_date = self.formatDate(self.date)
        current_price = self.hist.loc[valid_date].Close
        for holding in self.holdings:
            if holding.shortPosition:
                # Subtract the liability to buy back the shares
                total_value -= current_price * holding.numShares
            else:
                # Add the value of long positions
                total_value += current_price * holding.numShares
        return total_value

    def getPosition(self) -> int:
        position = sum(h.numShares if not h.shortPosition else -h.numShares for h in self.holdings)
        return position

    def calculatePositionSize(self, risk_per_trade: float, stop_loss: float) -> int:
        risk_amount = self.cash * risk_per_trade
        position_size = risk_amount / stop_loss
        return int(position_size)

    def applyStopLoss(self, stop_loss: float):
        valid_date = self.getValidDate(self.date)
        for holding in self.holdings[:]:
            if holding.shortPosition:
                if holding.entryPrice * (1 + stop_loss) <= self.hist.loc[valid_date].Close:
                    self._execute_short_cover(self.hist.loc[valid_date].Close, holding.numShares, valid_date)
            else:
                if holding.entryPrice * (1 - stop_loss) >= self.hist.loc[valid_date].Close:
                    self._execute_sell(self.hist.loc[valid_date].Close, holding.numShares, valid_date)

    def applyTakeProfit(self, take_profit: float):
        valid_date = self.getValidDate(self.date)
        for holding in self.holdings[:]:
            if holding.shortPosition:
                if holding.entryPrice * (1 - take_profit) >= self.hist.loc[valid_date].Close:
                    self._execute_short_cover(self.hist.loc[valid_date].Close, holding.numShares, valid_date)
            else:
                if holding.entryPrice * (1 + take_profit) <= self.hist.loc[valid_date].Close:
                    self._execute_sell(self.hist.loc[valid_date].Close, holding.numShares, valid_date)

    def calculateVaR(self, confidence_level: float = 0.95) -> float:
        returns = self.hist['Close'].pct_change().dropna()
        return calculateVaR(returns, confidence_level)

    def rebalancePortfolio(self, target_allocations: Dict[str, float]):
        valid_date = self.getValidDate(self.date)
        total_value = self.totalValue()
        for ticker, target_allocation in target_allocations.items():
            target_value = total_value * target_allocation
            current_value = sum(h.totalCost for h in self.holdings if h.ticker == ticker)
            if current_value < target_value:
                num_shares_to_buy = (target_value - current_value) / self.hist.loc[valid_date].Close
                self._execute_buy(self.hist.loc[valid_date].Close, int(num_shares_to_buy), valid_date)
            elif current_value > target_value:
                num_shares_to_sell = (current_value - target_value) / self.hist.loc[valid_date].Close
                self._execute_sell(self.hist.loc[valid_date].Close, int(num_shares_to_sell), valid_date)
