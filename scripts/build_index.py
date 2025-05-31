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
    def __init__(self, data_dir: str, required_vars: List[str] = None):
        self.data_dir = Path(data_dir)
        self.research_data = {}
        self.required_vars = required_vars or []
        
    def extract_variables_from_expression(self, expression: str) -> List[str]:
        """Extract variable names from a scoring expression."""
        # Find all variables in the format $variable_name
        variables = re.findall(r'\$(\w+)', expression)
        return list(set(variables))  # Remove duplicates
    
    def set_required_variables(self, variables: List[str]):
        """Set the required variables for score extraction."""
        self.required_vars = variables
        
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
                # Validate required fields
                if self.required_vars and all(key in scores for key in self.required_vars):
                    result = {}
                    for var in self.required_vars:
                        result[var] = float(scores[var])
                    return result
                elif not self.required_vars:
                    # If no required vars specified, return all numeric scores
                    result = {}
                    for key, value in scores.items():
                        try:
                            result[key] = float(value)
                        except (ValueError, TypeError):
                            pass
                    if result:
                        return result
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                continue
        
        # Fallback: try to find score patterns in text using required variables
        if not self.required_vars:
            return {}
            
        # Generate dynamic patterns for required variables
        extracted_scores = {}
        for var in self.required_vars:
            patterns = [
                rf'(?:{var}|{var.lower()}|{var.upper()})[:\s]+(\d+(?:\.\d+)?)',
                rf'"{var}"[:\s]+(\d+(?:\.\d+)?)',
                rf'{var.title()}[:\s]+(\d+(?:\.\d+)?)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        extracted_scores[var] = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        if len(extracted_scores) == len(self.required_vars):
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
        # Extract required variables from expression
        required_vars = self.extract_variables_from_expression(score_expr)
        self.set_required_variables(required_vars)
        print(f"Expression requires variables: {required_vars}")
        
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
        
        # Get all unique score keys from the data
        all_score_keys = set()
        for _, _, scores in index_tickers:
            all_score_keys.update(scores.keys())
        score_keys = sorted(list(all_score_keys))
        
        report = f"""# {strategy_name.title()} Index Report

**Generated:** {time.ctime()}
**Strategy:** {strategy_name}
**Scoring Expression:** `{score_expr}`
**Index Size:** {len(index_tickers)} stocks

## Index Composition

| Rank | Ticker | Score |"""
        
        # Add dynamic column headers
        for key in score_keys:
            report += f" {key.title()} |"
        report += "\n"
        
        # Add separator row
        report += "|------|--------|-------|"
        for _ in score_keys:
            report += "-------------|"
        report += "\n"
        
        # Add data rows
        for i, (ticker, score, scores) in enumerate(index_tickers, 1):
            report += f"| {i} | {ticker} | {score:.3f} |"
            for key in score_keys:
                value = scores.get(key, 0.0)
                report += f" {value:.1f} |"
            report += "\n"
        
        # Calculate averages
        avg_score = sum(score for _, score, _ in index_tickers) / len(index_tickers)
        
        report += f"""

## Index Statistics

- **Average Score:** {avg_score:.3f}"""
        
        # Add dynamic average statistics
        for key in score_keys:
            avg_value = sum(scores.get(key, 0.0) for _, _, scores in index_tickers) / len(index_tickers)
            report += f"\n- **Average {key.title()}:** {avg_value:.1f}"
        
        report += f"""

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
2. **Scoring:** Each company rated on multiple dimensions
3. **Index Construction:** Companies ranked using the expression: `{score_expr}`
4. **Selection:** Top {len(index_tickers)} companies selected for the index

### Scoring Framework
"""
        
        # Add dynamic scoring framework description
        for key in score_keys:
            report += f"\n- **{key.title()}:** Scoring dimension for {key}"
        
        report += f"""

### Index Expression: `{score_expr}`

This expression combines multiple scoring dimensions to rank companies effectively.

## Risk Considerations

- Strategy based on current market conditions and may need periodic rebalancing
- Index composition may be concentrated in specific sectors
- Results depend on the quality and recency of research data

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
        # Build dynamic score display
        score_parts = []
        for key, value in scores.items():
            score_parts.append(f"{key.title()}: {value:.1f}")
        score_display = ", ".join(score_parts) if score_parts else "No scores"
        print(f"{i:2d}. {ticker:<6} Score: {score:6.3f} ({score_display})")

if __name__ == "__main__":
    main() 