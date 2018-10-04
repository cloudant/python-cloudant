# Contributing

## Issues

Please [read these guidelines](http://ibm.biz/cdt-issue-guide) before opening an issue.
If you still need to open an issue then we ask that you complete the template as
fully as possible.

## Pull requests

We welcome pull requests, but ask contributors to keep in mind the following:

* Only PRs with the template completed will be accepted
* We will not accept PRs for user specific functionality

### Developer Certificate of Origin

In order for us to accept pull-requests, the contributor must sign-off a
[Developer Certificate of Origin (DCO)](DCO1.1.txt). This clarifies the
intellectual property license granted with any contribution. It is for your
protection as a Contributor as well as the protection of IBM and its customers;
it does not change your rights to use your own Contributions for any other purpose.

Please read the agreement and acknowledge it by ticking the appropriate box in the PR
 text, for example:

- [x] Tick to sign-off your agreement to the Developer Certificate of Origin (DCO) 1.1

## General information

Python-Cloudant Client Library is written in Python.

## Requirements

- Python
- pip

It is recommended to use a [virtual environment](https://virtualenv.pypa.io/en/latest) during development. The
python-cloudant dependencies can be installed via the `requirements.txt` file using pip.

For example to create a virtualenv and install requirements:

```sh
virtualenv .
./bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt
```

## Testing

The tests need an Apache CouchDB or Cloudant service to run against.

The tests create databases in your CouchDB instance, these are `db-<uuid4()>`.
They also create and delete documents in the `_replicator` database.

The tests are run with the `nosetests` runner. In this example the `ADMIN_PARTY` environment variable is used to tell
 the tests not to use any authentication. See below for the full set of variables that can be used.

```sh
$ ADMIN_PARTY=true nosetests -w ./tests/unit
```

There are several environment variables which affect
test behaviour:

- `RUN_CLOUDANT_TESTS`: set this to run the tests that use Cloudant-specific features. If
  you set this, you must set one of the following combinations of other variables:
    - `DB_URL`, `DB_USER` and `DB_PASSWORD`.
    - `CLOUDANT_ACCOUNT`, `DB_USER` and `DB_PASSWORD`.
    - If you set both `DB_URL` and `CLOUDANT_ACCOUNT`, `DB_URL` is used as the
      URL to make requests to and `CLOUDANT_ACCOUNT` is inserted into the `X-Cloudant-User`
      header.
- Without `RUN_CLOUDANT_TESTS`, the following environment variables have an effect:
    - Set `DB_URL` to set the root URL of the CouchDB/Cloudant instance. It defaults
      to `http://localhost:5984`.
    - Set `ADMIN_PARTY` to `true` to not use any authentication details.
    - Without `ADMIN_PARTY`, set `DB_USER` and `DB_PASSWORD` to use those
      credentials to access the database.
    - Without `ADMIN_PARTY` and `DB_USER`, the tests assume CouchDB is in
      admin party mode, but create a user via `_config` to run tests as.
      This user is deleted at the end of the test run, but beware it'll
      break other applications using the CouchDB instance that rely on
      admin party mode being in effect while the tests are running.

### Test attributes

Database tests also have node attributes. Currently there are these attributes:
`db` - `cloudant` and/or `couch`
`couchapi` - Apache CouchDB major version number (i.e. API level) e.g. `2`

Example to run database tests that require CouchDB version 1 API and no Cloudant features:
`nosetests -A 'db and ((db is "couch" or "couch" in db) and (not couchapi or couchapi <=1))' -w ./tests/unit`
