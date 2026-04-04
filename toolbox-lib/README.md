# Toolbox Library

## Tests

### Tests which make real network requests

Some tests send actual requests over the network to real APIs. They are marked with
`@pytest.mark.network`. These network tests are disabled by default because they require
credentials, can be slow and flaky, and may cost real money.

If you want to run them, make sure your `.env` file is populated with the necessary
credentials. Then run

```bash
uv run --env-file=.env pytest --markers network
```

pytest's `--stepwise` flag is helpful when iterating since it skips previously passing
tests.
