VENV_PYTHON    = venv/bin/python
SYSTEM_PYTHON  = $(or $(shell which python3), $(shell which python))
PYTHON         = $(or $(wildcard $(VENV_PYTHON)), $(SYSTEM_PYTHON))

serve: 
	$(PYTHON) -m streamlit run streamlit_app.py

clean-build:
	rm -rf build/

clean-python:
	rm -rf autoppa/__pycache__