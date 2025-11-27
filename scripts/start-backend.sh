#!/usr/bin/env bash
#
# Start the Knowledge Base Backend Server
# Usage: ./scripts/start-backend.sh [--dev|--prod] [--port PORT]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="dev"
PORT=8000
HOST="127.0.0.1"

# Script directory and project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Help message
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Start the Knowledge Base backend server.

Options:
    -d, --dev       Development mode with auto-reload (default)
    -p, --prod      Production mode
    --port PORT     Server port (default: 8000)
    --host HOST     Server host (default: 127.0.0.1, use 0.0.0.0 for external)
    -h, --help      Show this help message

Examples:
    $(basename "$0")                    # Start in dev mode on port 8000
    $(basename "$0") --prod --port 9000 # Production mode on port 9000
    $(basename "$0") --host 0.0.0.0     # Allow external connections

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev)
            MODE="dev"
            shift
            ;;
        -p|--prod)
            MODE="prod"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if backend directory exists
if [[ ! -d "$BACKEND_DIR" ]]; then
    log_error "Backend directory not found: $BACKEND_DIR"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    log_warn "Virtual environment not found. Creating..."
    cd "$BACKEND_DIR"
    
    if command -v uv &> /dev/null; then
        uv venv
        log_success "Virtual environment created with uv"
    elif command -v python3 &> /dev/null; then
        python3 -m venv .venv
        log_success "Virtual environment created with python3"
    else
        log_error "Neither uv nor python3 found. Please install Python 3.13+"
        exit 1
    fi
fi

# Activate virtual environment
log_info "Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    log_warn "Dependencies not installed. Installing..."
    cd "$BACKEND_DIR"
    
    if command -v uv &> /dev/null; then
        uv sync
    else
        pip install -e .
    fi
    log_success "Dependencies installed"
fi

# Check if port is available
if lsof -Pi :"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warn "Port $PORT is already in use"
    
    # Find the process using the port
    PID=$(lsof -Pi :"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1)
    PROCESS_NAME=$(ps -p "$PID" -o comm= 2>/dev/null || echo "unknown")
    
    log_info "Process using port $PORT: $PROCESS_NAME (PID: $PID)"
    
    read -rp "Kill existing process and continue? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        kill "$PID" 2>/dev/null || true
        sleep 1
        log_success "Killed process $PID"
    else
        log_error "Cannot start server - port $PORT is in use"
        exit 1
    fi
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Build uvicorn command
UVICORN_CMD="uvicorn app.main:app --host $HOST --port $PORT"

if [[ "$MODE" == "dev" ]]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
    log_info "Starting in DEVELOPMENT mode (auto-reload enabled)"
else
    log_info "Starting in PRODUCTION mode"
fi

# Display startup info
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}          Knowledge Base Backend Server                       ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Mode:        ${BLUE}$MODE${NC}                                            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Server:      ${BLUE}http://$HOST:$PORT${NC}                        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Swagger UI:  ${BLUE}http://$HOST:$PORT/docs${NC}                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ReDoc:       ${BLUE}http://$HOST:$PORT/redoc${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
log_info "Press Ctrl+C to stop the server"
echo ""

# Trap for cleanup on exit
cleanup() {
    echo ""
    log_info "Shutting down server..."
    deactivate 2>/dev/null || true
    log_success "Server stopped"
}
trap cleanup EXIT

# Start the server
exec $UVICORN_CMD
