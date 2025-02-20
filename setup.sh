#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BLUE}=== Setting up NLP Chain Development Environment ===${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 is not installed. Please install pip3 first.${NC}"
    exit 1
fi

# Check if Solana is installed
if ! command -v solana &> /dev/null; then
    echo -e "${BLUE}Installing Solana...${NC}"
    sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
    export PATH="/Users/$USER/.local/share/solana/install/active_release/bin:$PATH"
fi

# Check if Anchor is installed
if ! command -v anchor &> /dev/null; then
    echo -e "${BLUE}Installing Anchor...${NC}"
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
    avm install latest
    avm use latest
fi

# Create Python virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Configure Solana for local development
echo -e "${BLUE}Configuring Solana for local development...${NC}"
solana config set --url localhost
solana-keygen new --no-bip39-passphrase -o ~/.config/solana/id.json

# Build and deploy the program
echo -e "${BLUE}Building and deploying the program...${NC}"
anchor build
anchor deploy

echo -e "\n${GREEN}Setup complete! You can now:${NC}"
echo -e "1. Start the Solana validator: ${BOLD}solana-test-validator${NC}"
echo -e "2. Start the Flask app: ${BOLD}python app.py${NC}"
echo -e "3. Run the tests: ${BOLD}./test.sh${NC}" 