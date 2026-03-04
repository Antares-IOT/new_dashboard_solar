# # Base image
# FROM node:18-alpine AS builder

# WORKDIR /app

# # Copy package files
# COPY package*.json ./

# # Install dependencies
# RUN npm install

# # Copy source code
# COPY . .

# # Build Next.js app
# RUN npm run build

# # Production image
# FROM node:18-alpine

# WORKDIR /app

# # Copy package files
# COPY package*.json ./

# # Install production dependencies only
# RUN npm ci --only=production

# # Copy built app from builder
# COPY --from=builder /app/.next ./.next
# COPY --from=builder /app/public ./public

# # Expose port
# EXPOSE 5028

# # Set NODE_ENV
# ENV NODE_ENV=production

# # Start app
# CMD ["npm", "start"]


# Base image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy requirements terlebih dahulu
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua source code
COPY . .

# Expose port (samakan dengan app kamu)
EXPOSE 5028

# Run app
CMD ["python", "app.py"]