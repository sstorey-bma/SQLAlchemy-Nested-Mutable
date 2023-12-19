sudo apt-get update
sudo apt-get install -y git-lfs
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
poetry completions bash >> ~/.bash_completion
poetry install --sync
sudo apt-get install -y dotnet-sdk-8.0
sudo cat >> $HOME/.pypirc<< EOF
[distutils]
Index-servers =
  DSAI

[DSAI]
Repository = https://pkgs.dev.azure.com/BMA-DSAI/_packaging/DSAI/pypi/upload/
EOF
