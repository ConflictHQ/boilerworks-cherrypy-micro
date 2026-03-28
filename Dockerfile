FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["python", "-m", "app"]
