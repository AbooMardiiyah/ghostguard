.PHONY: dev dev-backend dev-frontend build up down logs test clean

# Local development
dev: dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npx vite --host 0.0.0.0 --port 5173

# Docker
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# Testing
test:
	cd backend && python -m pytest tests/ -v

# Cleanup
clean:
	docker compose down -v
	rm -f backend/data/db/*.db
