#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Base URL
BASE_URL="http://localhost:5000"

# Function to print section headers
print_header() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${NC}\n"
}

# Function to check if Solana is running
check_solana() {
    print_header "Checking Solana validator"
    if solana cluster-version &>/dev/null; then
        echo -e "${GREEN}Solana validator is running${NC}"
        solana cluster-version
    else
        echo -e "${RED}Solana validator is not running. Please start solana-test-validator first.${NC}"
        exit 1
    fi
}

# Function to check if the program is deployed
check_program() {
    print_header "Checking program deployment"
    PROGRAM_ID="Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"
    if solana program show $PROGRAM_ID &>/dev/null; then
        echo -e "${GREEN}Program is deployed${NC}"
        solana program show $PROGRAM_ID
    else
        echo -e "${RED}Program is not deployed. Please deploy using 'anchor deploy' first.${NC}"
        exit 1
    fi
}

# Function to check if the server is running
check_server() {
    print_header "Checking if server is running"
    if curl -s "$BASE_URL/health" > /dev/null; then
        echo -e "${GREEN}Server is running${NC}"
        # Show chain state info
        curl -s "$BASE_URL/health" | python3 -m json.tool
    else
        echo -e "${RED}Server is not running. Please start the Flask application first.${NC}"
        exit 1
    fi
}

# Function to make API calls and handle responses
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "\n${BOLD}Testing: $description${NC}"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -X GET "$BASE_URL$endpoint")
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Success:${NC}"
        echo "$response" | python3 -m json.tool
        return 0
    else
        echo -e "${RED}Failed:${NC} $response"
        return 1
    fi
}

# Function to validate Solana account
validate_account() {
    local address=$1
    local account_type=$2
    
    echo -e "\n${BOLD}Validating Solana account: $address${NC}"
    
    # Get account info
    account_info=$(solana account $address 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Account exists${NC}"
        echo "$account_info"
        return 0
    else
        echo -e "${RED}✗ Invalid account${NC}"
        return 1
    fi
}

# Function to test vector endpoint
test_vector_endpoint() {
    local block_address=$1
    print_header "Testing Vector Representation for Block $block_address"
    
    response=$(curl -s -X GET "$BASE_URL/blocks/$block_address/vector")
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Vector retrieved successfully:${NC}"
        echo "$response" | python3 -m json.tool
        
        # Validate vector data
        if echo "$response" | python3 -c '
import sys, json
data = json.load(sys.stdin)
vector = data.get("vector", [])
if len(vector) > 0 and any(isinstance(x, float) and x != 0 for x in vector):
    exit(0)
exit(1)
'; then
            echo -e "${GREEN}✓ Valid non-zero vector present${NC}"
            echo -e "${GREEN}✓ Vector size: $(echo "$response" | python3 -c 'import sys, json; print(len(json.load(sys.stdin)["vector"]))')${NC}"
        else
            echo -e "${RED}✗ Invalid or zero vector${NC}"
            return 1
        fi
    else
        echo -e "${RED}Failed to retrieve vector${NC}"
        return 1
    fi
}

# Function to test block hash chain
test_block_hash() {
    local block_address=$1
    print_header "Testing Block Hash Chain for $block_address"
    
    response=$(curl -s -X GET "$BASE_URL/blocks/$block_address")
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Block data retrieved successfully:${NC}"
        echo "$response" | python3 -m json.tool
        
        # Validate hash chain properties
        if echo "$response" | python3 -c '
import sys, json, base64
data = json.load(sys.stdin)

def is_valid_hash(h):
    try:
        decoded = base64.b64decode(h)
        return len(decoded) == 32
    except:
        return False

if (is_valid_hash(data.get("data_hash", "")) and 
    is_valid_hash(data.get("previous_hash", "")) and
    isinstance(data.get("index"), int) and
    isinstance(data.get("timestamp"), int)):
    exit(0)
exit(1)
'; then
            echo -e "${GREEN}✓ Valid block hash chain${NC}"
            return 0
        else
            echo -e "${RED}✗ Invalid block data${NC}"
            return 1
        fi
    else
        echo -e "${RED}Failed to retrieve block data${NC}"
        return 1
    fi
}

# Main test sequence
main() {
    # Check prerequisites
    check_solana
    check_program
    check_server

    # Test health endpoint
    print_header "Testing Health Check"
    call_api "GET" "/health" "" "Health check endpoint"
    chain_state=$(echo "$response" | python3 -c 'import sys, json; print(json.load(sys.stdin)["chain_state"])')
    
    # Validate chain state account
    validate_account "$chain_state" "ChainState"

    # Add sample data
    print_header "Adding Sample Data"
    response=$(call_api "POST" "/test/sample" "{}" "Adding sample blockchain-related texts")
    
    # Extract block addresses
    block_addresses=$(echo "$response" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for result in data.get("results", []):
    print(result.get("block_address", ""))
')

    # Test each block
    for block_address in $block_addresses; do
        # Validate block account
        validate_account "$block_address" "Block"
        
        # Test vector representation
        test_vector_endpoint "$block_address"
        
        # Test block hash chain
        test_block_hash "$block_address"
    done

    # Test adding a custom block
    print_header "Testing Block Addition"
    response=$(call_api "POST" "/blocks" '{
        "text": "Testing the Solana NLP chain with a custom text block. This should be processed and stored on-chain.",
        "span_length": 100,
        "overlap": 50,
        "metadata": {
            "source": "test_script",
            "type": "test"
        }
    }' "Adding custom text block")
    
    new_block_address=$(echo "$response" | python3 -c 'import sys, json; print(json.load(sys.stdin)["block_address"])')
    validate_account "$new_block_address" "Block"

    # Test similarity search
    print_header "Testing Similarity Search"
    call_api "GET" "/search?query=blockchain%20technology&threshold=0.7" "" "Searching for similar text spans"

    echo -e "\n${GREEN}${BOLD}All tests completed!${NC}\n"
}

# Run the test sequence
main

# Optional: Add error handling for common issues
if [ $? -ne 0 ]; then
    echo -e "\n${RED}Tests failed. Please check the error messages above.${NC}"
    exit 1
fi 