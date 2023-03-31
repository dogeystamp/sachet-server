# sachet

sachet is a small file share server.

## development

To start sachet in development mode:

Clone the repo.

```
git clone https://github.com/dogeystamp/sachet
cd sachet
```

Create a venv with required dependencies:

```
python -m venv venv
source venv/bin/activate
python -m pip3 install -r requirements.txt
```

Start Flask in development mode:

```
flask --debug --app sachet.server run
```

### tests

Tests are available with the following command:

```
pytest --cov --cov-report term-missing
```

### linting

Please use the linter before submitting code.

```
black .
```
