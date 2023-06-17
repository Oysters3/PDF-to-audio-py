# Testing

pypdf uses [`pytest`](https://docs.pytest.org/en/7.1.x/) for testing.

## De-selecting groups of tests

pypdf makes use of the following pytest markers:

* `slow`: Tests that require more than 5 seconds
* `samples`: Tests that require the [the `sample-files` git submodule](https://github.com/py-pdf/sample-files) to be initialized. As of October 2022, this is about 25 MB.
* `enable_socket`: Tests that download PDF documents. They are stored locally and thus only need to be downloaded once. As of October 2022, this is about 200 MB.

You can disable them by `pytest -m "not enable_socket"` or `pytest -m "not samples"`.
You can even disable all of them: `pytest -m "not enable_socket" -m "not samples" -m "not slow"`.

Please note that this reduces test coverage. The CI will always test all files.

## Creating a Coverage Report

If you want to get a coverage report that considers the Python version specific
code, you can run [`tox`](https://tox.wiki/en/latest/).

As a prerequisite, we recommend using [`pyenv`](https://github.com/pyenv/pyenv)
so that you can install the different Python versions:

```
pyenv install pypy3.8-7.3.7
pyenv install 3.6.15
pyenv install 3.7.12
pyenv install 3.8.12
pyenv install 3.9.10
pyenv install 3.10.2
```

Then you can execute `tox` which will create a coverage report in HTML form
in the end. The execution takes about 30 minutes.


## Docstrings in Unit tests

The first line of a docstring in a unit test should be written in a way that
you could prefix it with "This tests ensures that ...", e.g.

* Invalid XML in xmp_metadata is gracefully handled.
* The identity is returning its input.
* xmp_modify_date is extracted correctly.

This way, plugins like [`pytest-testdox`](https://pypi.org/project/pytest-testdox/)
can generate really nice output when the tests are running. This looks similar
to the output of [mocha.js](https://mochajs.org/).

If the test is a regression test, write

> This test is a regression test for issue #1234

If the regression test is just one parameter of other tests, then add it as
a comment for that parameter.
