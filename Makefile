help:
	@echo 'fixme                  - fix code formatting'
	@echo 'check                  - check code formatting'
	@echo 'build                  - build the image used for fixme & check'

fixme: build
	echo "Starting linting"
	docker run --rm -v "${PWD}:/home/bot" --user="1000:1000" -i bot-tester "bash" "-c" "cd /home/bot && isort bot && black bot"
	echo "Linting done!"

check: build
	echo "Checking linting"
	docker run --rm -v "${PWD}:/home/bot" -i bot-tester "bash" "-c" "cd /home/bot && tox -e isort -e flake8 -e black"

build:
	echo "building bot-tester"
	docker build . -f Dockerfile.tester -t bot-tester

.PHONY: help fixme check build
