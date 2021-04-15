help:
	@echo 'fixme                  - fix code formatting'
	@echo 'check                  - check code formatting'


fixme:
	echo "Starting linting"
	docker run --rm -v "${PWD}:/home/bot" -i fiskebot-tester "bash" "-c" "cd /fiskebot && isort bot && black bot"
	echo "Linting done!"

check:
	echo "Checking linting"
	docker run --rm -v "${PWD}:/home/bot" -i fiskebot-tester "bash" "-c" "cd /fiskebot && tox -e isort -e flake8 -e black"


.PHONY: help fixme check
