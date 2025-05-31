python scripts/build_index.py --data data/ai-native --score-expr '$ai_nativeness + $ai_product_value - $pre_existing_hype' --top-k 2 --start-date 2025-05-01
python scripts/research.py --universe universes/nasdaq100.csv --strategy strategies/ai-native.md


python scripts/build_index.py --data data/ai-native --score-expr '(($ai_nativeness-7) + ($ai_product_value-5)) / $pre_existing_hype' --start-date 2025-01-01 --top-k 10