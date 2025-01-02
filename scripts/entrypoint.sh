#!/bin/bash

DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source "$DIR/base.sh"
source "$DIR/infra.sh"
source "$DIR/apps.sh"

action=$1

case $action in
  setup)
    setup
  ;;
  info)
    info
  ;;
  update)
    update_stack
  ;;
  status)
    get_stack_status
  ;;
  deploy)
    deploy_all
  ;;
  deploy-one)
    deploy_one $2
  ;;
  get-ip)
    get_ip $2
  ;;
  output)
    output
  ;;
  connect)
    connect $2
  ;;
  logs)
    logs $2
  ;;
  destroy)
    destroy
  ;;
  *)
  log "Invalid action" "error"
  exit 1
  ;;
esac