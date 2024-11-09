from datetime import datetime
from pyBacktest.backtest import Backtest
from pyBacktest.strategy import SimpleMovingAverageCrossover

if __name__ == "__main__":
    backtest = Backtest(
        "AAPL",
        100000.0,
        strategy=SimpleMovingAverageCrossover(),
        startDate=datetime(2023, 1, 1),
        endDate=datetime(2024, 1, 1)
    )
    
    results = backtest.run()
    print(f"Final Portfolio Value: ${results['final_value']:,.2f}")
