#!/bin/bash
set -e

# Source environment
. /venv/bin/activate
. "$CARGO_HOME/env"

# Start Solana validator if not already running
if ! pgrep -x "solana-test-val" > /dev/null; then
    solana-test-validator &
    VALIDATOR_PID=$!

    # Wait for validator to start
    echo "Waiting for validator to start..."
    until solana cluster-version 2>/dev/null; do
        echo "."
        sleep 2
    done
    echo "Validator started successfully"
fi

# Initialize Solana if needed
if [ ! -f /root/.config/solana/id.json ]; then
    solana-keygen new --no-bip39-passphrase -o /root/.config/solana/id.json --force
    solana config set --url http://localhost:8899
    solana airdrop 2 $(solana address) || echo "Airdrop failed, continuing anyway..."
fi

# Start Flask app
echo "Starting Flask application..."
exec python app.py 