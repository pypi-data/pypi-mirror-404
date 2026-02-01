conda create -n torch-kindling python=3.13 -y
conda activate torch-kindling
pip install torch --index-url https://download.pytorch.org/whl/cu130
pip install -e .
