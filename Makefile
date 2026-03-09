.PHONY: backend frontend

backend:
	cd "$(CURDIR)/backend" && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd "$(CURDIR)/frontend" && npm run dev
