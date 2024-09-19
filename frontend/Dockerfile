# Specify the base image (use a specific version for consistency)
FROM node:latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies using npm ci for lockfile consistency
RUN npm install

# Install Vite globally
RUN npm install -g vite

# Copy the rest of the application code
COPY . .

# Expose the port the Vite app runs on
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev"]