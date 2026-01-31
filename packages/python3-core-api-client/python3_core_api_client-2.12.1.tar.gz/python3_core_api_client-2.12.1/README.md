 # python3-core-api-client

Python client for Core API.

This client was built for and tested on the **1.263.0** version of the API.

## Support

This client is officially supported by Cyberfusion.

Have questions? Ask your support questions on the [platform](https://platform.cyberfusion.io/). No access to the platform? Send an email to [support@cyberfusion.io](mailto:support@cyberfusion.io). **GitHub issues are not actively monitored.**

# Install

This client can be used in any Python project and with any framework.

This client requires Python 3.13 or higher.

## PyPI

Run the following command to install the package from PyPI:

    pip3 install python3-core-api-client

## Debian

Run the following commands to build a Debian package:

    mk-build-deps -i -t 'apt -o Debug::pkgProblemResolver=yes --no-install-recommends -y'
    dpkg-buildpackage -us -uc

# Usage

## API documentation

Refer to the [API documentation](https://core-api.cyberfusion.io/) for information about API requests.

**Enums and Models** are **auto-generated** based on the OpenAPI spec - so the client is completely in line with the Core API. **Requests and Resources** are not auto-generated.

## Getting started

Initialise the `CoreApiConnector` with your username and password **or** API key.

The connector takes care of authentication, and offers several resources (e.g. `virtual_hosts`) and endpoints (e.g. `list_virtual_hosts`).

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

# Using username and password

connector = CoreApiConnector(
    username='username', password='password'
)

# Or using API key

connector = CoreApiConnector(
    api_key='api_key'
)

response = connector.virtual_hosts.list_virtual_hosts()

virtual_hosts = response.dto
```

By default, no objects are included. You can manually specify which objects you wish to include, for example:

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

connector = CoreApiConnector(
    username='username', password='password'
)

response = connector.virtual_hosts.read_virtual_host(includes=["unix_user,cluster.region"])

virtual_host = response.dto

unix_user = virtual_host.includes.unix_user
region = virtual_host.includes.cluster.includes.region
```

## Authentication

This client takes care of authentication.

If authentication using username and password fails, `cyberfusion.CoreApiClient.exceptions.AuthenticationException` is thrown.

If authentication using API key fails, the regular `CallException` exception is raised.

Don't have an API user? Contact Cyberfusion.

## Requests

The client uses a fluent interface to build requests.

- Start with the connector
- Go to the desired resource
- Call the desired endpoint

Code example:

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

from cyberfusion.CoreApiClient.models import MailDomainCreateRequest

connector = CoreApiConnector(
    username='username', password='password'
)

connector.mail_domains.create_mail_domain(
    MailDomainCreateRequest(
        domain='cyberfusion.io',
        unix_user_id=1,
        is_local=True,
        catch_all_forward_email_addresses=[],
    )
)
```

Models are validated before sending the request (using [Pydantic](https://docs.pydantic.dev/latest/)). If invalid data is provided, `pydantic.ValidationError` is thrown.

Code example:

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

from cyberfusion.CoreApiClient.models import MailAliasCreateRequest

connector = CoreApiConnector(
    username='username', password='password'
)

connector.mail_aliases.create_mail_alias(
    MailAliasCreateRequest(
        local_part='&^@$#^&@$#^&',
        mail_domain_id=1,
    )
)
# throw pydantic.ValidationError
```

The exception has an `errors()` method to get all validation errors.

Code example:

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

from cyberfusion.CoreApiClient.models import MailAliasCreateRequest

import pydantic

connector = CoreApiConnector(
    username='username', password='password'
)

try:
    connector.mail_aliases.create_mail_alias(
        MailAliasCreateRequest(
            local_part='&^@$#^&@$#^&',
            mail_domain_id=1,
        )
    )
except pydantic.ValidationError as e:
    errors = e.errors()

for error in errors:
    print(error['loc'])
    print(error['msg'])
    print(error['type'])
```

## Responses

### Get model from response

Calling an endpoint returns a response model (`DtoResponse`) containing the resource model (in the `dto` variable).

Code example:

```python
from cyberfusion.CoreApiClient.connector import CoreApiConnector

from cyberfusion.CoreApiClient.models import MailDomainCreateRequest

connector = CoreApiConnector(
    username='username', password='password'
)

response = connector.mail_domains.create_mail_domain(
    MailDomainCreateRequest(
        domain='cyberfusion.io',
        unix_user_id=1,
        is_local=True,
        catch_all_forward_email_addresses=[],
    )
)

mail_domain_resource = response.dto
# mail_domain_resource is a model representing the API resource
```

### Get other information from response

The response model also contains the response status code, body (in both string and JSON format), headers and a failed boolean.

Need even more? Access the raw response object in `requests_response`.

Code example:

```python
import requests_cache

from cyberfusion.CoreApiClient.connector import CoreApiConnector

from cyberfusion.CoreApiClient.models import MailAliasCreateRequest

connector = CoreApiConnector(
    username='username', password='password', requests_session=requests_cache.CachedSession()
)

response = connector.mail_aliases.create_mail_alias(
    MailAliasCreateRequest(
        local_part='&^@$#^&@$#^&',
        mail_domain_id=1,
    )
)

if response.failed:
    print("HTTP request failed with status code: ", response.status_code)

if response.requests_response.from_cache:
    print("Cached response body: ", response.body)

    json_body = response.json
```

### Throw exception on failure

If a request returns an unexpected HTTP status code, `cyberfusion.CoreApiClient.exceptions.CallException` is thrown.

The exception includes the response, and the HTTP status code.

## Enums

Some properties only accept certain values (enums).

Find these values in `cyberfusion.CoreApiClient.models`.

## Deep dive

### Custom `requests` session

Want to provide your own `requests` session? Pass it to the connector:

```python
import requests

from cyberfusion.CoreApiClient.connector import CoreApiConnector

connector = CoreApiConnector(
    ..., requests_session=requests.Session()
)
```

Don't pass a custom session? A default one is created, with retries enabled.

### Manual requests

Don't want to use the full SDK, but easily send requests and retrieve responses from the Core API?

Initialise the connector as usual, and call `send`:

```python
import requests

from cyberfusion.CoreApiClient.connector import CoreApiConnector

connector = CoreApiConnector(...)

response = connector.send(method='GET', path='/foobar', data={}, query_parameters={})
```

To raise `cyberfusion.CoreApiClient.exceptions.CallException` in case of an unexpected HTTP status code, use `send_or_fail` instead of `send`. It takes the same parameters.

### Generating models

Auto-generate models as follows:

    datamodel-codegen --input-file-type openapi --url http://127.0.0.1:22190/openapi.json --output temp_models.py --target-python-version 3.13 --base-class cyberfusion.CoreApiClient.models.BaseCoreApiModel

This adds models to `temp_models.py`. Merge it with `models.py`.

To not use a local Core API instance, replace `--url` by `--input`. Pass the path to the OpenAPI spec (JSON).

# Test strategy

Tests use a mock server, [Stoplight Prism](https://stoplight.io/open-source/prism).

Prism checks requests' syntactic validity - based on the OpenAPI spec.

Therefore, the resources' test suites solely call methods without asserting specifics: nearly all possible issues - invalid requests, mismatch between resource models and endpoint, etc. - are already caught by having a validating mock server.
