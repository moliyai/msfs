-include .env

docker-up:
	@docker compose up

docker-down:
	@docker compose down

docker-rebuild:
	@docker compose up -d --build