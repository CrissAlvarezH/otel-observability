#!/bin/bash

set -e

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"


function setup() {
  log "Region: $AWS_REGION"
  log "Destination bucket: $S3_BUCKET_NAME"

  log "Validation s3 bucket $S3_BUCKET_NAME is available"

  if aws s3 ls s3://$S3_BUCKET_NAME 2>/dev/null; then
    log "Bucket already exists" "error"
    exit 1
  fi

  log "Creating key pairs to access instances"

  aws ec2 create-key-pair \
    --key-name otel-observability-$AWS_REGION \
    --region $AWS_REGION \
    --query 'KeyMaterial' \
    --output text > "otel-observability-$AWS_REGION.pem"

  chmod 400 "otel-observability-$AWS_REGION.pem"

  if [ ! -f "otel-observability-$AWS_REGION.pem" ]; then
    log "An error occurred creating key pairs" "error"
    exit 1
  fi

  log "Creating aws cloudformation stack"

  aws cloudformation create-stack \
    --region $AWS_REGION \
    --stack-name otel-observability \
    --template-body file://cloudformation.yml \
    --parameters ParameterKey=BucketName,ParameterValue=$S3_BUCKET_NAME \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    | cat
}

function info() {
  frontend_ip=$(get_ip frontend)
  files_service_ip=$(get_ip files-service)
  auth_service_ip=$(get_ip auth-service)

  log "INFRAESTRUCTURE:\n  Region: $AWS_REGION \n  Destination bucket: $S3_BUCKET_NAME"

  log "APPLICATIONS:\n  Frontend: http://$frontend_ip \n  Files service: http://$files_service_ip/docs \n  Auth service: http://$auth_service_ip/docs\n"
}

function update_stack() {
  log "Updating aws cloudformation stack"

  aws cloudformation update-stack \
    --stack-name otel-observability \
    --region $AWS_REGION \
    --template-body file://cloudformation.yml \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    | cat
}

function get_stack_status() {

  while true; do
    clear
    log "... Getting stack status <Ctrl+C to stop>"

    status=$(aws cloudformation describe-stacks \
      --stack-name otel-observability \
      --region $AWS_REGION \
      --query "Stacks[0].StackStatus" \
      --output text)

    log "Stack status: $status"
    sleep 2
  done
}

function get_ip() {
  app=$1

  output_key=""
  if [ "$app" == "frontend" ]; then
    output_key="FrontendInstancePublicIp"
  elif [ "$app" == "files-service" ]; then
    output_key="FilesServiceInstancePublicIp"
  elif [ "$app" == "auth-service" ]; then
    output_key="AuthServiceInstancePublicIp"
  else
    log "Invalid app" "error"
    exit 1
  fi

  ip=$(aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --region $AWS_REGION \
    --query "Stacks[0].Outputs[?OutputKey==\`$output_key\`].OutputValue | [0]" \
    --output text)

  echo $ip
}

function get_queue_url() {
  queue_url=$(aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --region $AWS_REGION \
    --query "Stacks[0].Outputs[?OutputKey==\`FilesQueueUrl\`].OutputValue | [0]" \
    --output text)

  echo $queue_url
}

function connect() {
  app=$1

  ip=$(get_ip $app)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" "ec2-user@$ip"
}

function destroy() {
  log "Deleting key pair"

  aws ec2 delete-key-pair \
    --region $AWS_REGION \
    --key-name otel-observability-$AWS_REGION 2>&1 || echo "Error deleting key pair: $?"

  if aws s3 ls s3://$S3_BUCKET_NAME 2>/dev/null; then
    log "Emptying $S3_BUCKET_NAME s3 bucket"
    aws s3 rm s3://$S3_BUCKET_NAME --recursive  
  fi

  log "Destroying cloudformation stack"

  aws cloudformation delete-stack \
    --region $AWS_REGION \
    --stack-name otel-observability 2>&1 || echo "Error deleting stack: $?"

  log "Cleaning up"

  rm -rf "otel-observability-$AWS_REGION.pem"
  rm -rf outputs.json
}

function output() {
  log "Getting outputs from cloudformation stack"

  aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --region $AWS_REGION \
    --query "Stacks[0].Outputs" \
    --output json \
    > outputs.json
}

function logs() {
  app=$1

  ip=$(get_ip $app)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability-$AWS_REGION.pem" "ec2-user@$ip" \
    "docker logs -f otel-$app"
}
