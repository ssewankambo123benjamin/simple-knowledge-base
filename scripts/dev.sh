#!/usr/bin/env bash
#
# Start both Frontend and Backend for development
# Usage: ./scripts/dev.sh
#
# Press Ctrl+C to stop both services
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Logging with prefixes
log_backend() { echo -e "${BLUE}[backend]${NC} $1"; }
log_frontend() { echo -e "${CYAN}[frontend]${NC} $1"; }
log_info() { echo -e "${GREEN}[dev]${NC} $1"; }
log_error() { echo -e "${RED}[error]${NC} $1" >&2; }

# Cleanup function
cleanup() {
    echo ""
    log_info "Shutting down services..."
    
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        log_backend "Stopping backend (PID: $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        log_frontend "Stopping frontend (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    # Kill any remaining processes on the ports
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    
    log_info "All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check prerequisites
check_prereqs() {
    if [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi
    
    if [[ ! -d "$FRONTEND_DIR" ]]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found. Please install Node.js"
        exit 1
    fi
}

# Start backend
start_backend() {
    log_backend "Starting backend server..."
    
    cd "$BACKEND_DIR"
    
    # Activate venv and start uvicorn
    if [[ -f ".venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source .venv/bin/activate
        uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT --reload 2>&1 | \
            sed "s/^/$(printf "${BLUE}[backend]${NC} ")/" &
        BACKEND_PID=$!
    else
        log_error "Backend venv not found. Run: cd backend && uv sync"
        exit 1
    fi
}

# Start frontend
start_frontend() {
    log_frontend "Starting frontend server..."
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        log_frontend "Installing dependencies..."
        npm install
    fi
    
    npm run dev 2>&1 | sed "s/^/$(printf "${CYAN}[frontend]${NC} ")/" &
    FRONTEND_PID=$!
}

# Wait for service to be ready
wait_for_service() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while ! nc -z localhost "$port" 2>/dev/null; do
        attempt=$((attempt + 1))
        if [[ $attempt -ge $max_attempts ]]; then
            log_error "$name failed to start on port $port"
            return 1
        fi
        sleep 0.5
    done
    return 0
}

# Main
main() {
    check_prereqs
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}             Knowledge Base Development Server                 ${GREEN}║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}  Backend:   ${BLUE}http://localhost:$BACKEND_PORT${NC}                           ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  Frontend:  ${CYAN}http://localhost:$FRONTEND_PORT${NC}                           ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  API Docs:  ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}                       ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "Press Ctrl+C to stop all services"
    echo ""
    
    # Start services
    start_backend
    sleep 2  # Give backend a head start
    start_frontend
    
    # Wait for both to be ready
    wait_for_service $BACKEND_PORT "Backend" && log_backend "Ready at http://localhost:$BACKEND_PORT"
    wait_for_service $FRONTEND_PORT "Frontend" && log_frontend "Ready at http://localhost:$FRONTEND_PORT"
    
    echo ""
    log_info "Both services are running. Watching for changes..."
    echo ""
    
    # Wait for processes
    wait
}

main "$@"
