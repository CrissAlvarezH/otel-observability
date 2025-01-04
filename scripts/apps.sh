#!/bin/bash

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"
source "$DIR/infra.sh"

function deploy_all() {
  frontend_ip=$(get_ip frontend)
  files_service_ip=$(get_ip files-service)
  auth_service_ip=$(get_ip auth-service)
  observability_ip=$(get_ip observability)

  run_pipeline_codebuild_deploy

  deploy_frontend $frontend_ip $files_service_ip $auth_service_ip $observability_ip

  deploy_auth_service $auth_service_ip $observability_ip

  deploy_files_service $files_service_ip $auth_service_ip $observability_ip

  deploy_observability_backend $observability_ip $frontend_ip

  wait_for_lambda_codebuild_to_finish $build_id

  log "Seeding tokens"
  curl -X POST http://$auth_service_ip/seed


  log "Deploy finished"
  log "INFRAESTRUCTURE:"
  echo "  Region: $AWS_REGION"
  echo "  Bucket: $S3_BUCKET_NAME"

  log "APPLICATIONS:"
  echo "  Frontend:  http://$frontend_ip"
  echo "  Files service:  http://$files_service_ip/docs"
  echo "  Auth service:  http://$auth_service_ip/docs"

  log "OBSERVABILITY:"
  echo "  Jaeger UI:  http://$observability_ip:16686\n"
}

function deploy_one() {
  app=$1

  frontend_ip=$(get_ip frontend)
  files_service_ip=$(get_ip files-service)
  auth_service_ip=$(get_ip auth-service)
  observability_ip=$(get_ip observability)

  if [ "$app" = "pipeline" ]; then
    run_pipeline_codebuild_deploy
    wait_for_lambda_codebuild_to_finish $build_id
  elif [ "$app" = "frontend" ]; then
    deploy_frontend $frontend_ip $files_service_ip $auth_service_ip $observability_ip
  elif [ "$app" = "files-service" ]; then
    deploy_files_service $files_service_ip $auth_service_ip $observability_ip
  elif [ "$app" = "auth-service" ]; then
    deploy_auth_service $auth_service_ip $observability_ip
    log "Seeding tokens"
    curl -X POST http://$auth_service_ip/seed
  elif [ "$app" = "observability" ]; then
    deploy_observability_backend $observability_ip $frontend_id
  else
    log "Invalid app"
    exit 1
  fi
}

function deploy_frontend() {
  frontend_ip=$1
  files_service_ip=$2
  auth_service_ip=$3
  observability_ip=$4

  log "Connecting to frontend instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" ec2-user@"$frontend_ip" << EOF
    cd /home/ec2-user/ 

    if [ ! -d 'otel-observability' ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/frontend
    echo 'VITE_API_DOMAIN=http://$files_service_ip' > .env
    echo 'VITE_AUTH_DOMAIN=http://$auth_service_ip' >> .env
    echo 'VITE_OTLP_EXPORTER_URL=http://$observability_ip:4318/v1/traces' >> .env
    docker build -t otel-frontend .
    docker stop otel-frontend 2>/dev/null || true
    docker rm otel-frontend 2>/dev/null || true
    docker run -d -p 80:80 --name otel-frontend otel-frontend
EOF
}

function deploy_files_service() {
  files_service_ip=$1
  auth_service_ip=$2
  observability_ip=$3

  log "Connecting to files service instance"

  queue_url=$(get_queue_url)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" ec2-user@"$files_service_ip" << EOF
    cd /home/ec2-user/

    if [ ! -d "otel-observability" ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/files-service
    echo "S3_BUCKET_NAME=$S3_BUCKET_NAME" > .env
    echo "AUTH_DOMAIN=http://$auth_service_ip" >> .env
    echo "AWS_REGION=$AWS_REGION" >> .env
    echo "SQS_QUEUE_URL=$queue_url" >> .env
    echo "OTLP_SPAN_EXPORTER_ENDPOINT=http://$observability_ip:4317" >> .env
    docker build -t otel-files-service .
    docker stop otel-files-service 2>/dev/null || true
    docker rm otel-files-service 2>/dev/null || true
    docker run -d -p 80:80 --name otel-files-service otel-files-service
EOF
}

function deploy_auth_service() {
  auth_service_ip=$1
  observability_ip=$2

  log "Connecting to auth service instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" ec2-user@"$auth_service_ip" << EOF
    cd /home/ec2-user/

    if [ ! -d "otel-observability" ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd apps/auth-service
    echo "AWS_REGION=$AWS_REGION" > .env
    echo "OTLP_SPAN_EXPORTER_ENDPOINT=http://$observability_ip:4317" >> .env
    docker build -t otel-auth-service .
    docker stop otel-auth-service 2>/dev/null || true
    docker rm otel-auth-service 2>/dev/null || true
    docker run -d -p 80:80 --name otel-auth-service otel-auth-service
EOF
}

function deploy_observability_backend() {
  observability_ip=$1
  frontend_id=$2

  log "Connecting to observability backend instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" ec2-user@"$observability_ip" << EOF
    cd /home/ec2-user/

    if [ ! -d 'otel-observability' ]; then 
      git clone https://github.com/CrissAlvarezH/otel-observability.git
      cd otel-observability
    else 
      cd otel-observability
      git pull --rebase
    fi

    cd observability

    echo "ALLOWED_ORIGINS=http://localhost:5173,http://$frontend_id" > .env

    docker-compose down
    docker-compose up -d
EOF
}

function run_pipeline_codebuild_deploy() {
  log "running pipeline codebuild"

  build_id=$(aws codebuild start-build \
    --project-name "otel-observability-pipeline-codebuild-project" \
    --region $AWS_REGION \
    --query "build.id" \
    --output text \
    | cat)
}

function wait_for_lambda_codebuild_to_finish() {
  log "waiting for build id: $build_id to finish"
  while true; do
    build_status=$(aws codebuild batch-get-builds \
      --ids $build_id \
      --query "builds[0].buildStatus" \
      --output text \
      --region $AWS_REGION \
      | cat)

    if [ "$build_status" == "SUCCEEDED" ]; then
      log "lambda function deployed successfully"
      break
    fi
    if [ "$build_status" == "FAILED" ]; then
      log "lambda function deployment failed"
      exit 1
    fi

    log "lambda codebuild deployment status: $build_status ... waiting 5 seconds"
    sleep 5
  done
}
