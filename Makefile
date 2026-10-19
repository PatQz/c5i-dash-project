.DEFAULT_GOAL := help

# Cargar variables de entorno desde .env si existe
ifneq (,$(wildcard .env))
include .env
export
endif

# Usar el entorno virtual si existe, si no, el python del sistema
ifeq ($(OS),Windows_NT)
PYTHON := $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,python)
else
PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
endif

.PHONY: help install descargar cargar etl db up down

help: ## Muestra esta ayuda
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Instala las dependencias de Python
	$(PYTHON) -m pip install -r requirements.txt

descargar: ## Descarga los datos del portal de Sonora a datos/
	$(PYTHON) etl/descargar_datos.py

cargar: ## Carga los datos de datos/ a PostgreSQL
	$(PYTHON) etl/carga_datos.py

etl: ## Pipeline completo: descarga lo que falte y carga los datos
	$(PYTHON) etl/pipeline.py

db: ## Levanta solo el contenedor de PostgreSQL
	docker compose up -d db

up: ## Levanta los contenedores con Docker Compose
	docker compose up --build -d

down: ## Detiene los contenedores
	docker compose down
