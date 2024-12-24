#!/bin/bash

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"
source "$DIR/infra.sh"

function deploy_all() {
  frontend_ip=$(get_ip frontend)
  files_service_ip=$(get_ip files-service)
  auth_service_ip=$(get_ip auth-service)

  deploy_frontend $frontend_ip $files_service_ip $auth_service_ip

  deploy_auth_service $auth_service_ip

  deploy_files_service $files_service_ip $auth_service_ip

  deploy_pipeline_function 

  log "Seeding tokens"
  curl -X POST http://$auth_service_ip/seed

  log "\nDeploy finished"
  log "Frontend: http://$frontend_ip"
  log "Files service: http://$files_service_ip/docs"
  log "Auth service: http://$auth_service_ip/docs"
}

function deploy_frontend() {
  frontend_ip=$1
  files_service_ip=$2
  auth_service_ip=$3

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
}

function deploy_files_service() {
  files_service_ip=$1
  auth_service_ip=$2

  log "Connecting to files service instance"

  queue_url=$(get_queue_url)

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
    echo "AUTH_DOMAIN=http://$auth_service_ip" >> .env
    echo "SQS_QUEUE_URL=$queue_url" >> .env
    docker build -t otel-files-service .
    docker stop otel-files-service 2>/dev/null || true
    docker rm otel-files-service 2>/dev/null || true
    docker run -d -p 80:80 --name otel-files-service otel-files-service
EOF
}

function deploy_auth_service() {
  auth_service_ip=$1

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
}

function deploy_pipeline_function() {
  log "deploying pipeline function"
  filename="pipeline-function.zip"

  log "packaging dependencies"
  cd apps/load-pipeline
  poetry export --without-hashes --format=requirements.txt --output=requirements.txt
  pip install -r requirements.txt --target ./package
  cd ./package
  zip -r "../$filename" .
  cd ..

  log "including code app to package"
  zip -r $filename src

  # cleanup
  rm requirements.txt 
  rm -r package

  log "pipeline package $filename created successfully"

  log "updating pipeline lambda code"

  aws lambda update-function-code \
    --function-name "otel-observability-pipeline-function" \
    --zip-file "fileb://$filename" \
    | cat

  rm $filename

  # come back to the project root directory
  cd ../.. 
}
