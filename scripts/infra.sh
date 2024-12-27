#!/bin/bash

set -e

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"

function setup() {
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
    --template-body file://cloudformation.yml \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    | cat
}

function update_stack() {
  log "Updating aws cloudformation stack"

  aws cloudformation update-stack \
    --stack-name otel-observability \
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
    --query "Stacks[0].Outputs[?OutputKey==\`$output_key\`].OutputValue | [0]" \
    --output text)

  echo $ip
}

function get_queue_url() {
  queue_url=$(aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --query "Stacks[0].Outputs[?OutputKey==\`FilesQueueUrl\`].OutputValue | [0]" \
    --output text)

  echo $queue_url
}

function connect() {
  app=$1

  ip=$(get_ip $app)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" "ec2-user@$ip"
}

function destroy() {
  log "Deleting key pair"

  aws ec2 delete-key-pair --key-name otel-observability

  log "Emptying otel-files-service s3 bucket"

  aws s3 rm s3://otel-files-service --recursive

  log "Destroying cloudformation stack"

  aws cloudformation delete-stack --stack-name otel-observability

  log "Cleaning up"

  rm -rf otel-observability.pem
  rm -rf outputs.json
}

function output() {
  log "Getting outputs from cloudformation stack"

  aws cloudformation describe-stacks \
    --stack-name otel-observability \
    --query "Stacks[0].Outputs" \
    --output json \
    > outputs.json
}

function logs() {
  app=$1

  ip=$(get_ip $app)

  ssh -o StrictHostKeyChecking=no \
    -i "./otel-observability.pem" "ec2-user@$ip" \
    "docker logs -f otel-$app"
}