#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

# Function to start the development environment
start() {
    echo -e "${BLUE}Starting development environment...${NC}"
    docker-compose up --build
}

# Function to rebuild the container
rebuild() {
    echo -e "${BLUE}Rebuilding container...${NC}"
    docker-compose build --no-cache
}

# Function to stop the development environment
stop() {
    echo -e "${BLUE}Stopping development environment...${NC}"
    docker-compose down
}

# Function to run tests
test() {
    echo -e "${BLUE}Running tests...${NC}"
    docker-compose exec app pytest
}

# Function to show logs
logs() {
    echo -e "${BLUE}Showing logs...${NC}"
    docker-compose logs -f
}

# Function to open a shell in the container
shell() {
    echo -e "${BLUE}Opening shell in container...${NC}"
    docker-compose exec app bash
}

# Check if Docker is installed
check_docker

# Parse command line arguments
case "$1" in
    "start")
        start
        ;;
    "stop")
        stop
        ;;
    "rebuild")
        rebuild
        ;;
    "test")
        test
        ;;
    "logs")
        logs
        ;;
    "shell")
        shell
        ;;
    *)
        echo -e "Usage: $0 {start|stop|rebuild|test|logs|shell}"
        echo -e "\nCommands:"
        echo -e "  ${BOLD}start${NC}   Start the development environment"
        echo -e "  ${BOLD}stop${NC}    Stop the development environment"
        echo -e "  ${BOLD}rebuild${NC} Rebuild the container from scratch"
        echo -e "  ${BOLD}test${NC}    Run tests"
        echo -e "  ${BOLD}logs${NC}    Show container logs"
        echo -e "  ${BOLD}shell${NC}   Open a shell in the container"
        exit 1
        ;;
esac 