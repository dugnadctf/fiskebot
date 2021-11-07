help:
	@echo 'fixme                  - fix code formatting'
	@echo 'check                  - check code formatting'
	@echo 'build                  - build the image used for fixme & check'

fixme: build
	echo "Starting linting"
	docker run --rm -v "${PWD}:/home/bot" --user="1000:1000" -i bot-tester "bash" "-c" "cd /home/bot && isort bot && isort tools && black bot && black tools"
	echo "Linting done!"

check: build
	echo "Checking linting"
	docker run --rm -v "${PWD}:/home/bot" -i bot-tester "bash" "-c" "cd /home/bot && tox -e isort_bot && tox -e isort_tools -e flake8 -e black_bot -e black_tools"

build:
	echo "building bot-tester"
	docker build . -f Dockerfile.tester -t bot-tester

.PHONY: help fixme check build
