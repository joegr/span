#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Versions - these should match Dockerfile
SOLANA_VERSION="1.18.1"
ANCHOR_VERSION="0.29.0"
RUST_VERSION="1.75.0"

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command failed with exit code $?."' EXIT

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo -e "${RED}This script is intended for local development setup, not Docker environments.${NC}"
    exit 1
fi

# Environment setup
export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
export PATH="$CARGO_HOME/bin:$PATH"

# Function to reload shell
reload_shell() {
    if [ -f "$CARGO_HOME/env" ]; then
        source "$CARGO_HOME/env"
    else
        echo -e "${RED}Warning: Cargo environment file not found${NC}"
    fi
}

echo -e "${BLUE}=== Setting up Local Development Environment ===${NC}\n"

# Check for required tools
for cmd in python3 pip3 git curl; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}$cmd is not installed. Please install it first.${NC}"
        exit 1
    fi
done

# Create Python virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install Rust if needed
if ! command -v rustup &> /dev/null; then
    echo -e "${BLUE}Installing Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
        sh -s -- -y --default-toolchain ${RUST_VERSION} --no-modify-path
    reload_shell
fi

# Install Solana if needed
if ! command -v solana &> /dev/null; then
    echo -e "${BLUE}Installing Solana...${NC}"
    sh -c "$(curl -sSfL https://release.solana.com/v${SOLANA_VERSION}/install)"
fi

# Install Anchor if needed
if ! command -v anchor &> /dev/null; then
    echo -e "${BLUE}Installing Anchor...${NC}"
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
    avm install ${ANCHOR_VERSION}
    avm use ${ANCHOR_VERSION}
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOL
FLASK_APP=app.py
FLASK_ENV=development
PYTHONUNBUFFERED=1
SOLANA_RPC_URL=http://localhost:8899
EOL
fi

echo -e "\n${GREEN}Local development environment setup complete!${NC}"
echo -e "\nTo start developing:"
echo -e "1. ${BOLD}source venv/bin/activate${NC}"
echo -e "2. ${BOLD}source .env${NC}"
echo -e "3. Use ${BOLD}./dev.sh${NC} for Docker operations" 