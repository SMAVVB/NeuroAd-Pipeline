#!/bin/bash

# Neuro Pipeline Project Setup Script
# This script sets up the project environment, installs dependencies, and clones external tools

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
TOOLS_DIR="$PROJECT_ROOT/tools"
MODELS_DIR="$PROJECT_ROOT/models"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${GREEN}=== Neuro Pipeline Project Setup ===${NC}"
echo ""

# Step 1: Create virtual environment
echo -e "${YELLOW}[1/7] Creating Python 3.12 virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3.12 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created at $VENV_DIR${NC}"
else
    echo -e "${YELLOW}✓ Virtual environment already exists${NC}"
fi

# Step 2: Activate virtual environment
echo -e "${YELLOW}[2/7] Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 3: Install PyTorch with ROCm
echo -e "${YELLOW}[3/7] Installing PyTorch with ROCm support...${NC}"
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.2
echo -e "${GREEN}✓ PyTorch with ROCm installed${NC}"

# Step 4: Install base dependencies
echo -e "${YELLOW}[4/7] Installing base dependencies...${NC}"
pip install pillow requests numpy
echo -e "${GREEN}✓ Base dependencies installed${NC}"

# Step 5: Clone external tools
echo -e "${YELLOW}[5/7] Cloning external tools...${NC}"

# Clone TRIBE v2
if [ ! -d "$TOOLS_DIR/tribev2" ]; then
    git clone https://github.com/facebookresearch/tribev2 "$TOOLS_DIR/tribev2"
    echo -e "${GREEN}✓ TRIBE v2 cloned${NC}"
else
    echo -e "${YELLOW}✓ TRIBE v2 already exists${NC}"
fi

# Clone DeepGaze
if [ ! -d "$TOOLS_DIR/DeepGaze" ]; then
    git clone https://github.com/matthias-k/DeepGaze "$TOOLS_DIR/DeepGaze"
    echo -e "${GREEN}✓ DeepGaze cloned${NC}"
else
    echo -e "${YELLOW}✓ DeepGaze already exists${NC}"
fi

# Clone ViNet
if [ ! -d "$TOOLS_DIR/ViNet" ]; then
    git clone https://github.com/samyak0210/ViNet "$TOOLS_DIR/ViNet"
    echo -e "${GREEN}✓ ViNet cloned${NC}"
else
    echo -e "${YELLOW}✓ ViNet already exists${NC}"
fi

# Step 6: Install each tool in the venv
echo -e "${YELLOW}[6/7] Installing tools in virtual environment...${NC}"

# Install TRIBE v2
if [ -d "$TOOLS_DIR/tribev2" ]; then
    cd "$TOOLS_DIR/tribev2"
    pip install -e .
    echo -e "${GREEN}✓ TRIBE v2 installed${NC}"
    cd "$PROJECT_ROOT"
fi

# Install DeepGaze
if [ -d "$TOOLS_DIR/DeepGaze" ]; then
    cd "$TOOLS_DIR/DeepGaze"
    pip install -e .
    echo -e "${GREEN}✓ DeepGaze installed${NC}"
    cd "$PROJECT_ROOT"
fi

# Install ViNet
if [ -d "$TOOLS_DIR/ViNet" ]; then
    cd "$TOOLS_DIR/ViNet"
    pip install -e .
    echo -e "${GREEN}✓ ViNet installed${NC}"
    cd "$PROJECT_ROOT"
fi

# Step 7: Create .env file
echo -e "${YELLOW}[7/7] Creating .env file...${NC}"
cat > "$ENV_FILE" << EOF
# Neuro Pipeline Project Environment Configuration

# Project Paths
PROJECT_ROOT=$PROJECT_ROOT
VENV_DIR=$VENV_DIR
TOOLS_DIR=$TOOLS_DIR
MODELS_DIR=$MODELS_DIR

# Python Executable
PYTHON_EXECUTABLE=$VENV_DIR/bin/python

# External Tools
TRIBE_V2_DIR=$TOOLS_DIR/tribev2
DEEPGAZE_DIR=$TOOLS_DIR/DeepGaze
VINET_DIR=$TOOLS_DIR/ViNet

# Model Paths
MODEL_DIR=$MODELS_DIR
EOF
echo -e "${GREEN}✓ .env file created${NC}"

# Final setup
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo -e "${YELLOW}To activate the virtual environment, run:${NC}"
echo -e "  source $VENV_DIR/bin/activate"
echo ""
echo -e "${YELLOW}To run the pipeline, activate the venv first:${NC}"
echo -e "  source $VENV_DIR/bin/activate"
echo -e "  python validate_pipeline.py"
echo ""