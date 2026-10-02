# =============================================================================
# AccessSlot Frontend — Production Dockerfile (multi-stage)
#
# Stage 1 (builder): Node 22 Alpine — installs deps, runs vite build
# Stage 2 (runner):  nginx Alpine   — serves the static dist/ output
#
# IMPORTANT: VITE_API_BASE_URL is a BUILD-TIME argument.
# Vite bakes the API URL into the JS bundle at build time — it cannot be
# changed at container runtime without rebuilding the image.
# =============================================================================

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first for layer cache optimisation
COPY package.json package-lock.json ./

# Install dependencies (ci = clean install, respects lock file)
RUN npm ci

# Accept the API base URL as a build argument.
# Default points to the local docker-compose backend service.
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy source code and build
COPY . .
RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS runner

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy built static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# nginx runs as pid 1 in foreground
CMD ["nginx", "-g", "daemon off;"]
