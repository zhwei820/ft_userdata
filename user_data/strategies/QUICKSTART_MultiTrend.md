# Multi-Trend Strategy - Quick Start Guide

This guide will help you get started with the Multi-Trend Strategy in just a few minutes.

## Prerequisites

1. **Freqtrade installed** - If not, follow: https://www.freqtrade.io/en/stable/installation/
2. **Exchange account** (Binance recommended for futures trading)
3. **Basic understanding** of trading concepts

## Step-by-Step Setup

### 1. Verify Files

Make sure you have these files in your freqtrade directory:
```
user_data/
├── strategies/
│   ├── multi_trend_strategy.py  ✓ (Strategy file)
│   ├── README_MultiTrend.md     ✓ (Documentation)
│   └── QUICKSTART_MultiTrend.md ✓ (This file)
└── config_multitrend.json       ✓ (Configuration)
```

### 2. Configure Your Exchange

Edit `user_data/config_multitrend.json` and add your API keys:

```json
"exchange": {
  "name": "binance",
  "key": "YOUR_API_KEY_HERE",
  "secret": "YOUR_SECRET_KEY_HERE",
  ...
}
```

**IMPORTANT**: Start with `"dry_run": true` for paper trading!

### 3. Download Historical Data

Before backtesting, download market data:

```bash
# Download 30 days of data for backtesting
freqtrade download-data \
  --config user_data/config_multitrend.json \
  --timerange 20240101- \
  --timeframe 5m
```

### 4. Run a Backtest

Test the strategy on historical data:

```bash
freqtrade backtesting \
  --config user_data/config_multitrend.json \
  --strategy MultiTrendStrategy \
  --timerange 20240101-20240131
```

**What to look for:**
- Total Profit: Should be positive
- Win Rate: Aim for >50%
- Max Drawdown: Should be <20%
- Total Trades: At least 20-30 trades for statistical significance

### 5. Start Paper Trading (Dry Run)

Once backtesting looks good, start paper trading:

```bash
freqtrade trade \
  --config user_data/config_multitrend.json \
  --strategy MultiTrendStrategy
```

**Monitor for at least 1 week** before considering live trading.

### 6. (Optional) Optimize Parameters

Use hyperopt to find better parameters:

```bash
freqtrade hyperopt \
  --config user_data/config_multitrend.json \
  --strategy MultiTrendStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --timerange 20240101-20240131 \
  --spaces buy sell \
  --epochs 100
```

This will take some time but can significantly improve performance.

## Understanding the Strategy

### How It Works

The strategy uses **6 indicators** to confirm trend direction:

1. ✅ **EMA Crossover** - Fast/Slow moving averages
2. ✅ **ADX** - Trend strength measurement
3. ✅ **Supertrend** - Dynamic support/resistance
4. ✅ **MACD** - Momentum indicator
5. ✅ **RSI** - Overbought/oversold levels
6. ✅ **Bollinger Bands** - Volatility measurement

**Entry Signal**: Requires 4 out of 4 confirmations (by default)
- More confirmations = Higher confidence
- Fewer false signals
- Better win rate

### Key Parameters

| Parameter | Default | What it does |
|-----------|---------|--------------|
| `timeframe` | 5m | How often strategy checks for signals |
| `min_trend_confirmations` | 4 | Number of indicators that must agree |
| `max_open_trades` | 3 | Maximum simultaneous trades |
| `stake_amount` | 100 | USDT per trade |
| `stoploss` | -5% | Maximum loss per trade |

## Quick Configuration Tweaks

### For More Trades

Reduce required confirmations in the strategy:
- Change `min_trend_confirmations` from 4 to 3
- Or use hyperopt to optimize

### For Fewer But Safer Trades

- Keep `min_trend_confirmations` at 4
- Increase `adx_threshold` to 30
- Tighten RSI bounds

### For Different Timeframes

Edit `config_multitrend.json`:
```json
"timeframe": "15m"  // Options: "1m", "5m", "15m", "1h", "4h"
```

**Note**: Lower timeframes = more trades, higher timeframes = fewer but potentially stronger signals

## Monitoring Your Bot

### Using FreqUI (Web Interface)

1. Install FreqUI:
```bash
freqtrade install-ui
```

2. Access at: http://localhost:8080
   - Username: `freqtrader`
   - Password: `SuperSecretPassword`

### Command Line Status

```bash
# Check current status
freqtrade status --config user_data/config_multitrend.json

# Show profit
freqtrade profit --config user_data/config_multitrend.json
```

### Telegram Bot (Optional)

Enable Telegram notifications in `config_multitrend.json`:

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your chat_id from [@userinfobot](https://t.me/userinfobot)
3. Update config:
```json
"telegram": {
  "enabled": true,
  "token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

## Common Issues & Solutions

### Issue: "No trades in backtest"

**Solutions:**
- Reduce `min_trend_confirmations` to 3
- Check if you have enough data downloaded
- Try different timeranges
- Verify pairs have sufficient volume

### Issue: "Too many losing trades"

**Solutions:**
- Increase `min_trend_confirmations` to 5
- Reduce `max_open_trades` to 1-2
- Use hyperopt to optimize parameters
- Check market conditions (strategy works best in trending markets)

### Issue: "ModuleNotFoundError: pandas_ta"

**Solution:**
```bash
pip install pandas-ta
pip install technical
```

### Issue: "Exchange API error"

**Solutions:**
- Verify API keys are correct
- Check API permissions (need futures trading enabled)
- Ensure IP is whitelisted on exchange
- Check if you have sufficient balance

## Safety Checklist

Before going live:

- [ ] Tested strategy in backtest with positive results
- [ ] Run dry-run for at least 1 week successfully
- [ ] Understand the strategy logic and parameters
- [ ] Set appropriate `max_open_trades` (start with 1-3)
- [ ] Set conservative `stake_amount` (1-2% of capital)
- [ ] Enable stop losses
- [ ] Have monitoring in place (Telegram/FreqUI)
- [ ] Only risk capital you can afford to lose

## Going Live

When you're ready for live trading:

1. **Update config**:
```json
"dry_run": false,
"dry_run_wallet": 1000,  // Remove or set to your actual balance
```

2. **Start small**:
```json
"max_open_trades": 1,
"stake_amount": 50,  // Or whatever you're comfortable with
```

3. **Start the bot**:
```bash
freqtrade trade \
  --config user_data/config_multitrend.json \
  --strategy MultiTrendStrategy
```

4. **Monitor closely** for the first few trades

## Performance Optimization

### After 1 Week

- Review win rate and profit factor
- Check which pairs perform best
- Identify any patterns in losses
- Consider adjusting timeframe if needed

### After 1 Month

- Run hyperopt with your live trading data
- Refine pair selection
- Adjust risk parameters if needed
- Consider adding more capital if performing well

### Continuous Improvement

- Keep learning about market conditions
- Join freqtrade community for tips
- Test new parameter combinations
- Adapt strategy to changing market conditions

## Resources

- **Full Documentation**: See `README_MultiTrend.md`
- **Freqtrade Docs**: https://www.freqtrade.io/
- **Discord Community**: https://discord.gg/freqtrade
- **GitHub Issues**: Report bugs or request features

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Run backtests and analyze results
3. ✅ Start paper trading (dry-run)
4. ✅ Monitor for 1-2 weeks
5. ✅ Optimize if needed
6. ✅ Go live with small amounts
7. ✅ Scale up gradually as you gain confidence

---

**Remember**: 
- Start small and scale gradually
- Never invest more than you can afford to lose
- Past performance doesn't guarantee future results
- Stay informed and keep learning

Good luck with your trading! 🚀

