#!/usr/bin/env python3
"""
Research script for conducting deep analysis on stock tickers using Perplexity AI.
"""

import argparse
import asyncio
import csv
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import aiohttp
import sys

class PerplexityResearcher:
    def __init__(self, api_key: str, batch_size: int = 5):
        self.api_key = api_key
        self.batch_size = batch_size
        self.base_url = "https://api.perplexity.ai"
        self.session = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.batch_size)
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research_ticker(self, ticker: str, strategy_prompt: str) -> Dict[str, Any]:
        """Research a single ticker using the strategy prompt."""
        print(f"Researching {ticker}...")
        
        # Combine strategy prompt with ticker-specific query
        full_prompt = f"{strategy_prompt}\n\n**Company to analyze: {ticker}**\n\nProvide a comprehensive analysis of {ticker} based on the framework above."
        
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a sophisticated financial analyst with access to current market data and company information."
                },
                {
                    "role": "user", 
                    "content": full_prompt
                }
            ],
            "return_related_questions": False,
            "return_images": False,
            "search_recency_filter": "year"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error for {ticker}: {response.status} - {error_text}")
                    return {
                        "ticker": ticker,
                        "error": f"HTTP {response.status}: {error_text}",
                        "timestamp": time.time()
                    }
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                citations = result.get("citations", [])
                search_results = result.get("search_results", [])
                
                return {
                    "ticker": ticker,
                    "content": content,
                    "citations": citations,
                    "search_results": search_results,
                    "timestamp": time.time(),
                    "usage": result.get("usage", {})
                }
                
        except Exception as e:
            print(f"Exception for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def research_batch(self, tickers: List[str], strategy_prompt: str) -> List[Dict[str, Any]]:
        """Research a batch of tickers concurrently."""
        tasks = [
            self.research_ticker(ticker, strategy_prompt) 
            for ticker in tickers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "ticker": tickers[i],
                    "error": str(result),
                    "timestamp": time.time()
                })
            else:
                processed_results.append(result)
        
        return processed_results

def load_universe(universe_file: str) -> List[str]:
    """Load tickers from universe CSV file."""
    tickers = []
    with open(universe_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickers.append(row['ticker'].strip().upper())
    return tickers

def load_strategy(strategy_file: str) -> str:
    """Load strategy prompt from markdown file."""
    with open(strategy_file, 'r') as f:
        return f.read()

def save_research_result(result: Dict[str, Any], output_dir: Path):
    """Save research result as markdown file."""
    ticker = result["ticker"]
    output_file = output_dir / f"{ticker}.md"
    
    # Create markdown content
    content = f"# Research Analysis: {ticker}\n\n"
    content += f"**Generated:** {time.ctime(result['timestamp'])}\n\n"
    
    if "error" in result:
        content += f"**Error:** {result['error']}\n\n"
    else:
        content += f"## Analysis\n\n{result['content']}\n\n"
        
        if result.get('citations'):
            content += "## Citations\n\n"
            for i, citation in enumerate(result['citations'], 1):
                content += f"{i}. {citation}\n"
            content += "\n"
        
        if result.get('search_results'):
            content += "## Search Results\n\n"
            for sr in result['search_results']:
                content += f"- **{sr.get('title', 'N/A')}** ({sr.get('date', 'N/A')})\n"
                content += f"  {sr.get('url', 'N/A')}\n"
                if sr.get('description'):
                    content += f"  {sr['description']}\n"
                content += "\n"
        
        if result.get('usage'):
            content += "## Usage Stats\n\n"
            usage = result['usage']
            content += f"- Prompt tokens: {usage.get('prompt_tokens', 'N/A')}\n"
            content += f"- Completion tokens: {usage.get('completion_tokens', 'N/A')}\n"
            content += f"- Total tokens: {usage.get('total_tokens', 'N/A')}\n"
            if usage.get('num_search_queries'):
                content += f"- Search queries: {usage['num_search_queries']}\n"
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Saved research for {ticker} to {output_file}")

async def main():
    parser = argparse.ArgumentParser(description="Research stock tickers using Perplexity AI")
    parser.add_argument("--universe", required=True, help="Path to universe CSV file")
    parser.add_argument("--strategy", required=True, help="Path to strategy markdown file") 
    parser.add_argument("--batch-size", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--output-dir", help="Output directory (default: data/<strategy_name>)")
    parser.add_argument("--api-key", help="Perplexity API key (or set PERPLEXITY_API_KEY env var)")
    parser.add_argument("--limit", type=int, help="Limit number of tickers to process")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("Error: Please provide API key via --api-key or PERPLEXITY_API_KEY environment variable")
        sys.exit(1)
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        strategy_name = Path(args.strategy).stem
        output_dir = Path("data") / strategy_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load inputs
    tickers = load_universe(args.universe)
    if args.limit:
        tickers = tickers[:args.limit]
    
    strategy_prompt = load_strategy(args.strategy)
    
    print(f"Loaded {len(tickers)} tickers from {args.universe}")
    print(f"Using strategy from {args.strategy}")
    print(f"Output directory: {output_dir}")
    print(f"Batch size: {args.batch_size}")
    
    # Process tickers in batches
    async with PerplexityResearcher(api_key, args.batch_size) as researcher:
        for i in range(0, len(tickers), args.batch_size):
            batch = tickers[i:i + args.batch_size]
            print(f"\nProcessing batch {i//args.batch_size + 1}: {batch}")
            
            results = await researcher.research_batch(batch, strategy_prompt)
            
            # Save results
            for result in results:
                save_research_result(result, output_dir)
            
            # Small delay between batches to be respectful
            if i + args.batch_size < len(tickers):
                print("Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
    
    print(f"\nCompleted research for {len(tickers)} tickers. Results saved to {output_dir}")

if __name__ == "__main__":
    asyncio.run(main()) 