FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY config ./config
COPY tests ./tests
RUN pip install --no-cache-dir -e '.[dev]'
CMD ["pytest", "-q"]
