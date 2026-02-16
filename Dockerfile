FROM python:3.13-slim

RUN set -e

# Set the working directory in the container
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

RUN pip install uv

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Copy current directory into working dir
COPY . .

# Copy SSL certificates
# COPY certs /app/certs

# Make port 1234 available to the world outside this container
EXPOSE 1234

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "1234"]
