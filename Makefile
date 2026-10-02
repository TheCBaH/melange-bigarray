OPAM ?= opam
DUNE ?= dune
NODE ?= node
PYTHON ?= python3
.PHONY: format deps build api.check ci clean tree.check oracle.prepare test.install
build:
	$(OPAM) exec -- $(DUNE) build @all
api.check: build
	$(NODE) _build/default/spike/output/spike/probe.js
	$(OPAM) exec -- $(PYTHON) tools/spike.py
test.install: api.check
oracle.prepare:
	$(PYTHON) tools/prepare_oracles.py
format:
	$(OPAM) exec -- ocamlformat --check --impl lib/melange_bigarray.ml.in
	$(OPAM) exec -- ocamlformat --check --intf lib/melange_bigarray.mli.in
	$(OPAM) exec -- $(DUNE) build @fmt
deps:
	$(OPAM) exec -- $(PYTHON) tools/check_tools.py
	npm ci
	npx playwright install --with-deps chromium --only-shell
ci: oracle.prepare api.check format tree.check
clean:
	$(OPAM) exec -- $(DUNE) clean
	rm -rf .cache/spike
tree.check:
	git diff --exit-code
	test -z "$$(git status --porcelain)"
