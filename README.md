# translation-api
Translation endpoint serving using transformers library for FuzzyLabs interview task.

## Requirements

- Docker (recommended)
- Python 3.11 (local)

## Run locally

Create/activate a venv and install deps:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Start the API:

```sh
uvicorn app.main:app --reload
```

Health checks:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Translate (first run downloads the model):

```sh
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"hello","source_lang":"en","target_lang":"fr"}'
```

## Streamlit UI (local)

Run the API first, then in another terminal:

```sh
streamlit run streamlit_app.py
```

Open: http://localhost:8501

Optional env var:

```sh
TRANSLATION_API_URL=http://localhost:8000 streamlit run streamlit_app.py
```

## Run with Docker (API only)

Build the image:

```sh
docker build -t translation-api .
```

Run the container:

```sh
docker run --rm -p 8000:8000 translation-api
```

Optionally, set worker count (defaults to 1):

```sh
docker run --rm -p 8000:8000 -e WEB_CONCURRENCY=2 translation-api
```

## Run with Docker Compose (API + Streamlit UI + Prometheus)

```sh
docker compose up --build
```

Open:

- API: http://localhost:8000/health
- UI: http://localhost:8501
- Prometheus: http://localhost:9090

## Environment variables

- `APP_VERSION` (optional): app version for logs, defaults to `unknown`
- `TRANSLATION_API_URL` (Streamlit): API base URL, defaults to `http://localhost:8000`
- `STREAMLIT_PUBLIC_URL` (Streamlit): UI URL shown in logs, defaults to `http://localhost:8501`
- `MAX_INPUT_TOKENS` (optional): max input tokens for translation, defaults to `512`
- `MAX_NEW_TOKENS` (optional): max output tokens for translation, defaults to `256`
- `WEB_CONCURRENCY` (Docker): number of Uvicorn workers, defaults to `1`
