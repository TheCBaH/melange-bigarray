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
test.install: oracle.prepare
	$(PYTHON) tools/install.py
oracle.prepare:
	$(PYTHON) tools/prepare_oracles.py
format:
	$(OPAM) exec -- ocamlformat --check --impl lib/melange_bigarray.ml.in
	$(OPAM) exec -- $(DUNE) build --build-dir $(BUILD_DIR) @fmt
deps:
	$(OPAM) exec -- $(PYTHON) tools/check_tools.py
	npm ci
	npx playwright install --with-deps $(or $(BROWSER_ENGINE),chromium)
tools.check:
	$(OPAM) exec -- $(PYTHON) tools/check_tools.py
test.offline:
	bash tools/offline.sh $(MAKE) test.differential
ci: deps tools.check oracle.prepare api.check format
	$(MAKE) test.offline
	$(MAKE) test.replay
	$(MAKE) bench
	$(MAKE) test.install
	$(MAKE) tree.check
clean:
	$(PYTHON) tools/clean.py
tree.check:
	git diff --exit-code
	test -z "$$(git status --porcelain)"

.PHONY: traces.build test.node test.browser test.differential test.unit runtest test.properties test.stress
traces.build: build
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py build
test.node: traces.build
	OCAML_VERSION=$(OCAML_VERSION) timeout 120 $(NODE) --max-old-space-size=256 tools/extensions_node.cjs
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py node
clients.build: traces.build
	$(OPAM) exec -- $(PYTHON) tools/clients.py
test.browser: clients.build
	OCAML_VERSION=$(OCAML_VERSION) timeout 180 $(NODE) tools/browser.cjs
test.differential: test.node test.browser
	$(OPAM) exec -- $(PYTHON) tools/api_coverage.py
	BUILD_DIR=$(BUILD_DIR) $(OPAM) exec -- $(PYTHON) tools/traces.py compare
test.unit runtest test.properties: test.differential
test.stress:
	TRACE_COUNT=10000 $(MAKE) test.offline
bench: traces.build
	$(OPAM) exec -- $(PYTHON) tools/bench.py
test.replay:
	bash tools/offline.sh $(OPAM) exec -- $(PYTHON) tools/replay_check.py
