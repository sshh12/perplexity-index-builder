# Perplexity Index Builder

A sophisticated system for creating custom market indexes using Perplexity AI's deep research capabilities. This tool allows you to define investment strategies, research companies at scale, and build data-driven market indexes.

## 🚀 Quick Start

```bash
# 1. Set your Perplexity API key
export PERPLEXITY_API_KEY="your_api_key_here"

# 2. Run research on a small sample (5 companies)
python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/ai-native.md --batch-size 3 --limit 5

# 3. Build the index
python scripts/build_index.py --data data/ai-native --score-expr '$nativeness - $hype' --top-k 3
```

## 📁 Project Structure

```
perplexity-index-builder/
├── universes/           # Stock universe definitions
│   └── nasdaq100.csv   # NASDAQ 100 tickers
├── strategies/          # Research strategy prompts  
│   └── ai-native.md    # AI-native companies strategy
├── scripts/            # Main processing scripts
│   ├── research.py     # Conduct research using Perplexity API
│   └── build_index.py  # Parse research and build indexes
├── data/               # Generated research data and indexes
└── requirements.txt    # Python dependencies
```

## 🔬 How It Works

### 1. Define Your Universe
Create CSV files with stock tickers you want to analyze:

```csv
ticker
AAPL
MSFT
GOOGL
...
```

### 2. Create Research Strategies
Write markdown prompts that define your research framework. Each strategy should:
- Define analysis criteria
- Specify scoring methodology  
- Request JSON output with numerical scores

Example scoring format:
```json
{
  "nativeness": 8,
  "hype": 6,
  "confidence": 7
}
```

### 3. Run Deep Research
The research script uses async processing to efficiently query Perplexity AI:

```bash
python scripts/research.py \
  --universe universes/nasdaq100.csv \
  --strategy strategies/ai-native.md \
  --batch-size 5 \
  --limit 10
```

**Parameters:**
- `--universe`: CSV file with tickers to research
- `--strategy`: Markdown file with research prompt
- `--batch-size`: Number of concurrent API calls (default: 5)
- `--limit`: Limit number of tickers (useful for testing)
- `--api-key`: Perplexity API key (or set `PERPLEXITY_API_KEY` env var)

### 4. Build Custom Indexes
Parse research results and create ranked indexes:

```bash
python scripts/build_index.py \
  --data data/ai-native \
  --score-expr '$nativeness - $hype' \
  --top-k 10
```

**Parameters:**
- `--data`: Directory containing research markdown files
- `--score-expr`: Mathematical expression for ranking (use `$variable` syntax)
- `--top-k`: Number of top stocks in final index
- `--output`: Output file path (optional)

## 📊 Scoring Expressions

You can create sophisticated ranking formulas using any variables from your research JSON:

```bash
# Value play: High AI nativeness, low hype
--score-expr '$nativeness - $hype'

# Confidence-weighted nativeness  
--score-expr '$nativeness * $confidence / 10'

# Complex multi-factor model
--score-expr '($nativeness * 2 + $growth - $hype) * $confidence / 10'
```

## 🔧 Example Workflows

### AI-Native Index
```bash
# Research AI-native companies
python scripts/research.py \
  --universe universes/nasdaq100.csv \
  --strategy strategies/ai-native.md

# Build index favoring high AI nativeness, penalizing hype
python scripts/build_index.py \
  --data data/ai-native \
  --score-expr '$nativeness - $hype' \
  --top-k 10
```

### Custom Strategy
1. Create `strategies/my-strategy.md` with your research framework
2. Define scoring criteria and JSON output format
3. Run research: `python scripts/research.py --strategy strategies/my-strategy.md --universe universes/nasdaq100.csv`
4. Build index: `python scripts/build_index.py --data data/my-strategy --score-expr '$my_score'`

## 📈 TradingView Integration

The system generates ready-to-use TradingView code:

### Simple Ticker List
```
NVDA, GOOGL, MSFT, META, AMZN
```

### Pine Script Index
```pinescript
// Equal Weight AI-Native Index (10 stocks)
index_value = 0.100000 * close(syminfo.ticker == 'NVDA' ? na : request.security('NVDA', timeframe.period, close)) + 
              0.100000 * close(syminfo.ticker == 'GOOGL' ? na : request.security('GOOGL', timeframe.period, close))
plot(index_value, title="AI-Native Index", color=color.blue, linewidth=2)
```

## 🛠 Advanced Usage

### Rate Limiting & Batching
- Use `--batch-size` to control API concurrency
- Built-in delays between batches for rate limiting
- Error handling and retry logic

### Custom Universes
Create specialized stock universes:
- `universes/faang.csv` - Tech giants
- `universes/biotech.csv` - Biotech companies  
- `universes/crypto-stocks.csv` - Crypto-related stocks

### Multi-Strategy Analysis
Run the same universe through different strategies:
```bash
python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/ai-native.md
python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/esg-focused.md
python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/growth-value.md
```

## 🔑 API Setup

1. Get a Perplexity API key from [https://docs.perplexity.ai/](https://docs.perplexity.ai/)
2. Set environment variable:
   ```bash
   export PERPLEXITY_API_KEY="your_key_here"
   ```
3. Or pass directly: `--api-key your_key_here`

## 📋 Requirements

- Python 3.8+
- Perplexity API key
- Dependencies: `pip install -r requirements.txt`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-strategy`
3. Add your strategy in `strategies/`
4. Test with small universe: `--limit 5`
5. Submit pull request

## ⚠️ Disclaimers

- This tool is for research and educational purposes only
- Generated indexes are not investment advice
- Always conduct additional due diligence
- Past performance does not guarantee future results
- Consider consulting with financial professionals

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy Index Building! 🚀📊**