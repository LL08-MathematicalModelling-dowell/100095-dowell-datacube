FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Build the Vite app
RUN npm run build

# Install serve to run the built app
RUN npm install -g serve

# Serve the built app on port 3000
CMD ["serve", "-s", "dist", "-l", "3000"]

EXPOSE 3000

# FROM node:18-bullseye-slim

# WORKDIR /app

# # Update OS packages to pick up security patches, install minimal certs, and clean apt cache
# RUN apt-get update && \
# 	apt-get upgrade -y && \
# 	apt-get install -y --no-install-recommends ca-certificates && \
# 	rm -rf /var/lib/apt/lists/*

# COPY package.json package-lock.json ./
# # Use npm ci for reproducible installs from the lockfile
# RUN npm ci
# COPY . .
# RUN npm run build
# CMD ["npm", "start"]