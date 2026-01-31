# raindrop-query

Official Python SDK for the [Raindrop Query API](https://query.raindrop.ai).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/raindrop-query)](https://pypi.org/project/raindrop-query/)

<!-- Start Summary [summary] -->
## Summary

Raindrop Query API (Beta): API for querying Signals, Events, Users, and Conversations data.
<!-- End Summary [summary] -->

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
* [raindrop-query](#raindrop-query)
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Authentication](#authentication)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Server Selection](#server-selection)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)
* [Development](#development)
  * [Maturity](#maturity)
  * [Contributions](#contributions)

<!-- End Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

```bash
pip install raindrop-query
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from raindrop-query python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "raindrop-query",
# ]
# ///

from raindrop_query import RaindropQuery

sdk = RaindropQuery(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

### Example

```python
# Synchronous Example
from raindrop_query import RaindropQuery


with RaindropQuery(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:

    res = rq_client.signals.list(limit=50, order_by="-timestamp")

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from raindrop_query import RaindropQuery

async def main():

    async with RaindropQuery(
        api_key="<YOUR_BEARER_TOKEN_HERE>",
    ) as rq_client:

        res = await rq_client.signals.list_async(limit=50, order_by="-timestamp")

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

<!-- Start Authentication [security] -->
## Authentication

### Per-Client Security Schemes

This SDK supports the following security scheme globally:

| Name      | Type | Scheme      |
| --------- | ---- | ----------- |
| `api_key` | http | HTTP Bearer |

To authenticate with the API the `api_key` parameter must be set when initializing the SDK client instance. For example:
```python
from raindrop_query import RaindropQuery


with RaindropQuery(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:

    res = rq_client.signals.list(limit=50, order_by="-timestamp")

    # Handle response
    print(res)

```
<!-- End Authentication [security] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [Conversations](docs/sdks/conversations/README.md)

* [list](docs/sdks/conversations/README.md#list) - List conversations
* [get](docs/sdks/conversations/README.md#get) - Get conversation details

### [Events](docs/sdks/events/README.md)

* [list](docs/sdks/events/README.md#list) - List events
* [search](docs/sdks/events/README.md#search) - Search events (GET)
* [count](docs/sdks/events/README.md#count) - Count events
* [timeseries](docs/sdks/events/README.md#timeseries) - Get event timeseries
* [facets](docs/sdks/events/README.md#facets) - Get event facets
* [get](docs/sdks/events/README.md#get) - Get event details

### [SignalGroups](docs/sdks/signalgroups/README.md)

* [list](docs/sdks/signalgroups/README.md#list) - List all signal groups
* [get](docs/sdks/signalgroups/README.md#get) - Get signal group details
* [list_signals](docs/sdks/signalgroups/README.md#list_signals) - List signals in group

### [Signals](docs/sdks/signals/README.md)

* [list](docs/sdks/signals/README.md#list) - List all signals
* [get](docs/sdks/signals/README.md#get) - Get signal details

### [Users](docs/sdks/users/README.md)

* [list](docs/sdks/users/README.md#list) - List users
* [get](docs/sdks/users/README.md#get) - Get user details

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from raindrop_query import RaindropQuery
from raindrop_query.utils import BackoffStrategy, RetryConfig


with RaindropQuery(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:

    res = rq_client.signals.list(limit=50, order_by="-timestamp",
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    # Handle response
    print(res)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from raindrop_query import RaindropQuery
from raindrop_query.utils import BackoffStrategy, RetryConfig


with RaindropQuery(
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:

    res = rq_client.signals.list(limit=50, order_by="-timestamp")

    # Handle response
    print(res)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`RaindropQueryError`](./src/raindrop_query/errors/raindropqueryerror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](#error-classes). |

### Example
```python
from raindrop_query import RaindropQuery, errors


with RaindropQuery(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:
    res = None
    try:

        res = rq_client.signals.list(limit=50, order_by="-timestamp")

        # Handle response
        print(res)


    except errors.RaindropQueryError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.SignalsListUnauthorizedError):
            print(e.data.error)  # models.SignalsListError
```

### Error Classes
**Primary error:**
* [`RaindropQueryError`](./src/raindrop_query/errors/raindropqueryerror.py): The base class for HTTP error responses.

<details><summary>Less common errors (18)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`RaindropQueryError`](./src/raindrop_query/errors/raindropqueryerror.py)**:
* [`EventsSearchBadRequestError`](./src/raindrop_query/errors/eventssearchbadrequesterror.py): Invalid request (e.g., date range exceeds maximum). Status code `400`. Applicable to 1 of 15 methods.*
* [`EventsFacetsBadRequestError`](./src/raindrop_query/errors/eventsfacetsbadrequesterror.py): Invalid field name. Status code `400`. Applicable to 1 of 15 methods.*
* [`SignalsListUnauthorizedError`](./src/raindrop_query/errors/signalslistunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 15 methods.*
* [`SignalGroupsListUnauthorizedError`](./src/raindrop_query/errors/signalgroupslistunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 15 methods.*
* [`EventsListUnauthorizedError`](./src/raindrop_query/errors/eventslistunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 15 methods.*
* [`UsersListUnauthorizedError`](./src/raindrop_query/errors/userslistunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 15 methods.*
* [`ConversationsListUnauthorizedError`](./src/raindrop_query/errors/conversationslistunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 15 methods.*
* [`SignalsGetNotFoundError`](./src/raindrop_query/errors/signalsgetnotfounderror.py): Signal not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`SignalGroupsGetNotFoundError`](./src/raindrop_query/errors/signalgroupsgetnotfounderror.py): Signal group not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`SignalGroupsListSignalsNotFoundError`](./src/raindrop_query/errors/signalgroupslistsignalsnotfounderror.py): Signal group not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`EventsGetNotFoundError`](./src/raindrop_query/errors/eventsgetnotfounderror.py): Event not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`UsersGetNotFoundError`](./src/raindrop_query/errors/usersgetnotfounderror.py): User not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`ConversationsGetNotFoundError`](./src/raindrop_query/errors/conversationsgetnotfounderror.py): Conversation not found. Status code `404`. Applicable to 1 of 15 methods.*
* [`ResponseValidationError`](./src/raindrop_query/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>

\* Check [the method documentation](#available-resources-and-operations) to see if the error is applicable.
<!-- End Error Handling [errors] -->

<!-- Start Server Selection [server] -->
## Server Selection

### Override Server URL Per-Client

The default server can be overridden globally by passing a URL to the `server_url: str` optional parameter when initializing the SDK client instance. For example:
```python
from raindrop_query import RaindropQuery


with RaindropQuery(
    server_url="https://query.raindrop.ai",
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as rq_client:

    res = rq_client.signals.list(limit=50, order_by="-timestamp")

    # Handle response
    print(res)

```
<!-- End Server Selection [server] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from raindrop_query import RaindropQuery
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = RaindropQuery(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from raindrop_query import RaindropQuery
from raindrop_query.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = RaindropQuery(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `RaindropQuery` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from raindrop_query import RaindropQuery
def main():

    with RaindropQuery(
        api_key="<YOUR_BEARER_TOKEN_HERE>",
    ) as rq_client:
        # Rest of application here...


# Or when using async:
async def amain():

    async with RaindropQuery(
        api_key="<YOUR_BEARER_TOKEN_HERE>",
    ) as rq_client:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from raindrop_query import RaindropQuery
import logging

logging.basicConfig(level=logging.DEBUG)
s = RaindropQuery(debug_logger=logging.getLogger("raindrop_query"))
```
<!-- End Debugging [debug] -->

<!-- Placeholder for Future Speakeasy SDK Sections -->

# Development

## Maturity

This SDK is in beta. We recommend pinning to a specific version.

## Support

For questions or issues, contact support@raindrop.ai
