OPAM ?= opam
DUNE ?= dune
NODE ?= node
PYTHON ?= python3
OCAML_VERSION ?= $(shell $(OPAM) exec -- ocamlc -version)
BUILD_DIR ?= _build-$(OCAML_VERSION)
.PHONY: format deps build api.check ci clean tree.check oracle.prepare test.install
build:
	$(OPAM) exec -- $(DUNE) build --build-dir $(BUILD_DIR) @all
api.check: build
	$(NODE) $(BUILD_DIR)/default/spike/output/spike/probe.js
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/spike.py
test.install: api.check
oracle.prepare:
	$(PYTHON) tools/prepare_oracles.py
format:
	$(OPAM) exec -- ocamlformat --check --impl lib/melange_bigarray.ml.in
	$(OPAM) exec -- $(DUNE) build --build-dir $(BUILD_DIR) @fmt
deps:
	$(OPAM) exec -- $(PYTHON) tools/check_tools.py
	npm ci
	npx playwright install --with-deps chromium --only-shell
tools.check:
	$(OPAM) exec -- $(PYTHON) tools/check_tools.py
test.offline:
	bash tools/offline.sh $(MAKE) test.differential
ci: tools.check oracle.prepare api.check format test.offline
	$(MAKE) tree.check
clean:
	$(OPAM) exec -- $(DUNE) clean --build-dir $(BUILD_DIR)
	rm -rf .cache/spike
tree.check:
	git diff --exit-code
	test -z "$$(git status --porcelain)"

.PHONY: traces.build test.node test.browser test.differential test.unit runtest test.properties test.stress
traces.build: build
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py build
test.node: traces.build
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py node
test.browser: traces.build
	OCAML_VERSION=$(OCAML_VERSION) timeout 180 $(NODE) tools/browser.cjs
test.differential: test.node test.browser
	$(OPAM) exec -- $(PYTHON) tools/api_coverage.py
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py compare
test.unit runtest test.properties: test.differential
test.stress:
	TRACE_COUNT=10000 $(MAKE) test.differential
