# Perplexity Index Builder

> Build custom market indexes using AI-powered research. Leverage Perplexity's deep research capabilities to score companies across any criteria, then generate tradeable indexes with TradingView integration.

<img width="800" alt="AI native index, base at May 2024" src="https://github.com/user-attachments/assets/5336127f-4793-4a8a-a55c-94eebe354bef" >

## Usage

1. **Create a strategy** using the right format with JSON scores - define your scoring criteria and rubric in markdown (see [`strategies/ai-native.md`](https://github.com/sshh12/perplexity-index-builder/blob/main/strategies/ai-native.md))

2. **Run research script** to analyze companies and inspect outputs:
   ```bash
   python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/ai-native.md
   ```

3. **Run index script** and play with different expressions to build your index:
   ```bash
   python scripts/build_index.py --data data/ai-native --score-expr '(($ai_nativeness-7) + ($ai_product_value-5)) / $pre_existing_hype' --start-date 2025-01-01 --top-k 10
   ```

4. **Open TradingView** to visualize your index:
   - Go to https://www.tradingview.com/
   - Open any chart 
   - Click the "Pine Editor" tab at the bottom
   - Paste in the generated Pine Script code
   - Click "Add to Chart" to see your custom index overlaid

## Examples

<details>
<summary>AI-Native Companies Index (Click to expand)</summary>

# Ai-Native Index Report

**Generated:** Sat May 31 23:00:12 2025
**Strategy:** ai-native
**Scoring Expression:** `(($ai_nativeness-7) + ($ai_product_value-5)) / $pre_existing_hype`
**Index Start Date:** 2025-05-30 (normalized to 100)
**Index Size:** 10 stocks

## Dataset Statistics

*Statistics calculated on the full dataset before applying top-k filter*

| Metric | Count | Min | Max | Mean | P25 | P50 (Median) | P75 |
|--------|--------|--------|--------|--------|--------|--------|--------|
| Ai_Nativeness | 95 | 5.0 | 10.0 | 7.1 | 6.0 | 7.0 | 8.0 |
| Ai_Product_Value | 95 | 2.0 | 10.0 | 7.0 | 6.0 | 7.0 | 8.0 |
| Pre_Existing_Hype | 95 | 2.0 | 10.0 | 5.9 | 5.0 | 6.0 | 7.0 |
| **Final Score** | 95 | -1.667 | 0.833 | 0.272 | 0.183 | 0.400 | 0.500 |


## Index Composition

| Rank | Ticker | Score | Ai_Nativeness | Ai_Product_Value | Pre_Existing_Hype |
|------|--------|-------|-------------|-------------|-------------|
| 1 | IDXX | 0.833 | 8.0 | 9.0 | 6.0 |
| 2 | NVDA | 0.800 | 10.0 | 10.0 | 10.0 |
| 3 | APP | 0.750 | 9.0 | 9.0 | 8.0 |
| 4 | PLTR | 0.750 | 9.0 | 9.0 | 8.0 |
| 5 | CRWD | 0.714 | 8.0 | 9.0 | 7.0 |
| 6 | AMZN | 0.714 | 8.0 | 9.0 | 7.0 |
| 7 | MELI | 0.714 | 9.0 | 8.0 | 7.0 |
| 8 | ARM | 0.714 | 8.0 | 9.0 | 7.0 |
| 9 | ADBE | 0.714 | 8.0 | 9.0 | 7.0 |
| 10 | META | 0.714 | 9.0 | 8.0 | 7.0 |


## Index Statistics

- **Average Score:** 0.742
- **Average Ai_Nativeness:** 8.6
- **Average Ai_Product_Value:** 8.9
- **Average Pre_Existing_Hype:** 7.4

**Index Normalization:** This index is normalized to 100 on 2025-05-30. All values represent the relative performance since that date.

## TradingView Integration

### Simple Ticker List
```
IDXX, NVDA, APP, PLTR, CRWD, AMZN, MELI, ARM, ADBE, META
```

### Equal Weight Pine Script
```pinescript
//@version=5
indicator("Equal Weight Ai-Native Index", shorttitle="AINATI-IDX", overlay=false)

// Index start date: 2025-05-30
start_date = timestamp("2025-05-30")

// Weights
w0 = 0.100000
w1 = 0.100000
w2 = 0.100000
w3 = 0.100000
w4 = 0.100000
w5 = 0.100000
w6 = 0.100000
w7 = 0.100000
w8 = 0.100000
w9 = 0.100000

// Stock prices
p0 = request.security('IDXX', timeframe.period, close)
p1 = request.security('NVDA', timeframe.period, close)
p2 = request.security('APP', timeframe.period, close)
p3 = request.security('PLTR', timeframe.period, close)
p4 = request.security('CRWD', timeframe.period, close)
p5 = request.security('AMZN', timeframe.period, close)
p6 = request.security('MELI', timeframe.period, close)
p7 = request.security('ARM', timeframe.period, close)
p8 = request.security('ADBE', timeframe.period, close)
p9 = request.security('META', timeframe.period, close)

// Baseline values (prices on start date)
var float base0 = na
var float base1 = na
var float base2 = na
var float base3 = na
var float base4 = na
var float base5 = na
var float base6 = na
var float base7 = na
var float base8 = na
var float base9 = na

// Set baseline values on or after start date
if barstate.isconfirmed
    if time >= start_date and na(base0)
        base0 := p0
    if time >= start_date and na(base1)
        base1 := p1
    if time >= start_date and na(base2)
        base2 := p2
    if time >= start_date and na(base3)
        base3 := p3
    if time >= start_date and na(base4)
        base4 := p4
    if time >= start_date and na(base5)
        base5 := p5
    if time >= start_date and na(base6)
        base6 := p6
    if time >= start_date and na(base7)
        base7 := p7
    if time >= start_date and na(base8)
        base8 := p8
    if time >= start_date and na(base9)
        base9 := p9

// Calculate normalized index value
// Each stock normalized to its start date price, then weighted
valid_bases = not na(base0) and not na(base1) and not na(base2) and not na(base3) and not na(base4) and not na(base5) and not na(base6) and not na(base7) and not na(base8) and not na(base9)
index_value = valid_bases ? 100 * (w0 * (p0 / base0) + w1 * (p1 / base1) + w2 * (p2 / base2) + w3 * (p3 / base3) + w4 * (p4 / base4) + w5 * (p5 / base5) + w6 * (p6 / base6) + w7 * (p7 / base7) + w8 * (p8 / base8) + w9 * (p9 / base9)) : na

plot(index_value, title="Equal Weight Ai-Native Index", color=color.blue, linewidth=2)
hline(100, "Base Level", color=color.gray, linestyle=hline.style_dashed)

// Display current index level and composition
if barstate.islast and not na(index_value)
    label.new(bar_index, index_value, "Index: " + str.tostring(index_value, "#.##"), 
              style=label.style_label_left, color=color.blue, textcolor=color.white)
```

### Score-Weighted Pine Script  
```pinescript
//@version=5
indicator("Score-Weighted Ai-Native Index", shorttitle="AINATI-IDX", overlay=false)

// Index start date: 2025-05-30
start_date = timestamp("2025-05-30")

// Weights
w0 = 0.112323
w1 = 0.107831
w2 = 0.101091
w3 = 0.101091
w4 = 0.096277
w5 = 0.096277
w6 = 0.096277
w7 = 0.096277
w8 = 0.096277
w9 = 0.096277

// Stock prices
p0 = request.security('IDXX', timeframe.period, close)
p1 = request.security('NVDA', timeframe.period, close)
p2 = request.security('APP', timeframe.period, close)
p3 = request.security('PLTR', timeframe.period, close)
p4 = request.security('CRWD', timeframe.period, close)
p5 = request.security('AMZN', timeframe.period, close)
p6 = request.security('MELI', timeframe.period, close)
p7 = request.security('ARM', timeframe.period, close)
p8 = request.security('ADBE', timeframe.period, close)
p9 = request.security('META', timeframe.period, close)

// Baseline values (prices on start date)
var float base0 = na
var float base1 = na
var float base2 = na
var float base3 = na
var float base4 = na
var float base5 = na
var float base6 = na
var float base7 = na
var float base8 = na
var float base9 = na

// Set baseline values on or after start date
if barstate.isconfirmed
    if time >= start_date and na(base0)
        base0 := p0
    if time >= start_date and na(base1)
        base1 := p1
    if time >= start_date and na(base2)
        base2 := p2
    if time >= start_date and na(base3)
        base3 := p3
    if time >= start_date and na(base4)
        base4 := p4
    if time >= start_date and na(base5)
        base5 := p5
    if time >= start_date and na(base6)
        base6 := p6
    if time >= start_date and na(base7)
        base7 := p7
    if time >= start_date and na(base8)
        base8 := p8
    if time >= start_date and na(base9)
        base9 := p9

// Calculate normalized index value
// Each stock normalized to its start date price, then weighted
valid_bases = not na(base0) and not na(base1) and not na(base2) and not na(base3) and not na(base4) and not na(base5) and not na(base6) and not na(base7) and not na(base8) and not na(base9)
index_value = valid_bases ? 100 * (w0 * (p0 / base0) + w1 * (p1 / base1) + w2 * (p2 / base2) + w3 * (p3 / base3) + w4 * (p4 / base4) + w5 * (p5 / base5) + w6 * (p6 / base6) + w7 * (p7 / base7) + w8 * (p8 / base8) + w9 * (p9 / base9)) : na

plot(index_value, title="Score-Weighted Ai-Native Index", color=color.blue, linewidth=2)
hline(100, "Base Level", color=color.gray, linestyle=hline.style_dashed)

// Display current index level and composition
if barstate.islast and not na(index_value)
    label.new(bar_index, index_value, "Index: " + str.tostring(index_value, "#.##"), 
              style=label.style_label_left, color=color.blue, textcolor=color.white)
```

## Methodology

This index was constructed by:

1. **Research Phase:** Deep analysis of each company using Perplexity AI's search capabilities
2. **Scoring:** Each company rated on multiple dimensions
3. **Index Construction:** Companies ranked using the expression: `(($ai_nativeness-7) + ($ai_product_value-5)) / $pre_existing_hype`
4. **Selection:** Top 10 companies selected for the index
5. **Normalization:** Index normalized to 100 on 2025-05-30

### Scoring Framework

- **Ai_Nativeness:** Scoring dimension for ai_nativeness
- **Ai_Product_Value:** Scoring dimension for ai_product_value
- **Pre_Existing_Hype:** Scoring dimension for pre_existing_hype

### Index Expression: `(($ai_nativeness-7) + ($ai_product_value-5)) / $pre_existing_hype`

This expression combines multiple scoring dimensions to rank companies effectively.

## Risk Considerations

- Strategy based on current market conditions and may need periodic rebalancing
- Index composition may be concentrated in specific sectors
- Results depend on the quality and recency of research data
- Index performance is relative to 2025-05-30 baseline

---

*This index is for informational purposes only and should not be considered investment advice.*

</details>

## Limitations

- LLMs can hallucinate - research outputs should be validated
- Internet sources may not be completely trustworthy - cross-reference important findings
- Market conditions change rapidly - indexes need periodic rebalancing
- Strategy effectiveness depends on scoring framework quality

---

*This tool is for informational and research purposes only and should not be considered investment advice. Always conduct your own research before making investment decisions.*