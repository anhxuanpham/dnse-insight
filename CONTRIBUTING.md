# Contributing to DNSE Insight

Thank you for your interest in contributing to DNSE Insight! We welcome contributions from the community.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

### Our Standards
- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

## Getting Started

### Prerequisites
- Python 3.9+
- Git
- Basic understanding of trading concepts
- Familiarity with Vietnamese stock market (helpful)

### Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/dnse-insight.git
cd dnse-insight

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/dnse-insight.git
```

## Development Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

3. **Install pre-commit hooks:**
```bash
pre-commit install
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with test credentials
```

## How to Contribute

### Reporting Bugs
- Check if the bug has already been reported
- Use the bug report template
- Include:
  - Python version
  - OS version
  - Steps to reproduce
  - Expected vs actual behavior
  - Logs/screenshots

### Suggesting Features
- Check if the feature has been suggested
- Use the feature request template
- Explain:
  - Use case
  - Expected behavior
  - Why it would be useful

### Code Contributions

#### Areas to Contribute
1. **Core Trading Bot**
   - New trading strategies
   - Technical indicators
   - Order execution improvements

2. **Dashboard (Feature #2)**
   - Frontend components
   - Chart improvements
   - UI/UX enhancements

3. **Market Screener (Feature #4)**
   - New screening filters
   - Performance optimization
   - Alert mechanisms

4. **Machine Learning (Feature #10)**
   - New ML models
   - Feature engineering
   - Model evaluation

5. **Documentation**
   - Code documentation
   - Tutorials
   - Examples

6. **Tests**
   - Unit tests
   - Integration tests
   - Performance tests

## Coding Standards

### Python Style Guide
We follow **PEP 8** with some modifications:

```python
# Good
def calculate_position_size(
    symbol: str,
    entry_price: float,
    stop_loss: float
) -> int:
    """
    Calculate position size based on risk management rules.

    Args:
        symbol: Stock symbol (e.g., "VCB")
        entry_price: Entry price in VND
        stop_loss: Stop loss price in VND

    Returns:
        Position size in shares
    """
    risk_amount = get_risk_amount()
    risk_per_share = abs(entry_price - stop_loss)
    return int(risk_amount / risk_per_share)
```

### Code Formatting
We use **Black** for code formatting:
```bash
black .
```

### Linting
We use **Flake8** for linting:
```bash
flake8 core/ utils/
```

### Type Hints
Use type hints for all functions:
```python
from typing import Dict, List, Optional

def get_positions(account_id: str) -> Dict[str, int]:
    """Get current positions"""
    pass
```

### Docstrings
Use Google-style docstrings:
```python
def place_order(
    symbol: str,
    side: OrderSide,
    quantity: int,
    price: float = 0
) -> Optional[Order]:
    """
    Place a trading order.

    Args:
        symbol: Stock symbol (e.g., "VCB")
        side: Order side (BUY or SELL)
        quantity: Number of shares
        price: Limit price (0 for market order)

    Returns:
        Order object if successful, None otherwise

    Raises:
        OrderExecutionError: If order fails to execute

    Example:
        >>> order = place_order("VCB", OrderSide.BUY, 100, 95.5)
        >>> print(order.order_id)
        "12345"
    """
    pass
```

### Logging
Use loguru for logging:
```python
from loguru import logger

logger.info(f"Placing order: {symbol}")
logger.warning(f"High volatility detected: {volatility}")
logger.error(f"Order execution failed: {error}")
```

### Error Handling
Always handle exceptions appropriately:
```python
try:
    order = place_order(symbol, side, quantity, price)
except OrderExecutionError as e:
    logger.error(f"Failed to place order: {e}")
    notify_error(e)
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils

# Run specific test file
pytest tests/test_signal_engine.py

# Run with verbose output
pytest -v
```

### Writing Tests
Use pytest for all tests:

```python
import pytest
from core.signal_engine import SignalEngine

class TestSignalEngine:
    """Test SignalEngine class"""

    @pytest.fixture
    def engine(self):
        """Create signal engine instance"""
        return SignalEngine()

    def test_calculate_sma(self, engine):
        """Test SMA calculation"""
        # Add test data
        for i in range(20):
            engine.update_price("VCB", 100.0 + i, 1000, 101.0, 99.0)

        # Calculate SMA
        sma = engine.calculate_sma("VCB", 20)

        # Assertions
        assert sma is not None
        assert isinstance(sma, float)
        assert sma > 100.0
```

### Test Coverage
- Aim for > 80% code coverage
- Critical paths must have 100% coverage
- Include edge cases and error scenarios

## Pull Request Process

### Before Submitting
1. **Update from upstream:**
```bash
git fetch upstream
git rebase upstream/main
```

2. **Run tests:**
```bash
pytest
flake8
black --check .
```

3. **Update documentation:**
- Update README if needed
- Add docstrings
- Update CHANGELOG

### PR Guidelines
1. **Branch naming:**
   - Feature: `feature/add-macd-indicator`
   - Bug fix: `fix/order-execution-bug`
   - Docs: `docs/update-readme`

2. **Commit messages:**
```
feat: Add MACD indicator to signal engine

- Implement MACD calculation
- Add MACD to signal generation
- Include tests for MACD

Closes #123
```

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

3. **PR Description:**
Use the template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
```

### Review Process
1. Automated checks must pass
2. At least one maintainer approval required
3. No unresolved comments
4. Up to date with main branch

### After Approval
We'll merge your PR using squash and merge.

## Development Workflow

### Typical Workflow
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Run tests
pytest
black .
flake8

# 4. Commit changes
git add .
git commit -m "feat: Add my feature"

# 5. Push to your fork
git push origin feature/my-feature

# 6. Create Pull Request on GitHub
```

### Keeping Fork Updated
```bash
# Fetch upstream changes
git fetch upstream

# Update main branch
git checkout main
git merge upstream/main

# Rebase feature branch
git checkout feature/my-feature
git rebase main
```

## Development Tips

### Debugging
```python
# Use logger for debugging
from loguru import logger

logger.debug(f"Variable value: {var}")

# Use ipdb for interactive debugging
import ipdb; ipdb.set_trace()
```

### Performance
```python
# Profile code
import cProfile
cProfile.run('my_function()')

# Time execution
import time
start = time.time()
my_function()
logger.info(f"Execution time: {time.time() - start:.2f}s")
```

### Testing with Real Data
```python
# Use fixtures for test data
@pytest.fixture
def sample_price_data():
    return {
        'symbol': 'VCB',
        'price': 100.0,
        'volume': 1000,
        # ...
    }
```

## Documentation

### Code Documentation
- Every module needs a docstring
- Every class needs a docstring
- Every public function needs a docstring
- Complex logic needs inline comments

### README Updates
Update README when:
- Adding new features
- Changing configuration
- Adding dependencies
- Changing installation steps

## Questions?

- **General questions:** Open a discussion
- **Bug reports:** Open an issue
- **Security issues:** Email security@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to DNSE Insight! 🚀
