# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package.json ./
COPY yarn.lock* ./

# Install dependencies (use --frozen-lockfile only if yarn.lock exists)
RUN yarn install

# Copy source code
COPY . .

# Build arguments for environment variables
ARG REACT_APP_BACKEND_URL
ARG REACT_APP_SQUARE_APPLICATION_ID
ARG REACT_APP_SQUARE_LOCATION_ID

ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV REACT_APP_SQUARE_APPLICATION_ID=$REACT_APP_SQUARE_APPLICATION_ID
ENV REACT_APP_SQUARE_LOCATION_ID=$REACT_APP_SQUARE_LOCATION_ID

# Build the app
RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
