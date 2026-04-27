#!/bin/bash

# Bring up the backend service
docker compose up backend frontend

# 1. Build Backend first
docker compose -f docker-compose.prod_enhanced.yml build backend

# 2. Then Build UI
docker compose -f docker-compose.prod_enhanced.yml build react-app


docker exec nginx nginx -s reload

docker exec -it <backend_container_id> env | grep MONGO

sudo docker exec nginx nginx -s reload   # if nginx runs in a container
# OR
sudo systemctl reload nginx              # if installed on host


sudo mkdir -p /var/www/demo
sudo chown www-data:www-data /var/www/demo


# In your docker-compose.prod_enhanced.yml, add the following under the nginx service to mount the demo files:
volumes:
      - /home/DowellDataCube/100095-dowell-datacube/Playground:/usr/share/nginx/html/demo