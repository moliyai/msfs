-include .env

docker-up:
	@docker compose up

docker-down:
	@docker compose down

docker-rebuild:
	@docker compose up -d --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Done."
