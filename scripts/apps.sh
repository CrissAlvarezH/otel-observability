#!/bin/bash

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"
source "$DIR/infra.sh"

function deploy() {
  frontend_ip=$(get_ip frontend)
  files_service_ip=$(get_ip files-service)
  auth_service_ip=$(get_ip auth-service)

  log "Connecting to frontend instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" ec2-user@"$frontend_ip" << EOF
    cd /home/ec2-user/ 

    if [ ! -d 'otel-observability' ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/frontend
    echo 'VITE_API_DOMAIN=http://$files_service_ip' >> .env
    echo 'VITE_AUTH_DOMAIN=http://$auth_service_ip' >> .env
    docker build -t otel-frontend .
    docker stop otel-frontend 2>/dev/null || true
    docker rm otel-frontend 2>/dev/null || true
    docker run -d -p 80:80 --name otel-frontend otel-frontend
EOF

  log "Connecting to files service instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" ec2-user@"$files_service_ip" << EOF
    cd /home/ec2-user/

    if [ ! -d "otel-observability" ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/files-service
    echo "S3_BUCKET_NAME=otel-files-service" >> .env
    echo 'AUTH_DOMAIN=http://$auth_service_ip' >> .env
    docker build -t otel-files-service .
    docker stop otel-files-service 2>/dev/null || true
    docker rm otel-files-service 2>/dev/null || true
    docker run -d -p 80:80 --name otel-files-service otel-files-service
EOF

  log "Connecting to auth service instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" ec2-user@"$auth_service_ip" << EOF
    cd /home/ec2-user/

    if [ ! -d "otel-observability" ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/auth-service
    docker build -t otel-auth-service .
    docker stop otel-auth-service 2>/dev/null || true
    docker rm otel-auth-service 2>/dev/null || true
    docker run -d -p 80:80 --name otel-auth-service otel-auth-service
EOF

  log "Seeding tokens"
  sleep 3
  curl -X POST http://$auth_service_ip/seed

  log "\nDeploy finished"
  log "Frontend: http://$frontend_ip"
  log "Files service: http://$files_service_ip/docs"
  log "Auth service: http://$auth_service_ip/docs"
}
