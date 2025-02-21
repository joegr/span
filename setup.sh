#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Versions
SOLANA_VERSION="1.18.1"
ANCHOR_VERSION="0.29.0"
RUST_VERSION="1.75.0"

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command failed with exit code $?."' EXIT

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

# Function to verify Rust installation
verify_rust() {
    echo -e "${BLUE}Verifying Rust toolchain...${NC}"
    if ! rustup --version; then
        echo -e "${RED}Rustup not found${NC}"
        return 1
    fi
    if ! cargo --version; then
        echo -e "${RED}Cargo not found${NC}"
        return 1
    fi
    if ! rustc --version; then
        echo -e "${RED}Rust compiler not found${NC}"
        return 1
    fi
    return 0
}

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

# Install or update Rust toolchain
echo -e "${BLUE}Setting up Rust toolchain...${NC}"
if ! command -v rustup &> /dev/null; then
    echo -e "${BLUE}Installing Rust via rustup...${NC}"
    # Download and verify rustup-init
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup-init
    chmod +x rustup-init
    # Install with specific configuration
    ./rustup-init -y --default-toolchain ${RUST_VERSION} --no-modify-path
    rm rustup-init
    reload_shell
else
    echo -e "${BLUE}Updating existing Rust installation...${NC}"
    rustup self update
    rustup update stable
    rustup default ${RUST_VERSION}
fi

# Verify and configure Rust installation
if verify_rust; then
    echo -e "${GREEN}Rust toolchain verified successfully${NC}"
    
    # Configure Rust components and targets
    echo -e "${BLUE}Configuring Rust components...${NC}"
    rustup component add rustfmt clippy
    rustup target add x86_64-unknown-linux-gnu
    
    # Configure Cargo
    echo -e "${BLUE}Configuring Cargo...${NC}"
    mkdir -p "$CARGO_HOME"
    cat > "$CARGO_HOME/config" << EOL
[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "target-cpu=native"]

[build]
jobs = 4

[net]
git-fetch-with-cli = true

[cargo-new]
vcs = "git"
EOL
else
    echo -e "${RED}Rust toolchain verification failed${NC}"
    exit 1
fi

# Check/Install Solana
if ! command -v solana &> /dev/null; then
    echo -e "${BLUE}Installing Solana...${NC}"
    mkdir -p ~/.local/share/solana/install
    curl -sSfL https://github.com/solana-labs/solana/releases/download/v${SOLANA_VERSION}/solana-release-$(uname -m)-$(uname -s | tr '[:upper:]' '[:lower:]').tar.bz2 | \
        tar -xj -C ~/.local/share/solana/install/active_release --strip-components=1
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.zshrc
fi

# Check/Install Anchor
if ! command -v anchor &> /dev/null; then
    echo -e "${BLUE}Installing Anchor...${NC}"
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
    avm install ${ANCHOR_VERSION}
    avm use ${ANCHOR_VERSION}
fi

# Create Python virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install development tools
echo -e "${BLUE}Installing development tools...${NC}"
pip install black flake8 pytest

# Install ML dependencies
echo -e "${BLUE}Installing ML dependencies...${NC}"
pip install --upgrade spacy transformers torch
python -m spacy download en_core_web_trf

# Configure Solana for local development
echo -e "${BLUE}Configuring Solana for local development...${NC}"
solana config set --url localhost

# Create Solana keypair directory if it doesn't exist
KEYPAIR_DIR="$HOME/.config/solana"
mkdir -p "$KEYPAIR_DIR"

# Generate new keypair if it doesn't exist
KEYPAIR_PATH="$KEYPAIR_DIR/id.json"
if [ ! -f "$KEYPAIR_PATH" ]; then
    echo -e "${BLUE}Generating new Solana keypair...${NC}"
    solana-keygen new --no-bip39-passphrase -o "$KEYPAIR_PATH"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOL
SOLANA_KEYPAIR_PATH=$KEYPAIR_PATH
SOLANA_RPC_URL=http://localhost:8899
FLASK_APP=app.py
FLASK_ENV=development
PYTHONUNBUFFERED=1
EOL
fi

# Source the environment variables
set -a
source .env
set +a

# Build and deploy the program
echo -e "${BLUE}Building and deploying the program...${NC}"
anchor build
anchor deploy

# Airdrop SOL to the keypair for testing
echo -e "${BLUE}Airdropping SOL for testing...${NC}"
solana airdrop 2 $(solana address)

# Verify installations
echo -e "${BLUE}Verifying installations...${NC}"
python3 --version
pip --version
rustc --version
cargo --version
solana --version
anchor --version
pip list | grep -E "spacy|transformers|torch|flask|numpy|solana|anchorpy"
python -c "import spacy; nlp = spacy.load('en_core_web_trf'); print('spaCy TRF model loaded successfully')"
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); print('Sentence transformers loaded successfully')"

echo -e "\n${GREEN}Setup complete! To start development:${NC}"
echo -e "1. Open a new terminal and run: ${BOLD}solana-test-validator${NC}"
echo -e "2. Open another terminal and run:${NC}"
echo -e "   ${BOLD}source venv/bin/activate${NC}"
echo -e "   ${BOLD}source .env${NC}"
echo -e "   ${BOLD}python app.py${NC}"
echo -e "3. In another terminal, run:${NC}"
echo -e "   ${BOLD}source venv/bin/activate${NC}"
echo -e "   ${BOLD}source .env${NC}"
echo -e "   ${BOLD}./test.sh${NC}" 