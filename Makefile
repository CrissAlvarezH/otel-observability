
.PHONY: setup deploy get-ip output connect destroy

setup:
	sh scripts/entrypoint.sh setup

status:
	sh scripts/entrypoint.sh status

deploy:
	sh scripts/entrypoint.sh deploy

get-ip:
	sh scripts/entrypoint.sh get-ip ${app}

output:
	sh scripts/entrypoint.sh output

connect:
	sh scripts/entrypoint.sh connect ${app}

logs:
	sh scripts/entrypoint.sh logs ${app}

destroy:
	sh scripts/entrypoint.sh destroy
