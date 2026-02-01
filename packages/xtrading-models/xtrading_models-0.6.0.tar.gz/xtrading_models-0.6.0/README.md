# xtrading-models

Shared trading models for the XTrading ecosystem.

## Installation

```bash
pip install xtrading-models
```

## Usage

```python
from datetime import datetime
from decimal import Decimal
from xtrading_models import MarketOrder, LimitOrder, BarData

# Create a market order
order = MarketOrder(action='BUY', totalQuantity=100)

# Create bar data
bar = BarData(
    date=datetime.now(),
    open=Decimal('100.00'),
    high=Decimal('105.00'),
    low=Decimal('99.00'),
    close=Decimal('104.00'),
    volume=1000000
)
```

## Models

- **Order classes**: `Order`, `LimitOrder`, `MarketOrder`, `StopOrder`, `StopLimitOrder`, `TrailingStopMarket`, `TrailingStopLimit`
- **Bar data**: `BarData` - OHLCV candlestick representation
- **Execution**: `Execution`, `CommissionReport`, `Fill`
- **Results**: `ExecutionResult`
- **Sentinels**: `UNSET_DOUBLE`, `UNSET_INTEGER`

## License

MIT
