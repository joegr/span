#!/bin/bash
set -e

# Create Solana config directory if it doesn't exist
mkdir -p /root/.config/solana

# Generate keypairs if they don't exist
if [ ! -f /root/.config/solana/id.json ]; then
    solana-keygen new --no-bip39-passphrase -o /root/.config/solana/id.json --force
fi

if [ ! -f /root/.config/solana/validator-keypair.json ]; then
    solana-keygen new --no-bip39-passphrase -o /root/.config/solana/validator-keypair.json --force
fi

if [ ! -f /root/.config/solana/vote-account-keypair.json ]; then
    solana-keygen new --no-bip39-passphrase -o /root/.config/solana/vote-account-keypair.json --force
fi

if [ ! -f /root/.config/solana/stake-account-keypair.json ]; then
    solana-keygen new --no-bip39-passphrase -o /root/.config/solana/stake-account-keypair.json --force
fi

# Set Solana config
solana config set --url http://localhost:8899

echo "Solana keypairs and config initialized!" 