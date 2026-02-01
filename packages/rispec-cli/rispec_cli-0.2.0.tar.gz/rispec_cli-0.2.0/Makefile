.PHONY: build dist sdist bdist_wheel upload upload-test bump clean

build:
	hatch build

dist: build
	@echo "Distribution created in dist/"

sdist:
	hatch build --sdist

bdist_wheel:
	hatch build --wheel

upload: build
	twine upload dist/*

upload-test: build
	twine upload --repository testpypi dist/*

bump:
	python scripts/python/bump.py

clean:
	rm -rf build/ dist/ *.egg-info **/*.egg-info
