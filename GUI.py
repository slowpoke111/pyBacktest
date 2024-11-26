import customtkinter as ctk
from typing import Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import webbrowser
import tempfile
import os
from pyBacktest.backtest import Backtest
from pyBacktest.strategy import Strategy

class BacktestGUI:
    def __init__(self, strategy: Strategy) -> None:
        self.strategy: Strategy = strategy
        self.backtest: Optional[Backtest] = None
        self.setup_gui()

    def setup_gui(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window: ctk.CTk = ctk.CTk()
        self.window.title("Backtest Visualization")
        self.window.geometry("800x100")

        self.setup_frame: ctk.CTkFrame = ctk.CTkFrame(self.window)
        self.setup_frame.pack(fill="x", padx=10, pady=5)

        self.control_frame: ctk.CTkFrame = ctk.CTkFrame(self.window)
        self.control_frame.pack(fill="x", padx=10, pady=5)

        self.setup_inputs()

        self.run_button: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="Run Backtest", 
            command=self.run_backtest
        )
        self.run_button.pack(side="left", padx=5)

        self.chart_button: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="Show Chart", 
            command=self.show_chart,
            state="disabled"
        )
        self.chart_button.pack(side="left", padx=5)

    def setup_inputs(self) -> None:
        ctk.CTkLabel(self.setup_frame, text="Ticker:").pack(side="left", padx=5)
        self.ticker_var: ctk.StringVar = ctk.StringVar(value="AAPL")
        self.ticker_entry: ctk.CTkEntry = ctk.CTkEntry(
            self.setup_frame, 
            textvariable=self.ticker_var,
            width=80
        )
        self.ticker_entry.pack(side="left", padx=5)

        ctk.CTkLabel(self.setup_frame, text="Initial Cash:").pack(side="left", padx=5)
        self.cash_var: ctk.StringVar = ctk.StringVar(value="10000")
        self.cash_entry: ctk.CTkEntry = ctk.CTkEntry(
            self.setup_frame, 
            textvariable=self.cash_var,
            width=100
        )
        self.cash_entry.pack(side="left", padx=5)

        ctk.CTkLabel(self.setup_frame, text="Start Date:").pack(side="left", padx=5)
        self.start_date_var: ctk.StringVar = ctk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.start_date_entry: ctk.CTkEntry = ctk.CTkEntry(
            self.setup_frame, 
            textvariable=self.start_date_var,
            width=100
        )
        self.start_date_entry.pack(side="left", padx=5)

        ctk.CTkLabel(self.setup_frame, text="End Date:").pack(side="left", padx=5)
        self.end_date_var: ctk.StringVar = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_date_entry: ctk.CTkEntry = ctk.CTkEntry(
            self.setup_frame, 
            textvariable=self.end_date_var,
            width=100
        )
        self.end_date_entry.pack(side="left", padx=5)

    def run_backtest(self) -> None:
        try:
            self.backtest = Backtest(
                ticker=self.ticker_var.get(),
                cash=float(self.cash_var.get()),
                strategy=self.strategy,
                startDate=datetime.strptime(self.start_date_var.get(), "%Y-%m-%d"),
                endDate=datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            )
            self.results = self.backtest.run()
            self.chart_button.configure(state="normal")
        except Exception as e:
            self.show_error(f"Backtest Error: {str(e)}")

    def create_chart(self) -> go.Figure:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Stock Price', 'Portfolio Value', 'Trading Activity'),
            row_heights=[0.3, 0.4, 0.3]
        )

        dates = self.backtest.hist.index
        close_prices = self.backtest.hist['Close']
        portfolio_values = []
        cash_values = []

        for date in dates:
            self.backtest.date = date
            portfolio_values.append(self.backtest.totalValue())
            cash_values.append(self.backtest.cash)

        fig.add_trace(
            go.Scatter(
                x=dates, 
                y=close_prices,
                name="Price",
                line=dict(color='lightgray')
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=portfolio_values,
                name="Portfolio Value",
                line=dict(color='green')
            ),
            row=2, col=1
        )

        buy_dates = []
        buy_prices = []
        sell_dates = []
        sell_prices = []

        for t in self.backtest.transactions:
            if t.tradeType.name.endswith('BUY'):
                buy_dates.append(t.date)
                buy_prices.append(t.pricePerShare)
            elif t.tradeType.name.endswith('SELL'):
                sell_dates.append(t.date)
                sell_prices.append(t.pricePerShare)

        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='Buy',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='Sell',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Bar(
                x=dates,
                y=self.backtest.hist['Volume'],
                name='Volume'
            ),
            row=3, col=1
        )

        fig.update_layout(
            title=f"Backtest Results - {self.backtest.ticker}",
            xaxis_title="Date",
            yaxis_title="Price / Value ($)",
            height=800
        )

        return fig

    def show_chart(self) -> None:
        if not self.backtest:
            return

        try:
            fig = self.create_chart()
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, 'backtest_chart.html')
            fig.write_html(temp_path)
            webbrowser.open('file://' + temp_path)

        except Exception as e:
            self.show_error(f"Chart Error: {str(e)}")

    def show_error(self, message: str) -> None:
        error_window = ctk.CTkToplevel(self.window)
        error_window.title("Error")
        error_window.geometry("400x200")
        
        ctk.CTkLabel(
            error_window,
            text=message,
            wraplength=350
        ).pack(padx=20, pady=20)
        
        ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        ).pack(pady=10)

    def run(self) -> None:
        self.window.mainloop()
