#!/usr/bin/env python3
"""
Index building script that parses research data and creates market indexes.
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

class IndexBuilder:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.research_data = {}
        
    def load_research_data(self) -> Dict[str, Dict]:
        """Load and parse all research markdown files."""
        print(f"Loading research data from {self.data_dir}")
        
        research_files = list(self.data_dir.glob("*.md"))
        print(f"Found {len(research_files)} research files")
        
        for file_path in research_files:
            ticker = file_path.stem
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract JSON scores from the content
                scores = self.extract_scores(content)
                
                if scores:
                    self.research_data[ticker] = {
                        'scores': scores,
                        'file_path': file_path,
                        'content': content
                    }
                    print(f"Loaded scores for {ticker}: {scores}")
                else:
                    print(f"Warning: No valid scores found for {ticker}")
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        print(f"Successfully loaded data for {len(self.research_data)} tickers")
        return self.research_data
    
    def extract_scores(self, content: str) -> Dict[str, float]:
        """Extract JSON scores from markdown content."""
        # Look for JSON blocks in the content
        json_pattern = r'```json\s*(\{[^}]+\})\s*```'
        matches = re.findall(json_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            try:
                scores = json.loads(match)
                # Validate expected fields
                if all(key in scores for key in ['nativeness', 'hype']):
                    return {
                        'nativeness': float(scores['nativeness']),
                        'hype': float(scores['hype']),
                        'confidence': float(scores.get('confidence', 5.0))
                    }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                continue
        
        # Fallback: try to find score patterns in text
        score_patterns = {
            'nativeness': [
                r'(?:nativeness|ai.nativeness)[:\s]+(\d+(?:\.\d+)?)',
                r'"nativeness"[:\s]+(\d+(?:\.\d+)?)',
                r'AI\s+Nativeness[:\s]+(\d+(?:\.\d+)?)'
            ],
            'hype': [
                r'(?:hype|market.hype)[:\s]+(\d+(?:\.\d+)?)',
                r'"hype"[:\s]+(\d+(?:\.\d+)?)',
                r'Market\s+Hype[:\s]+(\d+(?:\.\d+)?)'
            ]
        }
        
        extracted_scores = {}
        for score_type, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        extracted_scores[score_type] = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        if 'nativeness' in extracted_scores and 'hype' in extracted_scores:
            extracted_scores['confidence'] = 3.0  # Lower confidence for extracted scores
            return extracted_scores
        
        return {}
    
    def evaluate_expression(self, expression: str, scores: Dict[str, float]) -> float:
        """Evaluate a scoring expression with the given scores."""
        # Replace variable names with actual values
        expr = expression
        for var, value in scores.items():
            expr = expr.replace(f"${var}", str(value))
        
        # Basic safety check - only allow numbers, operators, and parentheses
        if not re.match(r'^[\d\s+\-*/().]+$', expr):
            raise ValueError(f"Invalid expression: {expression}")
        
        try:
            return eval(expr)
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")
    
    def build_index(self, score_expr: str, top_k: int = 10) -> List[Tuple[str, float, Dict]]:
        """Build index by evaluating score expression and ranking tickers."""
        scored_tickers = []
        
        for ticker, data in self.research_data.items():
            try:
                score = self.evaluate_expression(score_expr, data['scores'])
                scored_tickers.append((ticker, score, data['scores']))
            except Exception as e:
                print(f"Warning: Could not score {ticker}: {e}")
        
        # Sort by score (descending) and take top K
        scored_tickers.sort(key=lambda x: x[1], reverse=True)
        return scored_tickers[:top_k]
    
    def generate_tradingview_expression(self, index_tickers: List[Tuple[str, float, Dict]], 
                                      equal_weight: bool = True) -> str:
        """Generate TradingView Pine Script expression for the index."""
        if not index_tickers:
            return ""
        
        if equal_weight:
            # Equal weight index
            weight = 1.0 / len(index_tickers)
            expressions = []
            for ticker, score, _ in index_tickers:
                expressions.append(f"{weight:.6f} * close(syminfo.ticker == '{ticker}' ? na : request.security('{ticker}', timeframe.period, close))")
            
            pine_script = f"""
// Equal Weight AI-Native Index ({len(index_tickers)} stocks)
index_value = {' + '.join(expressions)}
plot(index_value, title="AI-Native Index", color=color.blue, linewidth=2)
"""
        else:
            # Score-weighted index
            total_score = sum(score for _, score, _ in index_tickers)
            expressions = []
            for ticker, score, _ in index_tickers:
                weight = score / total_score if total_score > 0 else 1.0 / len(index_tickers)
                expressions.append(f"{weight:.6f} * close(syminfo.ticker == '{ticker}' ? na : request.security('{ticker}', timeframe.period, close))")
            
            pine_script = f"""
// Score-Weighted AI-Native Index ({len(index_tickers)} stocks)
index_value = {' + '.join(expressions)}
plot(index_value, title="AI-Native Index", color=color.blue, linewidth=2)
"""
        
        return pine_script.strip()
    
    def generate_simple_ticker_list(self, index_tickers: List[Tuple[str, float, Dict]]) -> str:
        """Generate a simple comma-separated list of tickers for TradingView."""
        return ", ".join([ticker for ticker, _, _ in index_tickers])
    
    def create_index_report(self, index_tickers: List[Tuple[str, float, Dict]], 
                           score_expr: str, strategy_name: str) -> str:
        """Create a comprehensive markdown report for the index."""
        
        report = f"""# {strategy_name.title()} Index Report

**Generated:** {time.ctime()}
**Strategy:** {strategy_name}
**Scoring Expression:** `{score_expr}`
**Index Size:** {len(index_tickers)} stocks

## Index Composition

| Rank | Ticker | Score | AI Nativeness | Market Hype | Confidence |
|------|--------|-------|---------------|-------------|------------|
"""
        
        for i, (ticker, score, scores) in enumerate(index_tickers, 1):
            report += f"| {i} | {ticker} | {score:.3f} | {scores['nativeness']:.1f} | {scores['hype']:.1f} | {scores['confidence']:.1f} |\n"
        
        report += f"""

## Index Statistics

- **Average Score:** {sum(score for _, score, _ in index_tickers) / len(index_tickers):.3f}
- **Average AI Nativeness:** {sum(scores['nativeness'] for _, _, scores in index_tickers) / len(index_tickers):.1f}
- **Average Market Hype:** {sum(scores['hype'] for _, _, scores in index_tickers) / len(index_tickers):.1f}
- **Average Confidence:** {sum(scores['confidence'] for _, _, scores in index_tickers) / len(index_tickers):.1f}

## TradingView Integration

### Simple Ticker List
```
{self.generate_simple_ticker_list(index_tickers)}
```

### Equal Weight Pine Script
```pinescript
{self.generate_tradingview_expression(index_tickers, equal_weight=True)}
```

### Score-Weighted Pine Script  
```pinescript
{self.generate_tradingview_expression(index_tickers, equal_weight=False)}
```

## Methodology

This index was constructed by:

1. **Research Phase:** Deep analysis of each company using Perplexity AI's search capabilities
2. **Scoring:** Each company rated on AI Nativeness (1-10) and Market Hype (1-10)
3. **Index Construction:** Companies ranked using the expression: `{score_expr}`
4. **Selection:** Top {len(index_tickers)} companies selected for the index

### Scoring Framework

- **AI Nativeness (1-10):** How fundamentally AI-driven is the company's business model
- **Market Hype (1-10):** How much of the current valuation is driven by AI hype vs fundamentals
- **Confidence (1-10):** Analyst confidence in the assessment

### Index Expression: `{score_expr}`

This expression was designed to identify companies that are genuinely AI-native while being mindful of valuation bubbles.

## Risk Considerations

- High concentration in technology sector
- Sensitivity to AI market sentiment
- Potential for increased volatility during tech corrections
- Strategy based on current market conditions and may need periodic rebalancing

---

*This index is for informational purposes only and should not be considered investment advice.*
"""
        
        return report

def main():
    parser = argparse.ArgumentParser(description="Build market index from research data")
    parser.add_argument("--data", required=True, help="Directory containing research markdown files")
    parser.add_argument("--score-expr", required=True, help="Scoring expression (e.g., '$nativeness - $hype')")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top stocks to include in index")
    parser.add_argument("--output", help="Output file path (default: data/<data_dir_name>_index.md)")
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = IndexBuilder(args.data)
    
    # Load research data
    research_data = builder.load_research_data()
    
    if not research_data:
        print("Error: No valid research data found")
        return
    
    # Build index
    print(f"\nBuilding index with expression: {args.score_expr}")
    index_tickers = builder.build_index(args.score_expr, args.top_k)
    
    if not index_tickers:
        print("Error: No tickers could be scored")
        return
    
    print(f"Index built with {len(index_tickers)} stocks")
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        data_name = Path(args.data).name
        output_file = Path(args.data).parent / f"{data_name}_index.md"
    
    # Generate report
    strategy_name = Path(args.data).name
    report = builder.create_index_report(index_tickers, args.score_expr, strategy_name)
    
    # Save report
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"Index report saved to: {output_file}")
    
    # Print summary
    print(f"\nTop {len(index_tickers)} stocks in {strategy_name} index:")
    for i, (ticker, score, scores) in enumerate(index_tickers, 1):
        print(f"{i:2d}. {ticker:<6} Score: {score:6.3f} (AI: {scores['nativeness']:.1f}, Hype: {scores['hype']:.1f})")

if __name__ == "__main__":
    main() 