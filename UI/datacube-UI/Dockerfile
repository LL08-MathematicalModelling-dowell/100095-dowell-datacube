# --- Stage 1: Build ---
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Timeout fixes for unstable connections
RUN npm config set fetch-retry-maxtimeout 1200000 && \
    npm config set fetch-retries 10 && \
    npm install

# Copy source and build
COPY . .
RUN npm run build

# --- Stage 2: Production ---
FROM nginx:stable-alpine

# Copy the static build from the builder stage
# Vite builds to 'dist', standard React builds to 'build'
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 (Nginx default)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
