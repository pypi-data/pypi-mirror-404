# =================================
# Stage 1: Build frontend assets
# =================================
FROM node:20-slim AS node-build

WORKDIR /app

# Copy only package files first for caching
COPY sim/package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source files
COPY sim/ ./

# Build frontend
RUN npm run build

# =================================
# Stage 2: Python runtime
# =================================
FROM python:3.11-slim AS python-runtime

# Avoid prompts and enforce production-friendly Python
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .[sb3]
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend assets from Node stage
COPY --from=node-build /app/dist ./src/nexus_env/static

# Expose default HF port
EXPOSE 7860

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:7860/ || exit 1

# Entrypoint for RL training
ENTRYPOINT ["python", "main_train.py"]
CMD ["env.theme=cyber_district", "algo=ppo_stable"]
