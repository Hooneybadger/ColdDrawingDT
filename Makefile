PYTHONPATH := src:.
PYTHON ?= python3

.PHONY: test contracts model-verify fea-smoke demo-fast demo-fea factory-stage demo-stream fetch-pinn api

contracts:
	$(PYTHON) scripts/validate_contracts.py
	$(PYTHON) scripts/render_factory_layout.py

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

fetch-pinn:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fetch-pinn

model-verify:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli model-verify --features 0.3 0.2 0.08 0.7

fea-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli fea-smoke

demo-fast:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli demo-fast

demo-fea:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli demo-fea

factory-stage:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m cold_drawing_twin.cli factory-stage

demo-stream:
	@echo "Launch omniverse/apps/operator/cold_drawing_operator.kit on the RTX host."
	@echo "The operator client uses WebRTC. Streaming must not write Decisions."
	@test -f usd/factory/bugok_factory.usda || (echo "run make factory-stage first" && exit 1)

api:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m uvicorn --factory cold_drawing_twin.api.app:create_app --host 0.0.0.0 --port 8000
