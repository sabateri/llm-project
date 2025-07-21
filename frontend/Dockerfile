# Multi-stage build for React app
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
#COPY frontend/package*.json ./
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .
#COPY frontend/ ./

# Build the React app
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built React app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
#COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]