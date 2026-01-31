---
title: Nexus Gym
emoji: 🚀
colorFrom: red
colorTo: red
sdk: docker
app_port: 7860
app_file: main_train.py
tags:
- fastapi
- reinforcement-learning
- gymnasium
pinned: false
short_description: NEXUS - an AI-powered platformer game with procedural level
license: apache-2.0
---

# Nexus Gym

A Gymnasium environment for the Nexus Platformer game, capable of training reinforcement learning agents via WebSocket communication.

## Installation

```bash
pip install nexus-gym
```

## Release Process

This project uses `setuptools_scm` for versioning, meaning the package version is derived automatically from Git tags.

### 1. Tag the Release
Create a new tag for the version you want to release (e.g., v0.1.0).

```bash
git tag v0.1.0
git push origin v0.1.0
# Or to push all tags: git push origin --tags
```

**Note:** The `make release` command will fail if your git repository has uncommitted changes. Ensure you are in a clean state.

### 2. Build the Package
This command runs the `npm` build for the game simulation and packages the Python project.

```bash
make release
```

### 3. Publish to TestPyPI (Optional)
It is recommended to upload to TestPyPI first to verify everything looks correct.

```bash
make publish-test
```

### 4. Publish to PyPI
When you are ready to publish the official release:

```bash
make publish
```
