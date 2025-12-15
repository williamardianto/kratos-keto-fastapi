FROM python:3.13-slim-bullseye

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory.
WORKDIR /app

# Copy dependency files first for better layer caching.
COPY pyproject.toml uv.lock ./

# Install the application dependencies inside Docker.
RUN uv sync --locked --no-cache

# Copy the rest of the application code.
COPY . .

# Set PYTHONPATH to include the working directory
ENV PYTHONPATH=/app

# Run the application using uvicorn (more reliable than fastapi CLI)
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
