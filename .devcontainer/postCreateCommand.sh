sudo apt-get update
sudo apt-get install -y git-lfs
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
poetry completions bash >> ~/.bash_completion
poetry install --sync