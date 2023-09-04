# Use the official image as a parent image.
FROM nodered/node-red:latest

# Copy flows file
COPY flows.json /data/flows.json

# Copy config file
COPY shared/config.json /app/config.json

# Install node-red-dashboard
RUN npm install node-red-dashboard
