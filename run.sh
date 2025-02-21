#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}.env file not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Check if keypair exists
KEYPAIR_PATH=$(grep SOLANA_KEYPAIR_PATH .env | cut -d '=' -f2)
if [ ! -f "$KEYPAIR_PATH" ]; then
    echo -e "${RED}Solana keypair not found at $KEYPAIR_PATH. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Source environment variables
set -a
source .env
set +a

# Run the Flask app
echo -e "${BLUE}Starting Flask application...${NC}"
python app.py 