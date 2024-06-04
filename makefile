install:
  pip install -r requirements.txt
  npm install

test:
  tox

lint:
  pylint my_project/
  eslint src/
