# translation-api
Translation endpoint serving using transformers library for FuzzyLabs interview task

## Run with Docker

Build the image:

```sh
docker build -t translation-api .
```

Run the container:

```sh
docker run --rm -p 8000:8000 translation-api
```

Health check:

```sh
curl http://localhost:8000/health
```

Readiness check:

```sh
curl http://localhost:8000/ready
```

## Streamlit UI (optional)

Run the API first, then in another terminal:

```sh
pip install -r requirements.txt -r requirements-dev.txt
streamlit run streamlit_app.py
```

By default it calls `http://localhost:8000`. To change it:

```sh
TRANSLATION_API_URL=http://localhost:8000 streamlit run streamlit_app.py
```

## Run with Docker Compose (API + Streamlit UI)

Build and start both containers:

```sh
docker compose up --build
```

Then open:

- API: http://localhost:8000/health
- UI: http://localhost:8501
