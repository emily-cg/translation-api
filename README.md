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
