# Multi-Trend Strategy - Documentation

## Overview

The Multi-Trend Strategy is an advanced freqtrade strategy that uses multiple technical indicators to confirm trend direction before entering trades. It supports both LONG and SHORT positions and requires trend confluence from multiple indicators to improve win rates.

## Strategy Features

### 1. **Multiple Trend Detection Methods**

The strategy uses 6 different methods to detect and confirm trends:

- **Moving Averages (EMA)**: Fast (12), Slow (26), and Trend (100) EMAs for trend direction
- **ADX (Average Directional Index)**: Measures trend strength (threshold: 25)
- **Supertrend**: Dynamic support/resistance indicator
- **MACD**: Momentum indicator for trend confirmation
- **RSI**: Relative Strength Index for overbought/oversold conditions
- **Bollinger Bands**: Volatility and price extremes

### 2. **Trend Confluence System**

The strategy calculates a "trend strength" score (0-4) based on how many indicators agree on the trend direction:
- **4 confirmations**: All indicators agree (strongest signal)
- **3 confirmations**: Most indicators agree (strong signal)
- **2 confirmations**: Some agreement (weak signal)
- **0-1 confirmations**: No clear trend (no trade)

By default, the strategy requires **4 confirmations** before entering a trade.

### 3. **Long and Short Trading**

- **LONG positions**: Entered when bullish trend is confirmed by multiple indicators
- **SHORT positions**: Entered when bearish trend is confirmed by multiple indicators

### 4. **Risk Management Features**

- **Dynamic Stop Loss**: Adjusts based on trend strength
  - Strong trend (4 confirmations): 5% stop loss
  - Medium trend (3 confirmations): 4% stop loss
  - Weak trend (2 confirmations): 3% stop loss
  
- **Trailing Stop**: Enabled with 1% profit protection after 2% gain

- **ROI Table** (Minimal Return on Investment):
  - 8% target at entry
  - 5% after 30 minutes
  - 3% after 1 hour
  - 1% after 2 hours

## Entry Conditions

### LONG Entry
Requires ALL of the following:
- ✅ 4 (or configured) trend indicators showing bullish
- ✅ RSI between 30-70 (not overbought)
- ✅ Bullish candle (close > open)
- ✅ Volume above average
- ✅ Price between Bollinger Bands
- ✅ Price above long-term EMA trend
- ✅ MACD histogram positive

### SHORT Entry
Requires ALL of the following:
- ✅ 4 (or configured) trend indicators showing bearish
- ✅ RSI between 30-70 (not oversold)
- ✅ Bearish candle (close < open)
- ✅ Volume above average
- ✅ Price between Bollinger Bands
- ✅ Price below long-term EMA trend
- ✅ MACD histogram negative

## Exit Conditions

### LONG Exit
Triggered by ANY of the following:
- ❌ EMA bearish crossover (fast < slow)
- ❌ Supertrend turns bearish
- ❌ MACD bearish crossover
- ❌ RSI overbought (>70)
- ❌ Price breaks below trend EMA
- Plus volume confirmation

### SHORT Exit
Triggered by ANY of the following:
- ❌ EMA bullish crossover (fast > slow)
- ❌ Supertrend turns bullish
- ❌ MACD bullish crossover
- ❌ RSI oversold (<30)
- ❌ Price breaks above trend EMA
- Plus volume confirmation

## Configuration

### Basic Setup

1. **Copy the strategy file**:
   ```bash
   # The strategy is already in: user_data/strategies/multi_trend_strategy.py
   ```

2. **Create/Update config.json**:
   ```json
   {
     "trading_mode": "futures",
     "margin_mode": "isolated",
     "max_open_trades": 3,
     "stake_currency": "USDT",
     "stake_amount": 100,
     "dry_run": true,
     "strategy": "MultiTrendStrategy",
     "exchange": {
       "name": "binance",
       "key": "your-api-key",
       "secret": "your-api-secret",
       "ccxt_config": {},
       "ccxt_async_config": {}
     },
     "pairlists": [
       {
         "method": "StaticPairList"
       }
     ],
     "pairs": ["BTC/USDT", "ETH/USDT"],
     "timeframe": "5m"
   }
   ```

### Hyperoptable Parameters

You can optimize these parameters using hyperopt:

```python
# Moving Averages
ema_fast_period = 8-20 (default: 12)
ema_slow_period = 20-50 (default: 26)
ema_trend_period = 50-200 (default: 100)

# ADX
adx_period = 10-20 (default: 14)
adx_threshold = 20-35 (default: 25)

# RSI
rsi_period = 10-20 (default: 14)
rsi_overbought = 65-80 (default: 70)
rsi_oversold = 20-35 (default: 30)

# MACD
macd_fast = 8-15 (default: 12)
macd_slow = 20-30 (default: 26)
macd_signal = 7-12 (default: 9)

# Supertrend
supertrend_period = 7-14 (default: 10)
supertrend_multiplier = 2.0-4.0 (default: 3.0)

# Bollinger Bands
bb_period = 15-25 (default: 20)
bb_std = 1.5-2.5 (default: 2.0)

# Trend Confirmation
min_trend_confirmations = 3-5 (default: 4)
```

## Usage Examples

### 1. Backtesting

```bash
# Basic backtest
freqtrade backtesting \
  --strategy MultiTrendStrategy \
  --timerange 20230101-20231231 \
  --timeframe 5m

# With specific pairs
freqtrade backtesting \
  --strategy MultiTrendStrategy \
  --pairs BTC/USDT ETH/USDT \
  --timerange 20230101-20231231
```

### 2. Dry Run (Paper Trading)

```bash
freqtrade trade \
  --strategy MultiTrendStrategy \
  --config config.json \
  --dry-run
```

### 3. Live Trading

```bash
freqtrade trade \
  --strategy MultiTrendStrategy \
  --config config.json
```

### 4. Hyperopt (Parameter Optimization)

```bash
# Optimize entry parameters
freqtrade hyperopt \
  --strategy MultiTrendStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --timerange 20230101-20231231 \
  --spaces buy \
  --epochs 100

# Optimize all parameters
freqtrade hyperopt \
  --strategy MultiTrendStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --timerange 20230101-20231231 \
  --spaces buy sell roi stoploss \
  --epochs 500
```

## Performance Tips

### 1. **Timeframe Selection**
- **5m**: More trades, requires closer monitoring
- **15m**: Balanced approach (recommended for beginners)
- **1h**: Fewer but potentially more reliable signals

### 2. **Pair Selection**
- Focus on liquid pairs with good volatility
- Recommended: BTC/USDT, ETH/USDT, major altcoins
- Avoid low-volume pairs

### 3. **Risk Management**
- Start with small position sizes (1-2% of capital per trade)
- Use max_open_trades to limit exposure
- Enable trailing stop for profit protection

### 4. **Market Conditions**
- This strategy works best in trending markets
- May generate false signals in ranging/choppy markets
- Consider using with market regime filters

## Monitoring and Maintenance

### Key Metrics to Watch

1. **Win Rate**: Should be >50% with proper settings
2. **Profit Factor**: Aim for >1.5
3. **Max Drawdown**: Keep below 20%
4. **Average Trade Duration**: Depends on timeframe
5. **Risk/Reward Ratio**: Target >1.5:1

### Regular Tasks

- Review trades weekly
- Check for any significant losses
- Adjust parameters if market conditions change
- Update stop losses based on volatility

## Troubleshooting

### Issue: Too few trades
**Solution**: 
- Reduce `min_trend_confirmations` from 4 to 3
- Adjust timeframe to capture more opportunities
- Review pair selection

### Issue: Too many losing trades
**Solution**:
- Increase `min_trend_confirmations` to require stronger signals
- Tighten RSI bounds
- Increase ADX threshold
- Use hyperopt to find better parameters

### Issue: Large drawdowns
**Solution**:
- Reduce position size
- Enable stricter stop losses
- Reduce `max_open_trades`
- Add additional filters (e.g., volume, volatility)

## Advanced Customization

### Adding Additional Filters

You can modify the `populate_entry_trend` method to add custom filters:

```python
# Example: Add ATR filter for volatility
dataframe["atr"] = ta.atr(dataframe["high"], dataframe["low"], 
                          dataframe["close"], length=14)
dataframe["atr_sma"] = ta.sma(dataframe["atr"], length=20)

# Then in entry conditions add:
(dataframe["atr"] > dataframe["atr_sma"]) &  # High volatility
```

### Multi-Timeframe Analysis

You can use the `@informative` decorator to add higher timeframe confirmation:

```python
@informative('1h')
def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    dataframe['ema_trend_1h'] = ta.ema(dataframe['close'], length=100)
    return dataframe
```

## Disclaimer

**IMPORTANT**: 
- This strategy is provided for educational purposes
- Always test thoroughly in dry-run mode first
- Past performance does not guarantee future results
- Never invest more than you can afford to lose
- Cryptocurrency trading carries significant risk
- Use proper risk management and position sizing

## Support and Resources

- **Freqtrade Documentation**: https://www.freqtrade.io/
- **Strategy Guide**: https://www.freqtrade.io/en/stable/strategy-customization/
- **Discord Community**: https://discord.gg/freqtrade

## Version History

- **v1.0** (2025-01-11): Initial release with multi-trend detection and long/short support



"apiKey": "039db512-8c2b-48d1-ae61-bd22794594ff",
"secret": "96B615D4A3A1073A149A576115993BCF",


token  = "6791049513:AAGK-I3gUz1cdJwAQF9WAlmRz4_hYtQp890"
chatId = "1944697763"