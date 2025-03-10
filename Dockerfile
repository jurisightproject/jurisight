# Use a base image with Node.js and Python
FROM node:18-bullseye

# Set the working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y python3-pip python3-dev git

# Install Python dependencies first (cached for faster builds)
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy package.json and install Node.js dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Download the Hugging Face model during build
RUN mkdir -p /app/legal_led_model && \
    python3 -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; \
                model_path = 'Jurisight/legal_led'; \
                model = AutoModelForSeq2SeqLM.from_pretrained(model_path); \
                tokenizer = AutoTokenizer.from_pretrained(model_path); \
                model.save_pretrained('/app/legal_led_model'); \
                tokenizer.save_pretrained('/app/legal_led_model')"

# Copy the rest of the application code
COPY . .

# Expose the necessary port (Render assigns dynamically)
EXPOSE 3000  

# Start Flask first, then Express (prevents race conditions)
CMD ["sh", "-c", "python3 chatbot.py & npm start"]