.PHONY: help setup env backend dev stop restart health logs status
.PHONY: dataset normalize merge regen-all
.PHONY: test test-fewshot test-backend eval eval-full
.PHONY: ray-dev ray-status ray-check ray-logs
.PHONY: clean

SHELL := /bin/bash

# Configuration
PYTHON := .venv/bin/python
BACKEND_PID := .backend.pid
BACKEND_LOG := .backend.log
BACKEND_PORT := 8000
RAYCAST_DIR := dashboard
RAYCAST_PID := .raycast-dev.pid

# Environment
export PYTHONPATH := $(PWD)

help: ## Show this help message
	@echo "DSPy Prompt Improver - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Install Python dependencies"
	@echo "  make env            - Create .env from .env.example"
	@echo ""
	@echo "Backend (DSPy + DeepSeek):"
	@echo "  make backend        - Start DSPy backend server (foreground)"
	@echo "  make dev            - Start backend in background (dev mode)"
	@echo "  make stop           - Stop background backend"
	@echo "  make restart        - Restart background backend"
	@echo "  make health         - Check backend health"
	@echo "  make logs           - Show backend logs (tail -f)"
	@echo "  make status         - Show backend status"
	@echo ""
	@echo "Raycast Frontend:"
	@echo "  make ray-check      - Check localhost permission in package.json"
	@echo "  make ray-dev        - Start Raycast dev server (with pre-check)"
	@echo "  make ray-status     - Show Raycast dev server status"
	@echo "  make ray-logs       - Show Raycast dev server logs"
	@echo ""
	@echo "Dataset Generation:"
	@echo "  make dataset        - Generate fewshot training dataset"
	@echo "  make normalize      - Normalize ComponentCatalog"
	@echo "  make merge          - Merge training datasets"
	@echo "  make regen-all      - Regenerate all datasets"
	@echo ""
	@echo "Testing & Evaluation:"
	@echo "  make test           - Run Python tests"
	@echo "  make test-fewshot   - Test few-shot compilation"
	@echo "  make test-backend   - Test backend integration"
	@echo "  make eval           - Run quality gates evaluation (5 cases)"
	@echo "  make eval-full      - Run full evaluation (30 cases)"
	@echo ""
	@echo "Utils:"
	@echo "  make clean          - Clean generated files"
	@echo ""
	@echo "Examples:"
	@echo "  make dev            # Start backend in background"
	@echo "  make ray-dev        # Start Raycast dev server"
	@echo "  make health         # Check if backend is running"
	@echo "  make stop           # Stop backend when done"

# =============================================================================
# Setup & Installation
# =============================================================================

setup: ## Install Python dependencies
	@printf "\033[34m→ Installing Python dependencies...\033[0m\n"
	@uv sync --all-extras

env: ## Create .env from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		printf "\033[32m✓ .env file created\033[0m\n"; \
	else \
		printf "\033[33m⚠️  .env already exists\033[0m\n"; \
	fi

# =============================================================================
# Backend
# =============================================================================

backend: ## Start DSPy backend server (foreground)
	@printf "\033[34m→ Starting DSPy backend on port $(BACKEND_PORT)...\033[0m\n"
	@$(PYTHON) main.py

dev: ## Start backend in background (for development)
	@printf "\033[34m→ Starting DSPy backend in background...\033[0m\n"
	@if [ -f $(BACKEND_PID) ]; then \
		pid=$$(cat $(BACKEND_PID)); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "\033[33m⚠️  Backend already running (PID: $$pid)\033[0m\n"; \
			exit 1; \
		fi; \
	fi
	@nohup $(PYTHON) main.py > $(BACKEND_LOG) 2>&1 & echo $$! > $(BACKEND_PID)
	@printf "\033[32m✓ Backend started in background\033[0m\n"
	@printf "\033[34m→ Logs: tail -f $(BACKEND_LOG)\033[0m\n"
	@sleep 2
	@$(MAKE) --silent health

stop: ## Stop background backend
	@printf "\033[34m→ Stopping backend...\033[0m\n"
	@if [ -f $(BACKEND_PID) ]; then \
		pid=$$(cat $(BACKEND_PID)); \
		if ps -p $$pid > /dev/null 2>&1; then \
			kill $$pid; \
			rm $(BACKEND_PID); \
			printf "\033[32m✓ Backend stopped\033[0m\n"; \
		else \
			rm $(BACKEND_PID); \
			printf "\033[33m⚠️  Backend was not running\033[0m\n"; \
		fi; \
	else \
		printf "\033[33m⚠️  No PID file found\033[0m\n"; \
	fi

restart: ## Restart backend
	@$(MAKE) --silent stop
	@$(MAKE) --silent dev

health: ## Check backend health
	@printf "\033[34m→ Checking backend health...\033[0m\n"
	@curl -s http://localhost:$(BACKEND_PORT)/health | python3 -m json.tool 2>/dev/null || printf "\033[33m⚠️  Backend not responding\033[0m\n"

logs: ## Show backend logs
	@tail -f $(BACKEND_LOG)

status: ## Show backend status
	@printf "\033[1mBackend Status:\033[0m\n"
	@if [ -f $(BACKEND_PID) ]; then \
		pid=$$(cat $(BACKEND_PID)); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "\033[32m● Running\033[0m (PID: $$pid)\n"; \
			echo ""; \
			$(MAKE) --silent health; \
		else \
			printf "\033[33m○ Stopped\033[0m (stale PID file)\n"; \
			rm $(BACKEND_PID); \
		fi; \
	else \
		printf "\033[33m○ Stopped\033[0m\n"; \
	fi

# =============================================================================
# Dataset Generation
# =============================================================================

dataset: ## Generate fewshot training dataset from cases.jsonl
	@printf "\033[34m→ Generating fewshot dataset...\033[0m\n"
	@$(PYTHON) scripts/data/generate_fewshot_dataset.py

normalize: ## Normalize ComponentCatalog to DSPy format
	@printf "\033[34m→ Normalizing ComponentCatalog...\033[0m\n"
	@$(PYTHON) scripts/data/fewshot/component_normalizer.py

merge: ## Merge training datasets
	@printf "\033[34m→ Merging datasets...\033[0m\n"
	@$(PYTHON) scripts/data/fewshot/merge_datasets.py

regen-all: normalize dataset merge ## Regenerate all datasets

# =============================================================================
# Testing & Evaluation
# =============================================================================

test: ## Run Python tests
	@printf "\033[34m→ Running Python tests...\033[0m\n"
	@uv run pytest

test-fewshot: ## Test few-shot compilation
	@printf "\033[34m→ Testing few-shot compilation...\033[0m\n"
	@$(PYTHON) scripts/data/fewshot/test_fewshot_compilation.py

test-backend: ## Test backend integration
	@printf "\033[34m→ Testing backend integration...\033[0m\n"
	@$(PYTHON) scripts/tests/test_fewshot_backend.py

eval: ## Run quality gates comparison (5 cases)
	@printf "\033[34m→ Running quality gates evaluation (5 cases)...\033[0m\n"
	@$(PYTHON) scripts/eval/compare_quality_gates.py --subset 5

eval-full: ## Run full quality gates evaluation (30 cases)
	@printf "\033[34m→ Running full quality gates evaluation (30 cases)...\033[0m\n"
	@$(PYTHON) scripts/eval/compare_quality_gates.py --subset 30

# =============================================================================
# Raycast Frontend
# =============================================================================

ray-check: ## Check localhost permission in package.json
	@printf "\033[34m→ Checking localhost permission...\033[0m\n"
	@if grep -q '"localhost": true' $(RAYCAST_DIR)/package.json; then \
		printf "\033[32m✓ Localhost permission is present\033[0m\n"; \
		printf "   Extension can connect to http://localhost:8000\n"; \
	else \
		printf "\033[31m✗ CRITICAL: Localhost permission MISSING from package.json\033[0m\n"; \
		printf "\n"; \
		printf "   Without this permission, the extension CANNOT connect to the DSPy backend.\n"; \
		printf "   You will see: 'DSPy backend not available' errors.\n"; \
		printf "\n"; \
		printf "   \033[33m🔧 FIX: Add this line to $(RAYCAST_DIR)/package.json after 'license':\033[0m\n"; \
		printf "\n"; \
		printf "   {\n"; \
		printf "     \"name\": \"prompt-improver-local\",\n"; \
		printf "     \"license\": \"MIT\",\n"; \
		printf "     \"localhost\": true,  // ← ADD THIS LINE\n"; \
		printf "     \"commands\": [...]\n"; \
		printf "   }\n"; \
		printf "\n"; \
		printf "   Then restart Raycast dev server.\n"; \
		exit 1; \
	fi

ray-dev: ## Start Raycast dev server (with permission pre-check)
	@$(MAKE) --silent ray-check
	@printf "\033[34m→ Starting Raycast dev server...\033[0m\n"
	@cd $(RAYCAST_DIR) && npm run dev

ray-status: ## Show Raycast dev server status
	@printf "\033[1mRaycast Dev Server Status:\033[0m\n"
	@if pgrep -f "ray develop" > /dev/null 2>&1; then \
		pid=$$(pgrep -f "ray develop"); \
		printf "\033[32m● Running\033[0m (PID: $$pid)\n"; \
	else \
		printf "\033[33m○ Stopped\033[0m\n"; \
		printf "\n   Start with: make ray-dev\n"; \
	fi

ray-logs: ## Show Raycast dev server logs
	@printf "\033[34m→ Tailing Raycast dev server logs...\033[0m\n"
	@if [ -f "$(RAYCAST_DIR)/.raycast/dev-server.log" ]; then \
		tail -f $(RAYCAST_DIR)/.raycast/dev-server.log; \
	else \
		printf "\033[33m⚠️  No Raycast dev server log found\033[0m\n"; \
		printf "   Start the dev server first: make ray-dev\n"; \
	fi

# =============================================================================
# Utils
# =============================================================================

clean: ## Clean generated files
	@printf "\033[34m→ Cleaning generated files...\033[0m\n"
	@rm -f $(BACKEND_PID) $(BACKEND_LOG)
	@rm -rf models/*.json
	@rm -f eval/quality-gates-comparison*.json
	@printf "\033[32m✓ Cleaned\033[0m\n"

# Default target
.DEFAULT_GOAL := help
