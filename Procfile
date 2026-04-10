web: python run_production_migrations.py && gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-10000}
