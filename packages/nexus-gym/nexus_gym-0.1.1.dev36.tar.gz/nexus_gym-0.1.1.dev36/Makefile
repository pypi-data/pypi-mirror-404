.PHONY: help install build-sim run-app run-example train eval

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies and JS dependencies
	pip install -e "."
	pip install -e ".[sb3]"
	cd sim && npm install

build-sim: ## Build the game simulation
	cd sim && npm run build
	mkdir -p src/nexus_env/static
	rm -rf src/nexus_env/static/*
	cp -r sim/dist/* src/nexus_env/static/

run-app: ## Run the FastAPI application locally
	python main_train.py

run-example: ## Run default example
	python examples/example.py

train: ## Train a model using Hydra defaults
	python scripts/train.py

eval: ## Evaluate a model using Hydra defaults
	python scripts/train.py mode=eval

release: ## Build and package for PyPI
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: git repository is dirty. Please commit changes or stash them."; \
		exit 1; \
	fi
	@echo "Building static assets..."
	$(MAKE) build-sim
	@echo "Building Python package (PyPI-safe version)..."
	SETUPTOOLS_SCM_LOCAL_SCHEME=no-local-version python -m build
	@echo "Build complete. Check dist/ folder."

force-release: clean ## Build and package for PyPI (ignoring git status)
	@echo "Building static assets..."
	$(MAKE) build-sim
	@echo "Building Python package (PyPI-safe version)..."
	SETUPTOOLS_SCM_LOCAL_SCHEME=no-local-version python -m build
	@echo "Build complete. Check dist/ folder."

clean: ## Clean build artifacts
	rm -rf dist/ build/ src/*.egg-info

publish-test: ## Upload dist/* to TestPyPI
	twine upload --repository testpypi dist/*

publish: ## Upload dist/* to PyPI
	twine upload dist/*
