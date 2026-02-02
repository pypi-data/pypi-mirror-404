# img-src

Developer-friendly & type-safe Python SDK specifically catered to leverage *img-src* API.

[![License: MIT](https://img.shields.io/badge/LICENSE_//_MIT-3b5bdb?style=for-the-badge&labelColor=eff6ff)](https://opensource.org/licenses/MIT)

<br /><br />

<!-- Start Summary [summary] -->
## Summary

img-src API: Image processing and delivery API.

A serverless image processing and delivery API built on Cloudflare Workers with parameter-driven image transformation and on-demand transcoding.

## Features

- **Image Upload**: Store original images in R2 with SHA256-based deduplication
- **On-Demand Transformation**: Resize, crop, and convert images via URL parameters
- **Format Conversion**: WebP, AVIF, JPEG, PNG output formats
- **Path Organization**: Organize images into folders with multiple paths per image
- **CDN Caching**: Automatic edge caching for transformed images

## Authentication

Authenticate using API Keys with `imgsrc_` prefix. Create your API key at https://img-src.io/settings

## Rate Limiting

- **Free Plan**: 100 requests/minute
- **Pro Plan**: 500 requests/minute

Rate limit headers are included in all responses.
<!-- End Summary [summary] -->

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
* [img-src](#img-src)
  * [Features](#features)
  * [Authentication](#authentication)
  * [Rate Limiting](#rate-limiting)
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Authentication](#authentication-1)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [Pagination](#pagination)
  * [File uploads](#file-uploads)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Server Selection](#server-selection)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)

<!-- End Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

/docs/github-setup#step-by-step-guide).

> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add img-src
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install img-src
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add img-src
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from img-src python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "img-src",
# ]
# ///

from img_src import Imgsrc

sdk = Imgsrc(
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

### Upload and Transform Images

```python
import os
from img_src import Imgsrc

# Create API key at https://img-src.io/settings
client = Imgsrc(bearer_auth=os.environ["IMGSRC_API_KEY"])

# Upload an image
with open("photo.jpg", "rb") as f:
    uploaded = client.images.upload_image(file=f, target_path="photos/2024")
    print(f"Uploaded: {uploaded.url}")

# Access with transformations via CDN
# https://img-src.io/i/{username}/photos/2024/photo.webp?w=800&h=600&fit=cover&q=85

# List images
images = client.images.list_images(limit=20)
print(f"Total: {images.total} images")
```
<!-- End SDK Example Usage [usage] -->

<!-- Start Authentication [security] -->
## Authentication

### Per-Client Security Schemes

This SDK supports the following security scheme globally:

| Name          | Type | Scheme      |
| ------------- | ---- | ----------- |
| `bearer_auth` | http | HTTP Bearer |

To authenticate with the API the `bearer_auth` parameter must be set when initializing the SDK client instance. For example:
```python
from img_src import Imgsrc

with Imgsrc(
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.settings.get_settings()

    assert res.settings_response is not None

    # Handle response
    print(res.settings_response)

```
<!-- End Authentication [security] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [Images](docs/sdks/images/README.md)

* [upload_image](docs/sdks/images/README.md#upload_image) - Upload image
* [list_images](docs/sdks/images/README.md#list_images) - List images
* [search_images](docs/sdks/images/README.md#search_images) - Search images
* [get_image](docs/sdks/images/README.md#get_image) - Get image metadata
* [delete_image](docs/sdks/images/README.md#delete_image) - Delete image
* [create_signed_url](docs/sdks/images/README.md#create_signed_url) - Create signed URL
* [delete_image_path](docs/sdks/images/README.md#delete_image_path) - Delete image path

### [Presets](docs/sdks/presets/README.md)

* [list_presets](docs/sdks/presets/README.md#list_presets) - List presets
* [create_preset](docs/sdks/presets/README.md#create_preset) - Create preset
* [get_preset](docs/sdks/presets/README.md#get_preset) - Get preset
* [update_preset](docs/sdks/presets/README.md#update_preset) - Update preset
* [delete_preset](docs/sdks/presets/README.md#delete_preset) - Delete preset

### [Settings](docs/sdks/settings/README.md)

* [get_settings](docs/sdks/settings/README.md#get_settings) - Get user settings
* [update_settings](docs/sdks/settings/README.md#update_settings) - Update user settings

### [Usage](docs/sdks/usage/README.md)

* [get_usage](docs/sdks/usage/README.md#get_usage) - Get usage statistics

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start Pagination [pagination] -->
## Pagination

Some of the endpoints in this SDK support pagination. To use pagination, you make your SDK calls as usual, but the
returned response object will have a `Next` method that can be called to pull down the next group of results. If the
return value of `Next` is `None`, then there are no more pages to be fetched.

Here's an example of one such pagination call:
```python
from img_src import Imgsrc

with Imgsrc(
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.images.list_images(limit=50, offset=0, path="blog/2024")

    while res is not None:
        # Handle items

        res = res.next()

```
<!-- End Pagination [pagination] -->

<!-- Start File uploads [file-upload] -->
## File uploads

Certain SDK methods accept file objects as part of a request body or multi-part request. It is possible and typically recommended to upload files as a stream rather than reading the entire contents into memory. This avoids excessive memory consumption and potentially crashing with out-of-memory errors when working with very large files. The following example demonstrates how to attach a file stream to a request.

> [!TIP]
>
> For endpoints that handle file uploads bytes arrays can also be used. However, using streams is recommended for large files.
>

```python
from img_src import Imgsrc

with Imgsrc(
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.images.upload_image(request={
        "target_path": "blog/2024",
    })

    assert res.upload_response is not None

    # Handle response
    print(res.upload_response)

```
<!-- End File uploads [file-upload] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from img_src import Imgsrc
from img_src.utils import BackoffStrategy, RetryConfig

with Imgsrc(
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.settings.get_settings(,
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    assert res.settings_response is not None

    # Handle response
    print(res.settings_response)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from img_src import Imgsrc
from img_src.utils import BackoffStrategy, RetryConfig

with Imgsrc(
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.settings.get_settings()

    assert res.settings_response is not None

    # Handle response
    print(res.settings_response)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`ImgsrcError`](./src/img_src/errors/imgsrcerror.py) is the base class for all HTTP error responses. It has the following properties:

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
from img_src import Imgsrc, errors

with Imgsrc(
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:
    res = None
    try:

        res = imgsrc.settings.get_settings()

        assert res.settings_response is not None

        # Handle response
        print(res.settings_response)

    except errors.ImgsrcError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.ErrorResponse):
            print(e.data.error)  # models.ErrorDetail
```

### Error Classes
**Primary errors:**
* [`ImgsrcError`](./src/img_src/errors/imgsrcerror.py): The base class for HTTP error responses.
  * [`ErrorResponse`](./src/img_src/errors/errorresponse.py): Generic error.

<details><summary>Less common errors (5)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.

**Inherit from [`ImgsrcError`](./src/img_src/errors/imgsrcerror.py)**:
* [`ResponseValidationError`](./src/img_src/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>
<!-- End Error Handling [errors] -->

<!-- Start Server Selection [server] -->
## Server Selection

### Override Server URL Per-Client

The default server can be overridden globally by passing a URL to the `server_url: str` optional parameter when initializing the SDK client instance. For example:
```python
from img_src import Imgsrc

with Imgsrc(
    server_url="https://api.img-src.io",
    bearer_auth="process.env["IMGSRC_API_KEY"]",
) as imgsrc:

    res = imgsrc.settings.get_settings()

    assert res.settings_response is not None

    # Handle response
    print(res.settings_response)

```
<!-- End Server Selection [server] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from img_src import Imgsrc
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = Imgsrc(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from img_src import Imgsrc
from img_src.httpclient import AsyncHttpClient
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

s = Imgsrc(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `Imgsrc` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from img_src import Imgsrc
def main():

    with Imgsrc(
        bearer_auth="process.env["IMGSRC_API_KEY"]",
    ) as imgsrc:
        # Rest of application here...

# Or when using async:
async def amain():

    async with Imgsrc(
        bearer_auth="process.env["IMGSRC_API_KEY"]",
    ) as imgsrc:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from img_src import Imgsrc
import logging

logging.basicConfig(level=logging.DEBUG)
s = Imgsrc(debug_logger=logging.getLogger("img_src"))
```
<!-- End Debugging [debug] -->
