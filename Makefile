PYTHONPATH := src:.
PYTHON ?= python3

.PHONY: test test-pinn contracts model-verify fea-smoke fea-validate fea-requeue fea-reclaim demo-fast demo-fea demo-system seed-opcua factory-stage demo-stream fetch-pinn api

contracts:
	$(PYTHON) scripts/validate_contracts.py
	$(PYTHON) scripts/render_factory_layout.py

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q -m "not pinn_release"

test-pinn:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q -m pinn_release

fetch-pinn:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fetch-pinn

model-verify:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli model-verify --features 0.3 0.2 0.08 0.7

fea-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fea-smoke

fea-validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fea-validate --work-dir simulation/workspaces/fea-smoke

fea-requeue:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fea-requeue

fea-reclaim:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fea-reclaim

demo-fast:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli demo-fast

demo-fea:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli demo-fea

demo-system:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli demo-system

seed-opcua:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli seed-opcua

factory-stage:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli factory-stage

demo-stream:
	@echo "Launch omniverse/apps/operator/cold_drawing_operator.kit on the RTX host."
	@echo "The operator client polls the HTTP API. Streaming must not write Decisions."
	@test -f usd/factory/bugok_factory.usda || (echo "run make factory-stage first" && exit 1)

api:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m uvicorn --factory cold_drawing_twin.api.app:create_app --host 0.0.0.0 --port 8000
