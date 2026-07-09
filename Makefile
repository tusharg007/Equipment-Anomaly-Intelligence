PYTHON ?= python
PIP ?= $(PYTHON) -m pip
DBT ?= dbt
PROFILE ?= dbt_mfg
PROFILES_DIR ?= dbt_mfg

setup:
	$(PIP) install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

generate-data:
	$(PYTHON) src/generate_synthetic_data.py

load-db:
	$(PYTHON) src/load_to_postgres.py

dbt-run:
	$(DBT) run --project-dir dbt_mfg --profiles-dir $(PROFILES_DIR) --profile $(PROFILE)

train:
	$(PYTHON) src/train_defect_model.py

anomalies:
	$(PYTHON) src/detect_anomalies.py

risk:
	$(PYTHON) src/downtime_risk_scoring.py

api:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest tests -q

smoke-test:
	$(PYTHON) src/smoke_test.py

all: generate-data train anomalies risk
