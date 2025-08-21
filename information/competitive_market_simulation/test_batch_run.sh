#!/bin/bash
# Test script for batch runner

echo "Testing batch simulation runner..."
echo "================================="

# Test 1: Small sequential batch
echo -e "\nTest 1: Running 3 simulations sequentially"
python batch_run.py --num-sims 3 --log-level INFO

# Test 2: Small parallel batch (uncomment to test)
# echo -e "\nTest 2: Running 5 simulations in parallel"
# python batch_run.py --num-sims 5 --parallel --max-workers 2

echo -e "\nBatch test complete!"
echo "Check the logs/ directory for batch results"
echo "Open http://localhost:8080/batch in the dashboard to view aggregated results"