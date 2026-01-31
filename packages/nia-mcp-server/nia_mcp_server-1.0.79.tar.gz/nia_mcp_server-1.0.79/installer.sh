#!/bin/bash

# Nia MCP Server Bootstrap Installer
# This script installs Node.js if needed and runs the wizard
#
# Usage:
#   curl -fsSL https://app.trynia.ai/cli | sh
#   curl -fsSL https://app.trynia.ai/cli | sh -s -- nk_your_api_key
#   curl -fsSL https://app.trynia.ai/cli | sh -s -- --remote

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Check OS
check_os() {
    case "$OSTYPE" in
        darwin*) OS="macos" ;;
        linux*) OS="linux" ;;
        msys*|cygwin*|mingw*) OS="windows" ;;
        *)
            print_error "Unsupported operating system: $OSTYPE"
            exit 1
            ;;
    esac
}

# Check if Node.js is installed with required version
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ] 2>/dev/null; then
            print_success "Node.js $(node -v) found"
            return 0
        else
            print_warning "Node.js $(node -v) found but version 18+ required"
            return 1
        fi
    fi
    return 1
}

# Check if npx is available
check_npx() {
    command -v npx &> /dev/null
}

# Check if Homebrew is installed (macOS)
check_homebrew() {
    if command -v brew &> /dev/null; then
        return 0
    fi
    # Check Apple Silicon location
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        return 0
    fi
    # Check Intel Mac location
    if [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
        return 0
    fi
    return 1
}

# Install Homebrew (macOS)
install_homebrew() {
    print_info "Installing Homebrew..."
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        # Add to PATH for Apple Silicon
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        print_success "Homebrew installed"
        return 0
    fi
    return 1
}

# Install Node.js
install_node() {
    print_header "Installing Node.js"
    
    case "$OS" in
        macos)
            # Try Homebrew first (preferred on macOS)
            if check_homebrew || install_homebrew; then
                print_info "Installing Node.js via Homebrew..."
                if brew install node; then
                    print_success "Node.js installed via Homebrew"
                    return 0
                fi
            fi
            
            # Fallback to nvm
            print_info "Trying nvm installer..."
            if curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash; then
                export NVM_DIR="$HOME/.nvm"
                [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
                nvm install --lts
                print_success "Node.js installed via nvm"
                return 0
            fi
            ;;
            
        linux)
            # Try package manager
            if command -v apt-get &> /dev/null; then
                print_info "Installing Node.js via apt..."
                curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                sudo apt-get install -y nodejs
                print_success "Node.js installed"
                return 0
            elif command -v dnf &> /dev/null; then
                print_info "Installing Node.js via dnf..."
                sudo dnf install -y nodejs
                print_success "Node.js installed"
                return 0
            elif command -v yum &> /dev/null; then
                print_info "Installing Node.js via yum..."
                curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                sudo yum install -y nodejs
                print_success "Node.js installed"
                return 0
            elif command -v pacman &> /dev/null; then
                print_info "Installing Node.js via pacman..."
                sudo pacman -S --noconfirm nodejs npm
                print_success "Node.js installed"
                return 0
            fi
            
            # Fallback to nvm
            print_info "Trying nvm installer..."
            if curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash; then
                export NVM_DIR="$HOME/.nvm"
                [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
                nvm install --lts
                print_success "Node.js installed via nvm"
                return 0
            fi
            ;;
            
        windows)
            print_error "On Windows, please install Node.js manually from https://nodejs.org"
            print_info "Then run: npx @nia/wizard"
            exit 1
            ;;
    esac
    
    print_error "Could not install Node.js automatically"
    print_info "Please install Node.js 18+ manually: https://nodejs.org"
    print_info "Then run: npx @nia/wizard"
    exit 1
}

# Main
main() {
    print_header "Nia MCP Server Installer"
    
    echo -e "${CYAN}"
    cat << "EOF"
    ███╗   ██╗██╗ █████╗
    ████╗  ██║██║██╔══██╗
    ██╔██╗ ██║██║███████║
    ██║╚██╗██║██║██╔══██║
    ██║ ╚████║██║██║  ██║
    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
EOF
    echo -e "${NC}"
    
    check_os
    
    # Check/install Node.js
    if ! check_node; then
        print_info "Node.js 18+ is required"
        install_node
        
        # Re-check after install
        if ! check_node; then
            print_error "Node.js installation failed"
            exit 1
        fi
    fi
    
    # Verify npx
    if ! check_npx; then
        print_error "npx not found. Please ensure Node.js is properly installed."
        print_info "Try running: npm install -g npm"
        exit 1
    fi
    
    echo ""
    print_info "Starting Nia wizard..."
    echo ""
    
    # Run the wizard from a neutral directory to avoid package.json conflicts
    cd "$HOME" || cd /tmp
    
    # Run the wizard with any passed arguments
    exec npx nia-wizard "$@"
}

main "$@"
