from pyBacktest.tradeTypes import TradeType, Order, Transaction
from datetime import datetime

def cancel_order(backtest, order_index: int) -> bool:
    if 0 <= order_index < len(backtest.pending_orders):
        order = backtest.pending_orders[order_index]
        order.active = False
        backtest.transactions.append(
            Transaction(
                tradeType=TradeType.Cancel,
                ticker=order.ticker,
                commission=0,
                executedSuccessfully=True,
                numShares=order.numShares,
                pricePerShare=order.targetPrice,
                totalCost=0,
                date=backtest.date,
                notes="Order canceled"
            )
        )
        return True
    return False

def submit_gtc_order(backtest, tradeType: TradeType, numShares: int, targetPrice: float) -> Order:
    order = Order(
        tradeType=tradeType,
        ticker=backtest.ticker,
        numShares=numShares,
        targetPrice=targetPrice,
        duration='GTC',
        orderDate=backtest.date
    )
    backtest.pending_orders.append(order)
    return order