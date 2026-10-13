.PHONY: test demo lint real cfd-convergence fea-convergence docker clean

test:
	pytest -q

demo:
	python -m fsi.cli demo --config config/baseline.yaml --out results/reference

lint:
	ruff check src tests scripts

real:
	bash scripts/run_real_pipeline.sh

cfd-convergence:
	python scripts/run_cfd_convergence.py --config config/baseline.yaml

fea-convergence:
	python scripts/run_fea_convergence.py --surface results/real/cfd_surface.csv --config config/baseline.yaml

docker:
	docker build -t openfoam-calculix-fsi-test .
	docker run --rm openfoam-calculix-fsi-test

clean:
	rm -rf .pytest_cache .ruff_cache build dist results/real results/cfd_convergence results/fea_convergence
