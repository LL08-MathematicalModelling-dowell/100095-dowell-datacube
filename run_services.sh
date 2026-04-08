#!/bin/bash

# Bring up the backend service
docker compose up backend frontend

# 1. Build Backend first
docker compose -f docker-compose.prod_enhanced.yml build backend

# 2. Then Build UI
docker compose -f docker-compose.prod_enhanced.yml build react-app


docker exec nginx nginx -s reload

docker exec -it <backend_container_id> env | grep MONGO



