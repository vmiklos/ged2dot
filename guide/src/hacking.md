# Development notes

## How to set up a virtual env

Create it:

```
python3.11 -m venv ged2dot-env
```

Activate it:

```
. ged2dot-env/bin/activate
```

Install requirements:

```
pip install -r requirements.txt
```

## Development cycle

A typical flow is:

```
... hack hack hack ...
make check-mypy
ged2dot --input test.ged --output test.dot && dot -Tsvg -o test.svg test.dot # test the changes
```

Once you're happy with your change:

```
make check # run all tests
... write new tests if coverage regressed ...
```

## Python debugging

To run a single test:

```
env PYTHONPATH=.:tests python3 -m unittest tests.test_ged2dot.TestMain.test_happy
```

## Maintenance

Ideally CI checks everything before a commit hits master, but here are a few
things which are not part of CI:

- Run `tools/requirements.py` once a month and make sure Python dependencies are reasonably up to date.
