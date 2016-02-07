virtualenv --quiet .
source bin/activate
pip install --quiet -r config/requirements.txt
python app.py debug
