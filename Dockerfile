FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=mcp_nexus.settings

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles /app/logs

RUN mkdir -p /app/logs
RUN chmod 777 /app/logs

# Run as non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Create the logs file if it doesn't exist
RUN touch /app/logs/mcp_nexus.log

# Command to run the application
CMD ["gunicorn", "mcp_nexus.wsgi:application", "--bind", "0.0.0.0:8000"]