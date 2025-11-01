.PHONY: help pull up down restart ps logs logs-tail build update
.PHONY: create-userdir new-config
.PHONY: backtest backtest-show download-data list-data list-strategies
.PHONY: plot-profit plot-dataframe
.PHONY: shell trade dry-run

# Default configuration
CONFIG ?= user_data/config_multitrend.json
STRATEGY ?= MultiTrendStrategy
TIMEFRAME ?= 5m
PAIRS ?= SOL/USDT:USDT
EXCHANGE ?= okx
DAYS ?= 30
TIMERANGE ?= $(shell date -u -v-30d '+%Y%m%d' 2>/dev/null || date -u -d '30 days ago' '+%Y%m%d')-$(shell date -u '+%Y%m%d')

echo:
	@echo $(TIMERANGE)

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Management

pull: ## Pull the latest freqtrade docker image
	docker compose pull

up: ## Start freqtrade in detached mode
	docker compose up -d

down: ## Stop freqtrade
	docker compose down

restart: ## Restart freqtrade
	docker compose restart

ps: ## Show running containers
	docker compose ps

logs: ## Show all logs
	docker compose logs

logs-tail: ## Show and follow logs
	docker compose logs -f

build: ## Build custom docker image
	docker compose build --pull

update: pull restart ## Update freqtrade to latest version

##@ Setup

# create-userdir: ## Create user directory structure
# 	docker compose run --rm freqtrade create-userdir --userdir user_data

# new-config: ## Create new configuration (interactive)
# 	docker compose run --rm freqtrade new-config --config $(CONFIG)

##@ Trading

run: up ## Start bot in live/dry-run mode (alias for 'up')

trade: ## Start bot in live trading mode (use 'make up' instead)
	@echo "Use 'make up' or 'make run' to start trading in detached mode"
	docker compose up -d

dry-run: ## Start bot in dry-run mode
	docker compose run --rm freqtrade trade --config $(CONFIG) --strategy $(STRATEGY) --dry-run

##@ Data Management

download-data: ## Download historical data (PAIRS, EXCHANGE, DAYS, TIMEFRAME)
	docker compose run --rm freqtrade download-data \
		--config $(CONFIG) \
		--pairs $(PAIRS) \
		--exchange $(EXCHANGE) \
		--days $(DAYS) \
		-t $(TIMEFRAME) \
		--data-format-ohlcv json

list-data: ## List available data
	docker compose run --rm freqtrade list-data --exchange $(EXCHANGE)

list-pairs: ## List available pairs for exchange
	docker compose run --rm freqtrade list-pairs --exchange $(EXCHANGE) --quote USDT --print-json

list-timeframes: ## List available timeframes for exchange
	docker compose run --rm freqtrade list-timeframes --exchange $(EXCHANGE)

list-exchanges: ## List available exchanges
	docker compose run --rm freqtrade list-exchanges

##@ Backtesting

backtest: ## Run backtesting (CONFIG, STRATEGY, TIMERANGE, TIMEFRAME)
	docker compose run --rm freqtrade backtesting \
		--config $(CONFIG) \
		--strategy $(STRATEGY) \
		$(if $(TIMERANGE),--timerange $(TIMERANGE),) \
		-i $(TIMEFRAME) \
		--data-format-ohlcv json

backtest-show: ## Show backtest results
	docker compose run --rm freqtrade backtesting-show

backtest-analysis: ## Analyze backtest results
	docker compose run --rm freqtrade backtesting-analysis

##@ Strategy Management

list-strategies: ## List available strategies
	docker compose run --rm freqtrade list-strategies --userdir user_data

new-strategy: ## Create new strategy from template (NAME)
	docker compose run --rm freqtrade new-strategy --strategy $(NAME) --userdir user_data

test-strategy: ## Test strategy for common errors
	docker compose run --rm freqtrade test-strategy --strategy $(STRATEGY) --config $(CONFIG)

##@ Plotting

plot-profit: ## Plot profit chart
	docker compose run --rm freqtrade plot-profit --config $(CONFIG) --strategy $(STRATEGY)

plot-dataframe: ## Plot dataframe with indicators (PAIRS, TIMERANGE)
	docker compose run --rm freqtrade plot-dataframe \
		--config $(CONFIG) \
		--strategy $(STRATEGY) \
		$(if $(PAIRS),-p $(PAIRS),) \
		$(if $(TIMERANGE),--timerange $(TIMERANGE),)

##@ Hyperopt & Analysis

hyperopt: ## Run hyperopt optimization (EPOCHS)
	docker compose run --rm freqtrade hyperopt \
		--config $(CONFIG) \
		--strategy $(STRATEGY) \
		--hyperopt-loss SharpeHyperOptLoss \
		--epochs $(or $(EPOCHS),100)

hyperopt-list: ## List hyperopt results
	docker compose run --rm freqtrade hyperopt-list

hyperopt-show: ## Show hyperopt result details (INDEX)
	docker compose run --rm freqtrade hyperopt-show -n $(or $(INDEX),-1)

edge: ## Run edge position sizing
	docker compose run --rm freqtrade edge --config $(CONFIG) --strategy $(STRATEGY)

lookahead-analysis: ## Run lookahead analysis
	docker compose run --rm freqtrade lookahead-analysis --strategy $(STRATEGY)

recursive-analysis: ## Run recursive analysis
	docker compose run --rm freqtrade recursive-analysis --strategy $(STRATEGY)

##@ Database & Trades

show-trades: ## Show trades from database
	docker compose run --rm freqtrade show-trades --config $(CONFIG)

convert-db: ## Convert database to new format
	docker compose run --rm freqtrade convert-db

##@ Utilities

shell: ## Open shell in freqtrade container
	docker compose run --rm freqtrade /bin/bash

show-config: ## Show configuration
	docker compose run --rm freqtrade show-config --config $(CONFIG)

version: ## Show freqtrade version
	docker compose run --rm freqtrade --version

install-ui: ## Install FreqUI
	docker compose run --rm freqtrade install-ui

webserver: ## Start webserver for API/UI
	docker compose run --rm freqtrade webserver --config $(CONFIG)

test-pairlist: ## Test pairlist configuration
	docker compose run --rm freqtrade test-pairlist --config $(CONFIG)

##@ Quick Start Examples

example-download: ## Example: Download 5 days of ETH/BTC 1h data from Binance
	docker compose run --rm freqtrade download-data --pairs ETH/BTC --exchange binance --days 5 -t 1h

example-backtest: ## Example: Backtest SampleStrategy on 5m timeframe
	docker compose run --rm freqtrade backtesting \
		--config user_data/config.json \
		--strategy SampleStrategy \
		--timerange 20190801-20191001 \
		-i 5m

quick-start: create-userdir new-config ## Quick start: Create userdir and config

##@ Jupyter Lab (Data Analysis)

jupyter-up: ## Start Jupyter Lab server
	docker compose -f docker/docker-compose-jupyter.yml up

jupyter-down: ## Stop Jupyter Lab server
	docker compose -f docker/docker-compose-jupyter.yml down

jupyter-build: ## Build Jupyter Lab image
	docker compose -f docker/docker-compose-jupyter.yml build --no-cache

##@ Cleanup

clean-logs: ## Remove log files
	rm -rf user_data/logs/*.log

clean-cache: ## Remove __pycache__ directories
	find user_data -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-backtest: ## Remove backtest results
	rm -rf user_data/backtest_results/*

clean-all: clean-logs clean-cache clean-backtest ## Clean logs, cache, and backtest results
