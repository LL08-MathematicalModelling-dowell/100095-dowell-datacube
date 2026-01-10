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