"""
Multi-Trend Strategy with Long/Short Trading
Uses multiple trend detection methods to improve win rate
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    informative,
    DecimalParameter,
    IntParameter,
    CategoricalParameter,
)

import pandas_ta as ta
from technical import qtpylib


class MultiTrendStrategy(IStrategy):
    """
    Multi-Trend Strategy using multiple methods to determine trend direction:
    1. Moving Averages (EMA crossover)
    2. ADX (Trend strength)
    3. Supertrend
    4. MACD
    5. RSI (for overbought/oversold)
    6. Bollinger Bands (volatility breakout)
    
    Trades both LONG and SHORT positions based on trend confluence
    """

    INTERFACE_VERSION = 3

    # Enable short trading
    can_short: bool = True

    # ROI table - more conservative for multi-timeframe strategy
    minimal_roi = {
        "0": 0.08,    # 8% profit target
        "30": 0.05,   # 5% after 30 minutes
        "60": 0.03,   # 3% after 1 hour
        "120": 0.01,  # 1% after 2 hours
    }

    # Stoploss
    stoploss = -0.05  # 5% stop loss

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    # Timeframe
    timeframe = "5m"

    # Run populate_indicators() only for new candle
    process_only_new_candles = True

    # Exit signal configuration
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # Hyperoptable parameters
    # Moving Average periods
    ema_fast_period = IntParameter(8, 20, default=12, space="buy")
    ema_slow_period = IntParameter(20, 50, default=26, space="buy")
    ema_trend_period = IntParameter(50, 200, default=100, space="buy")
    
    # ADX parameters
    adx_period = IntParameter(10, 20, default=14, space="buy")
    adx_threshold = IntParameter(20, 35, default=25, space="buy")
    
    # RSI parameters
    rsi_period = IntParameter(10, 20, default=14, space="buy")
    rsi_overbought = IntParameter(65, 80, default=70, space="sell")
    rsi_oversold = IntParameter(20, 35, default=30, space="buy")
    
    # MACD parameters
    macd_fast = IntParameter(8, 15, default=12, space="buy")
    macd_slow = IntParameter(20, 30, default=26, space="buy")
    macd_signal = IntParameter(7, 12, default=9, space="buy")
    
    # Supertrend parameters
    supertrend_period = IntParameter(7, 14, default=10, space="buy")
    supertrend_multiplier = DecimalParameter(2.0, 4.0, default=3.0, space="buy")
    
    # Bollinger Bands parameters
    bb_period = IntParameter(15, 25, default=20, space="buy")
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space="buy")
    
    # Minimum number of trend confirmations required
    min_trend_confirmations = IntParameter(3, 5, default=4, space="buy")

    # Plot configuration
    plot_config = {
        "main_plot": {
            "ema_fast": {"color": "blue"},
            "ema_slow": {"color": "red"},
            "ema_trend": {"color": "orange"},
            "supertrend": {"color": "green"},
            "bb_upper": {"color": "gray"},
            "bb_lower": {"color": "gray"},
        },
        "subplots": {
            "MACD": {
                "macd": {"color": "blue"},
                "macd_signal": {"color": "orange"},
                "macd_hist": {"color": "gray", "type": "bar"},
            },
            "RSI": {
                "rsi": {"color": "purple"},
            },
            "ADX": {
                "adx": {"color": "green"},
                "di_plus": {"color": "blue"},
                "di_minus": {"color": "red"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all technical indicators for trend detection
        """
        
        # 1. Moving Averages (EMA)
        dataframe["ema_fast"] = ta.ema(dataframe["close"], length=self.ema_fast_period.value)
        dataframe["ema_slow"] = ta.ema(dataframe["close"], length=self.ema_slow_period.value)
        dataframe["ema_trend"] = ta.ema(dataframe["close"], length=self.ema_trend_period.value)
        
        # 2. ADX - Average Directional Index (trend strength)
        adx_data = ta.adx(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=self.adx_period.value
        )
        if adx_data is not None:
            dataframe["adx"] = adx_data[f"ADX_{self.adx_period.value}"]
            dataframe["di_plus"] = adx_data[f"DMP_{self.adx_period.value}"]
            dataframe["di_minus"] = adx_data[f"DMN_{self.adx_period.value}"]
        else:
            dataframe["adx"] = 0
            dataframe["di_plus"] = 0
            dataframe["di_minus"] = 0
        
        # 3. Supertrend
        supertrend_data = ta.supertrend(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=self.supertrend_period.value,
            multiplier=self.supertrend_multiplier.value
        )
        if supertrend_data is not None:
            dataframe["supertrend"] = supertrend_data[f"SUPERT_{self.supertrend_period.value}_{self.supertrend_multiplier.value}"]
            dataframe["supertrend_direction"] = supertrend_data[f"SUPERTd_{self.supertrend_period.value}_{self.supertrend_multiplier.value}"]
        else:
            dataframe["supertrend"] = dataframe["close"]
            dataframe["supertrend_direction"] = 1
        
        # 4. MACD
        macd_data = ta.macd(
            dataframe["close"],
            fast=self.macd_fast.value,
            slow=self.macd_slow.value,
            signal=self.macd_signal.value
        )
        if macd_data is not None:
            dataframe["macd"] = macd_data[f"MACD_{self.macd_fast.value}_{self.macd_slow.value}_{self.macd_signal.value}"]
            dataframe["macd_signal"] = macd_data[f"MACDs_{self.macd_fast.value}_{self.macd_slow.value}_{self.macd_signal.value}"]
            dataframe["macd_hist"] = macd_data[f"MACDh_{self.macd_fast.value}_{self.macd_slow.value}_{self.macd_signal.value}"]
        else:
            dataframe["macd"] = 0
            dataframe["macd_signal"] = 0
            dataframe["macd_hist"] = 0
        
        # 5. RSI
        dataframe["rsi"] = ta.rsi(dataframe["close"], length=self.rsi_period.value)
        
        # 6. Bollinger Bands
        bb_data = ta.bbands(
            dataframe["close"],
            length=self.bb_period.value,
            std=self.bb_std.value
        )
        if bb_data is not None:
            dataframe["bb_upper"] = bb_data[f"BBU_{self.bb_period.value}_{self.bb_std.value}"]
            dataframe["bb_middle"] = bb_data[f"BBM_{self.bb_period.value}_{self.bb_std.value}"]
            dataframe["bb_lower"] = bb_data[f"BBL_{self.bb_period.value}_{self.bb_std.value}"]
            dataframe["bb_width"] = (dataframe["bb_upper"] - dataframe["bb_lower"]) / dataframe["bb_middle"]
        else:
            dataframe["bb_upper"] = dataframe["close"] * 1.02
            dataframe["bb_middle"] = dataframe["close"]
            dataframe["bb_lower"] = dataframe["close"] * 0.98
            dataframe["bb_width"] = 0.04
        
        # 7. Volume indicators
        dataframe["volume_sma"] = ta.sma(dataframe["volume"], length=20)
        
        # Calculate individual trend signals
        dataframe["trend_ema"] = np.where(
            (dataframe["ema_fast"] > dataframe["ema_slow"]) & 
            (dataframe["close"] > dataframe["ema_trend"]),
            1,  # Bullish
            np.where(
                (dataframe["ema_fast"] < dataframe["ema_slow"]) & 
                (dataframe["close"] < dataframe["ema_trend"]),
                -1,  # Bearish
                0  # Neutral
            )
        )
        
        dataframe["trend_adx"] = np.where(
            (dataframe["adx"] > self.adx_threshold.value) & 
            (dataframe["di_plus"] > dataframe["di_minus"]),
            1,  # Bullish with strong trend
            np.where(
                (dataframe["adx"] > self.adx_threshold.value) & 
                (dataframe["di_plus"] < dataframe["di_minus"]),
                -1,  # Bearish with strong trend
                0  # Weak trend
            )
        )
        
        dataframe["trend_supertrend"] = np.where(
            dataframe["supertrend_direction"] == 1,
            1,  # Bullish
            -1  # Bearish
        )
        
        dataframe["trend_macd"] = np.where(
            (dataframe["macd"] > dataframe["macd_signal"]) & 
            (dataframe["macd_hist"] > 0),
            1,  # Bullish
            np.where(
                (dataframe["macd"] < dataframe["macd_signal"]) & 
                (dataframe["macd_hist"] < 0),
                -1,  # Bearish
                0  # Neutral
            )
        )
        
        # Calculate trend score (sum of all trend indicators)
        dataframe["trend_score"] = (
            dataframe["trend_ema"] +
            dataframe["trend_adx"] +
            dataframe["trend_supertrend"] +
            dataframe["trend_macd"]
        )
        
        # Trend strength (0-4, number of confirming indicators)
        dataframe["trend_strength_long"] = (
            (dataframe["trend_ema"] == 1).astype(int) +
            (dataframe["trend_adx"] == 1).astype(int) +
            (dataframe["trend_supertrend"] == 1).astype(int) +
            (dataframe["trend_macd"] == 1).astype(int)
        )
        
        dataframe["trend_strength_short"] = (
            (dataframe["trend_ema"] == -1).astype(int) +
            (dataframe["trend_adx"] == -1).astype(int) +
            (dataframe["trend_supertrend"] == -1).astype(int) +
            (dataframe["trend_macd"] == -1).astype(int)
        )
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry conditions for long and short positions
        """
        
        # LONG ENTRY CONDITIONS
        # Require multiple confirmations for trend
        dataframe.loc[
            (
                # Multiple trend confirmations
                (dataframe["trend_strength_long"] >= self.min_trend_confirmations.value) &
                
                # RSI not overbought
                (dataframe["rsi"] < self.rsi_overbought.value) &
                (dataframe["rsi"] > self.rsi_oversold.value) &
                
                # Price action
                (dataframe["close"] > dataframe["open"]) &  # Bullish candle
                
                # Volume confirmation
                (dataframe["volume"] > dataframe["volume_sma"]) &
                
                # Bollinger Bands - not overextended
                (dataframe["close"] > dataframe["bb_lower"]) &
                (dataframe["close"] < dataframe["bb_upper"]) &
                
                # Additional confirmation: price above EMA trend
                (dataframe["close"] > dataframe["ema_trend"]) &
                
                # MACD momentum
                (dataframe["macd_hist"] > 0)
            ),
            "enter_long",
        ] = 1

        # SHORT ENTRY CONDITIONS
        # Require multiple confirmations for trend
        dataframe.loc[
            (
                # Multiple trend confirmations
                (dataframe["trend_strength_short"] >= self.min_trend_confirmations.value) &
                
                # RSI not oversold
                (dataframe["rsi"] > self.rsi_oversold.value) &
                (dataframe["rsi"] < self.rsi_overbought.value) &
                
                # Price action
                (dataframe["close"] < dataframe["open"]) &  # Bearish candle
                
                # Volume confirmation
                (dataframe["volume"] > dataframe["volume_sma"]) &
                
                # Bollinger Bands - not overextended
                (dataframe["close"] < dataframe["bb_upper"]) &
                (dataframe["close"] > dataframe["bb_lower"]) &
                
                # Additional confirmation: price below EMA trend
                (dataframe["close"] < dataframe["ema_trend"]) &
                
                # MACD momentum
                (dataframe["macd_hist"] < 0)
            ),
            "enter_short",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit conditions for long and short positions
        """
        
        # EXIT LONG CONDITIONS
        dataframe.loc[
            (
                # Trend reversal signals
                (
                    # EMA crossover bearish
                    (dataframe["ema_fast"] < dataframe["ema_slow"]) |
                    
                    # Supertrend turns bearish
                    (dataframe["supertrend_direction"] == -1) |
                    
                    # MACD bearish crossover
                    (
                        (dataframe["macd"] < dataframe["macd_signal"]) &
                        (dataframe["macd_hist"] < 0)
                    ) |
                    
                    # RSI overbought
                    (dataframe["rsi"] > self.rsi_overbought.value) |
                    
                    # Price breaks below trend EMA
                    (dataframe["close"] < dataframe["ema_trend"])
                ) &
                
                # Confirm with volume
                (dataframe["volume"] > dataframe["volume_sma"] * 0.8)
            ),
            "exit_long",
        ] = 1

        # EXIT SHORT CONDITIONS
        dataframe.loc[
            (
                # Trend reversal signals
                (
                    # EMA crossover bullish
                    (dataframe["ema_fast"] > dataframe["ema_slow"]) |
                    
                    # Supertrend turns bullish
                    (dataframe["supertrend_direction"] == 1) |
                    
                    # MACD bullish crossover
                    (
                        (dataframe["macd"] > dataframe["macd_signal"]) &
                        (dataframe["macd_hist"] > 0)
                    ) |
                    
                    # RSI oversold
                    (dataframe["rsi"] < self.rsi_oversold.value) |
                    
                    # Price breaks above trend EMA
                    (dataframe["close"] > dataframe["ema_trend"])
                ) &
                
                # Confirm with volume
                (dataframe["volume"] > dataframe["volume_sma"] * 0.8)
            ),
            "exit_short",
        ] = 1

        return dataframe

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: Optional[str],
        side: str,
        **kwargs
    ) -> bool:
        """
        Additional confirmation before entering trade
        Can be used to add additional filters or risk management
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        
        if len(dataframe) < 1:
            return False
            
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Ensure we have strong trend confirmation
        if side == "long":
            trend_val = last_candle.get("trend_strength_long", 0)
            return isinstance(trend_val, (int, float)) and trend_val >= self.min_trend_confirmations.value
        elif side == "short":
            trend_val = last_candle.get("trend_strength_short", 0)
            return isinstance(trend_val, (int, float)) and trend_val >= self.min_trend_confirmations.value
            
        return True

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> Optional[float]:
        """
        Dynamic stoploss based on trend strength
        Tighter stops when trend weakens
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        
        if len(dataframe) < 1:
            return None
            
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Get trend strength for current position
        if trade.is_short:
            trend_strength = last_candle.get("trend_strength_short", 0)
        else:
            trend_strength = last_candle.get("trend_strength_long", 0)
        
        # Ensure trend_strength is numeric
        if not isinstance(trend_strength, (int, float)):
            return None
        
        # Tighten stop if trend is weakening
        if trend_strength < 2:  # Less than 2 confirmations
            return -0.03  # 3% stop
        elif trend_strength < 3:
            return -0.04  # 4% stop
        else:
            return -0.05  # 5% stop (default)
