# Prepare python environment
python -m pip install --requirement requirements.txt

# Prepare MongoDB Development DB
./.devcontainer/installMongoDB.sh
./.devcontainer/startMongoDB.sh