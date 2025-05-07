.PHONY: install install-uv install-deps

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | less && uv python install 3.13 && uv venv -p 3.13

install-deps:
	source .venv/bin/activate && uv pip install -r requirements.txt

install: install-uv install-deps