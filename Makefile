
BUILD=build
PYTHON=python

$(BUILD)/lexertab.json: src/lexergen.py src/lexerdef.json
	$(PYTHON) src/lexergen.py src/lexerdef.json $@
