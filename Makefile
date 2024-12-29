
.PHONY: setup status deploy get-ip output connect logs destroy

setup:
	sh scripts/entrypoint.sh setup

info:
	sh scripts/entrypoint.sh info

update:
	sh scripts/entrypoint.sh update

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

amis:
	@echo "Getting last AMIs (Amazon Linux 2 x86_64) by region"
	@for region in $$(aws ec2 describe-regions --query "Regions[].RegionName" --output text); do \
		AMI=$$(aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" --query 'sort_by(Images, &CreationDate)[-1].ImageId' --region $$region --output text); \
		echo "$$region:\n  AMI: $$AMI"; \
	done
