#!/bin/bash

function log() {
  GREEN='\033[0;32m'
  YELLOW="\033[0;33m"
  COLOR_OFF="\033[0m"

  if [ "$2" = "warn" ]; then
    color="$YELLOW"
  else
    color="$GREEN"
  fi

  printf "\n${color}$1${COLOR_OFF}\n"
}

action=$1

if [ "$action" == "setup" ]; then

  log "Creating key pairs to access instances"

  aws ec2 create-key-pair \
    --key-name otel-observability \
    --query 'KeyMaterial' \
    --output text > otel-observability.pem

  chmod 400 otel-observability.pem

  if [ ! -f "otel-observability.pem" ]; then
    log "An error occurred creating key pairs" "error"
    exit 1
  fi

  log "Creating aws cloudformation stack"

  aws cloudformation create-stack \
    --stack-name otel-observability \
    --template-body file://cloudformation/main.yml \
    --capabilities CAPABILITY_NAMED_IAM \
    | cat

elif [ "$action" == "deploy" ]; then
  log "Connecting to frontend instance"

  frontend_ip=$(sh scripts.sh get-ip frontend)
  files_service_ip=$(sh scripts.sh get-ip files-service)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" ec2-user@"$frontend_ip" \
    "cd /home/ec2-user/ && \
    if [ ! -d 'otel-observability' ]; then \
      git clone https://github.com/CrissAlvarezH/otel-observability.git && \
      cd otel-observability; \
    else \
      cd otel-observability && \
      git pull; \
    fi && \
    cd apps/frontend && \
    echo 'VITE_API_DOMAIN=http://$files_service_ip' > .env && \
    docker build -t otel-frontend . && \
    docker stop otel-frontend 2>/dev/null || true && \
    docker rm otel-frontend 2>/dev/null || true && \
    docker run -d -p 80:80 --name otel-frontend otel-frontend"

  log "Connecting to files service instance"

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" ec2-user@"$files_service_ip" \
    'cd /home/ec2-user/ && \
    if [ ! -d "otel-observability" ]; then \
      git clone https://github.com/CrissAlvarezH/otel-observability.git && \
      cd otel-observability; \
    else \
      cd otel-observability && \
      git pull; \
    fi && \
    cd apps/files-service && \
    echo "S3_BUCKET_NAME=otel-files-service" > .env && \
    docker build -t otel-files-service . && \
    docker stop otel-files-service 2>/dev/null || true && \
    docker rm otel-files-service 2>/dev/null || true && \
    docker run -d -p 80:80 --name otel-files-service otel-files-service'

  log "Deploy finished"
  log "Frontend: http://$frontend_ip"
  log "Files service: http://$files_service_ip"

elif [ "$action" == "get-ip" ]; then
  service=$2

  output_key=""
  if [ "$service" == "frontend" ]; then
    output_key="FrontendInstancePublicIp"
  elif [ "$service" == "files-service" ]; then
    output_key="FilesServiceInstancePublicIp"
  else
    log "Invalid service" "error"
  fi

  ip=$(aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --query "Stacks[0].Outputs[?OutputKey==\`$output_key\`].OutputValue | [0]" \
    --output text)

  echo $ip

elif [ "$action" == "output" ]; then
  log "Getting outputs from cloudformation stack"

  aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --query "Stacks[0].Outputs" \
    --output json \
    > outputs.json

elif [ "$action" == "connect" ]; then
  service=$2

  ip=$(sh scripts.sh get-ip $service)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" "ec2-user@$ip"

elif [ "$action" == "destroy" ]; then
  log "Destroying cloudformation stack"

  aws cloudformation delete-stack --stack-name otel-observability

  log "Deleting key pair"

  aws ec2 delete-key-pair --key-name otel-observability

  log "Cleaning up"

  rm -rf otel-observability.pem
  rm -rf outputs.json
  rm -rf output-frontend-user-data.txt
  rm -rf output-files-service-user-data.txt

else
  log "Invalid action" "error"
  exit 1
fi
