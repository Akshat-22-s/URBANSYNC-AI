FROM node:20-alpine

WORKDIR /app

# Install libc6-compat for compatibility with native packages on Alpine
RUN apk add --no-cache libc6-compat

# Copy package definition files
COPY package.json package-lock.json* ./

# Install dependencies using clean install if package-lock is present
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy application code
COPY . .

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the production application
RUN npm run build

# Expose web server port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the Next.js application
CMD ["npm", "start"]
