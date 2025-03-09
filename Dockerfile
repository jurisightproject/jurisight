# Use a base image with Node.js and Python
FROM node:18-bullseye

# Set the working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y python3-pip python3-dev

# Copy and install Python dependencies first to leverage caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy package.json and install Node.js dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy the trained model into the container
COPY legal_led_model /app/legal_led_model

# Copy the rest of the application code
COPY . .

# Expose necessary ports (Render assigns them dynamically)
EXPOSE 3000

# Start both Flask and Node.js servers
CMD ["sh", "-c", "python3 chatbot.py & npm start"]