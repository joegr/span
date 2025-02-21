#!/bin/bash
set -e  # Exit on error

# Source environment
. /venv/bin/activate
. "$CARGO_HOME/env"

# Ensure Solana directories exist
mkdir -p /root/.config/solana

# Start Solana validator and wait for it
solana-test-validator &
VALIDATOR_PID=$!

# Wait for validator to start
echo "Waiting for validator to start..."
until solana cluster-version 2>/dev/null; do
    echo "."
    sleep 2
done
echo "Validator started successfully"

# Initialize Solana and deploy program
echo "Configuring Solana..."
solana config set --url http://localhost:8899
solana airdrop 2 $(solana address) || echo "Airdrop failed, continuing anyway..."

echo "Building and deploying Anchor program..."
anchor build
anchor deploy || echo "Deploy failed, continuing anyway..."

# Start Flask app (when it exits, kill validator)
echo "Starting Flask application..."
trap "kill $VALIDATOR_PID" EXIT
python app.py 