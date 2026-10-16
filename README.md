# Stats CORS API

FastAPI service for dynamically computing summary statistics from a comma-separated integer query string. It permits browser CORS requests only from `https://dash-v2r2tu.example.com` and adds `X-Request-ID` and `X-Process-Time` to all HTTP responses, including preflights and errors.

## Endpoint

`GET /stats?values=1,2,3`

Example response:

```json
{
  "email": "23f2000363@ds.study.iitm.ac.in",
  "count": 3,
  "sum": 6,
  "min": 1,
  "max": 3,
  "mean": 2.0
}
```

The values above are an example only; the service computes the result for every request.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux/WSL: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Try `http://127.0.0.1:8000/stats?values=1,2,3` and `http://127.0.0.1:8000/health`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Deploy to Render

1. Upload these project files to a GitHub repository.
2. In Render, choose **New + → Blueprint** (or create a Python web service from the repository).
3. Select the repository containing `render.yaml`; Render will use the included free web-service configuration.
4. Wait for deployment to complete. Render will show a public URL like `https://stats-cors-api-<suffix>.onrender.com`.
5. Verify `/health`, then verify `/stats?values=10,20,-3` on that deployed URL. Submit the base URL (without `/stats`) to the grader.

The `render.yaml` defines a free web service with `uvicorn main:app --host 0.0.0.0 --port $PORT` and uses `/health` as its health check.
