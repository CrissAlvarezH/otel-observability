#!/bin/bash

set -e

# read .env file and set default values if there are no values
DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
if [ -f "$DIR/../.env" ]; then
  source "$DIR/../.env"
fi

if [ -z "$AWS_REGION" ]; then
  AWS_REGION="us-east-1"
fi

if [ -z "$S3_BUCKET_NAME" ]; then
  S3_BUCKET_NAME="otel-files-service"
fi


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
