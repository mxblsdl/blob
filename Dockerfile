FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy current directory into working dir
COPY . .

# Copy SSL certificates
COPY certs /app/certs

# Make port 80 available to the world outside this container
EXPOSE 80

# Install git for development
# RUN apt update && apt install -y git

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--ssl-keyfile", "/app/certs/privkey.pem", "--ssl-certfile", "/app/certs/fullchain.pem"]
