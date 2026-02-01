# agilicus_api.DeploymentsApi

All URIs are relative to *https://api.agilicus.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_deployment**](DeploymentsApi.md#create_deployment) | **POST** /v1/deployments | Add a Deployment
[**create_deployment_instance**](DeploymentsApi.md#create_deployment_instance) | **POST** /v1/deployment_instances | Add a DeploymentInstance
[**create_deployment_template**](DeploymentsApi.md#create_deployment_template) | **POST** /v1/deployment_templates | Add a DeploymentTemplate
[**delete_deployment**](DeploymentsApi.md#delete_deployment) | **DELETE** /v1/deployments/{deployment_id} | Delete a deployment
[**delete_deployment_instance**](DeploymentsApi.md#delete_deployment_instance) | **DELETE** /v1/deployment_instances/{deployment_instance_id} | Delete a DeploymentInstance
[**delete_deployment_template**](DeploymentsApi.md#delete_deployment_template) | **DELETE** /v1/deployment_templates/{deployment_template_id} | Delete a DeploymentTemplate
[**get_deployment**](DeploymentsApi.md#get_deployment) | **GET** /v1/deployments/{deployment_id} | Get a Deployment
[**get_deployment_instance**](DeploymentsApi.md#get_deployment_instance) | **GET** /v1/deployment_instances/{deployment_instance_id} | Get a DeploymentInstance
[**get_deployment_template**](DeploymentsApi.md#get_deployment_template) | **GET** /v1/deployment_templates/{deployment_template_id} | Get a DeploymentTemplate
[**list_deployment_instances**](DeploymentsApi.md#list_deployment_instances) | **GET** /v1/deployment_instances | Get all deployment instances
[**list_deployment_templates**](DeploymentsApi.md#list_deployment_templates) | **GET** /v1/deployment_templates | Get all deployment templates
[**list_deployments**](DeploymentsApi.md#list_deployments) | **GET** /v1/deployments | Get all deployments
[**update_deployment**](DeploymentsApi.md#update_deployment) | **PUT** /v1/deployments/{deployment_id} | Update a Deployment
[**update_deployment_instance**](DeploymentsApi.md#update_deployment_instance) | **PUT** /v1/deployment_instances/{deployment_instance_id} | Update a DeploymentInstance
[**update_deployment_template**](DeploymentsApi.md#update_deployment_template) | **PUT** /v1/deployment_templates/{deployment_template_id} | Update a DeploymentTemplate


# **create_deployment**
> Deployment create_deployment(deployment)

Add a Deployment

Create a new Deployment 

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from agilicus_api.model.deployment import Deployment
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment = Deployment(
        metadata=MetadataWithId(),
        spec=DeploymentSpec(
            org_id="123",
            name="2",
            description="description_example",
            schema={},
            schema_name="schema_name_example",
        ),
        status=DeploymentStatus(
            schema_errors=[
                "schema_errors_example",
            ],
            parameters=[
                DeploymentParameter(
                    name="name_example",
                    type=None,
                    description=None,
                    default=None,
                ),
            ],
        ),
    ) # Deployment | 

    # example passing only required values which don't have defaults set
    try:
        # Add a Deployment
        api_response = api_instance.create_deployment(deployment)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->create_deployment: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment** | [**Deployment**](Deployment.md)|  |

### Return type

[**Deployment**](Deployment.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | New Deployment created. |  -  |
**400** | The request is invalid |  -  |
**409** | Deployment already exists. The Deployment is returned.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_deployment_instance**
> DeploymentInstance create_deployment_instance(deployment_instance)

Add a DeploymentInstance

Create a new DeploymentInstance 

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_instance import DeploymentInstance
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_instance = DeploymentInstance(
        metadata=MetadataWithId(),
        spec=DeploymentInstanceSpec(
            org_id="123",
            deployment_id="123",
            name="2",
            description="description_example",
            inputs=[
                DeploymentInstanceInput(
                    name="name_example",
                    value_as_string="value_as_string_example",
                ),
            ],
        ),
        status=DeploymentInstanceStatus(
            status="create_in_progress",
            last_failed_message="last_failed_message_example",
            resources=[
                DeploymentInstanceResource(
                    id="id_example",
                    type="type_example",
                    name="name_example",
                    template_name="template_name_example",
                    shared=True,
                ),
            ],
            deployment=Deployment(
                metadata=MetadataWithId(),
                spec=DeploymentSpec(
                    org_id="123",
                    name="2",
                    description="description_example",
                    schema={},
                    schema_name="schema_name_example",
                ),
                status=DeploymentStatus(
                    schema_errors=[
                        "schema_errors_example",
                    ],
                    parameters=[
                        DeploymentParameter(
                            name="name_example",
                            type=None,
                            description=None,
                            default=None,
                        ),
                    ],
                ),
            ),
            resolved_schema=[
                DeploymentResolvedSchema(
                    name="name_example",
                    schema={},
                ),
            ],
            missing_parameters=[
                DeploymentParameter(
                    name="name_example",
                    type=None,
                    description=None,
                    default=None,
                ),
            ],
            outputs=[
                DeploymentOutput(
                    name="name_example",
                    type="type_example",
                    type_reference="type_reference_example",
                    description="description_example",
                    mandatory=True,
                    route_hint=[
                        "route_hint_example",
                    ],
                ),
            ],
        ),
    ) # DeploymentInstance | 

    # example passing only required values which don't have defaults set
    try:
        # Add a DeploymentInstance
        api_response = api_instance.create_deployment_instance(deployment_instance)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->create_deployment_instance: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_instance** | [**DeploymentInstance**](DeploymentInstance.md)|  |

### Return type

[**DeploymentInstance**](DeploymentInstance.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | New DeploymentInstance created. |  -  |
**400** | The request is invalid |  -  |
**409** | Deployment Instance already exists. The DeploymentInstance is returned.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_deployment_template**
> DeploymentTemplate create_deployment_template(deployment_template)

Add a DeploymentTemplate

Create a new DeploymentTemplate 

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_template import DeploymentTemplate
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_template = DeploymentTemplate(
        metadata=MetadataWithId(),
        spec=DeploymentTemplateSpec(
            org_id="123",
            name="6bUUG/jNSwg0_bs9ZayIMrKdgNvb6gvxmPb",
            description="description_example",
            template={},
            template_type="model",
        ),
    ) # DeploymentTemplate | 

    # example passing only required values which don't have defaults set
    try:
        # Add a DeploymentTemplate
        api_response = api_instance.create_deployment_template(deployment_template)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->create_deployment_template: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_template** | [**DeploymentTemplate**](DeploymentTemplate.md)|  |

### Return type

[**DeploymentTemplate**](DeploymentTemplate.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | New DeploymentTemplate created. |  -  |
**400** | The request is invalid |  -  |
**409** | Deployment Template already exists. The DeploymentTemplate is returned.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_deployment**
> delete_deployment(deployment_id)

Delete a deployment

Delete a Deployment

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_id = "1234" # str | deployment id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Delete a deployment
        api_instance.delete_deployment(deployment_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Delete a deployment
        api_instance.delete_deployment(deployment_id, org_id=org_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_id** | **str**| deployment id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

void (empty response body)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Deployment was deleted |  -  |
**404** | Deployment does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_deployment_instance**
> delete_deployment_instance(deployment_instance_id)

Delete a DeploymentInstance

Delete a DeploymentInstance

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_instance_id = "1234" # str | deployment instance id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Delete a DeploymentInstance
        api_instance.delete_deployment_instance(deployment_instance_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment_instance: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Delete a DeploymentInstance
        api_instance.delete_deployment_instance(deployment_instance_id, org_id=org_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment_instance: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_instance_id** | **str**| deployment instance id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

void (empty response body)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | DeploymentInstance was deleted |  -  |
**404** | DeploymentInstance does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_deployment_template**
> delete_deployment_template(deployment_template_id)

Delete a DeploymentTemplate

Delete a DeploymentTemplate

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_template_id = "1234" # str | deployment template id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Delete a DeploymentTemplate
        api_instance.delete_deployment_template(deployment_template_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment_template: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Delete a DeploymentTemplate
        api_instance.delete_deployment_template(deployment_template_id, org_id=org_id)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->delete_deployment_template: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_template_id** | **str**| deployment template id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

void (empty response body)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | DeploymentTemplate was deleted |  -  |
**404** | DeploymentTemplate does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_deployment**
> Deployment get_deployment(deployment_id)

Get a Deployment

Get a Deployment

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from agilicus_api.model.deployment import Deployment
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_id = "1234" # str | deployment id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Get a Deployment
        api_response = api_instance.get_deployment(deployment_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get a Deployment
        api_response = api_instance.get_deployment(deployment_id, org_id=org_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_id** | **str**| deployment id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

[**Deployment**](Deployment.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return a Deployment. |  -  |
**404** | Deployment does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_deployment_instance**
> DeploymentInstance get_deployment_instance(deployment_instance_id)

Get a DeploymentInstance

Get a DeploymentInstance

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_instance import DeploymentInstance
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_instance_id = "1234" # str | deployment instance id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Get a DeploymentInstance
        api_response = api_instance.get_deployment_instance(deployment_instance_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment_instance: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get a DeploymentInstance
        api_response = api_instance.get_deployment_instance(deployment_instance_id, org_id=org_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment_instance: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_instance_id** | **str**| deployment instance id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

[**DeploymentInstance**](DeploymentInstance.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return a DeploymentInstance |  -  |
**404** | DeploymentInstance does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_deployment_template**
> DeploymentTemplate get_deployment_template(deployment_template_id)

Get a DeploymentTemplate

Get a DeploymentTemplate

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_template import DeploymentTemplate
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_template_id = "1234" # str | deployment template id path
    org_id = "1234" # str | Organisation Unique identifier (optional)

    # example passing only required values which don't have defaults set
    try:
        # Get a DeploymentTemplate
        api_response = api_instance.get_deployment_template(deployment_template_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment_template: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get a DeploymentTemplate
        api_response = api_instance.get_deployment_template(deployment_template_id, org_id=org_id)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->get_deployment_template: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_template_id** | **str**| deployment template id path |
 **org_id** | **str**| Organisation Unique identifier | [optional]

### Return type

[**DeploymentTemplate**](DeploymentTemplate.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return a DeploymentTemplate |  -  |
**404** | DeploymentTemplate does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_deployment_instances**
> ListDeploymentInstances list_deployment_instances()

Get all deployment instances

Get a list DeploymentInstance objects

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.list_deployment_instances import ListDeploymentInstances
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    org_id = "1234" # str | Organisation Unique identifier (optional)
    limit = 1 # int | limit the number of rows in the response (optional) if omitted the server will use the default value of 500

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get all deployment instances
        api_response = api_instance.list_deployment_instances(org_id=org_id, limit=limit)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->list_deployment_instances: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **org_id** | **str**| Organisation Unique identifier | [optional]
 **limit** | **int**| limit the number of rows in the response | [optional] if omitted the server will use the default value of 500

### Return type

[**ListDeploymentInstances**](ListDeploymentInstances.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of DeploymentInstances |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_deployment_templates**
> ListDeploymentTemplates list_deployment_templates()

Get all deployment templates

Get a list DeploymentTemplate objects

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.list_deployment_templates import ListDeploymentTemplates
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    org_id = "1234" # str | Organisation Unique identifier (optional)
    limit = 1 # int | limit the number of rows in the response (optional) if omitted the server will use the default value of 500
    deployment_template_type = "model" # str | deployment template type query (optional)
    system_templates = True # bool | include system templates with the query (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get all deployment templates
        api_response = api_instance.list_deployment_templates(org_id=org_id, limit=limit, deployment_template_type=deployment_template_type, system_templates=system_templates)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->list_deployment_templates: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **org_id** | **str**| Organisation Unique identifier | [optional]
 **limit** | **int**| limit the number of rows in the response | [optional] if omitted the server will use the default value of 500
 **deployment_template_type** | **str**| deployment template type query | [optional]
 **system_templates** | **bool**| include system templates with the query | [optional]

### Return type

[**ListDeploymentTemplates**](ListDeploymentTemplates.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of DeploymentTemplate |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_deployments**
> ListDeployments list_deployments()

Get all deployments

Get a list Deployment objects

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.list_deployments import ListDeployments
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    org_id = "1234" # str | Organisation Unique identifier (optional)
    limit = 1 # int | limit the number of rows in the response (optional) if omitted the server will use the default value of 500

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Get all deployments
        api_response = api_instance.list_deployments(org_id=org_id, limit=limit)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->list_deployments: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **org_id** | **str**| Organisation Unique identifier | [optional]
 **limit** | **int**| limit the number of rows in the response | [optional] if omitted the server will use the default value of 500

### Return type

[**ListDeployments**](ListDeployments.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | A list of Deployments |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_deployment**
> Deployment update_deployment(deployment_id, deployment)

Update a Deployment

Update a Deployment

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.error_message import ErrorMessage
from agilicus_api.model.deployment import Deployment
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_id = "1234" # str | deployment id path
    deployment = Deployment(
        metadata=MetadataWithId(),
        spec=DeploymentSpec(
            org_id="123",
            name="2",
            description="description_example",
            schema={},
            schema_name="schema_name_example",
        ),
        status=DeploymentStatus(
            schema_errors=[
                "schema_errors_example",
            ],
            parameters=[
                DeploymentParameter(
                    name="name_example",
                    type=None,
                    description=None,
                    default=None,
                ),
            ],
        ),
    ) # Deployment | 

    # example passing only required values which don't have defaults set
    try:
        # Update a Deployment
        api_response = api_instance.update_deployment(deployment_id, deployment)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->update_deployment: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_id** | **str**| deployment id path |
 **deployment** | [**Deployment**](Deployment.md)|  |

### Return type

[**Deployment**](Deployment.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return updated Deployment |  -  |
**400** | The request is invalid |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_deployment_instance**
> DeploymentInstance update_deployment_instance(deployment_instance_id, deployment_instance)

Update a DeploymentInstance

Update a DeploymentInstance

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_instance import DeploymentInstance
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_instance_id = "1234" # str | deployment instance id path
    deployment_instance = DeploymentInstance(
        metadata=MetadataWithId(),
        spec=DeploymentInstanceSpec(
            org_id="123",
            deployment_id="123",
            name="2",
            description="description_example",
            inputs=[
                DeploymentInstanceInput(
                    name="name_example",
                    value_as_string="value_as_string_example",
                ),
            ],
        ),
        status=DeploymentInstanceStatus(
            status="create_in_progress",
            last_failed_message="last_failed_message_example",
            resources=[
                DeploymentInstanceResource(
                    id="id_example",
                    type="type_example",
                    name="name_example",
                    template_name="template_name_example",
                    shared=True,
                ),
            ],
            deployment=Deployment(
                metadata=MetadataWithId(),
                spec=DeploymentSpec(
                    org_id="123",
                    name="2",
                    description="description_example",
                    schema={},
                    schema_name="schema_name_example",
                ),
                status=DeploymentStatus(
                    schema_errors=[
                        "schema_errors_example",
                    ],
                    parameters=[
                        DeploymentParameter(
                            name="name_example",
                            type=None,
                            description=None,
                            default=None,
                        ),
                    ],
                ),
            ),
            resolved_schema=[
                DeploymentResolvedSchema(
                    name="name_example",
                    schema={},
                ),
            ],
            missing_parameters=[
                DeploymentParameter(
                    name="name_example",
                    type=None,
                    description=None,
                    default=None,
                ),
            ],
            outputs=[
                DeploymentOutput(
                    name="name_example",
                    type="type_example",
                    type_reference="type_reference_example",
                    description="description_example",
                    mandatory=True,
                    route_hint=[
                        "route_hint_example",
                    ],
                ),
            ],
        ),
    ) # DeploymentInstance | 

    # example passing only required values which don't have defaults set
    try:
        # Update a DeploymentInstance
        api_response = api_instance.update_deployment_instance(deployment_instance_id, deployment_instance)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->update_deployment_instance: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_instance_id** | **str**| deployment instance id path |
 **deployment_instance** | [**DeploymentInstance**](DeploymentInstance.md)|  |

### Return type

[**DeploymentInstance**](DeploymentInstance.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return updated DeploymentInstance |  -  |
**400** | The request is invalid |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_deployment_template**
> DeploymentTemplate update_deployment_template(deployment_template_id, deployment_template)

Update a DeploymentTemplate

Update a DeploymentTemplate

### Example

* Bearer (JWT) Authentication (token-valid):
```python
import time
import agilicus_api
from agilicus_api.api import deployments_api
from agilicus_api.model.deployment_template import DeploymentTemplate
from agilicus_api.model.error_message import ErrorMessage
from pprint import pprint
# Defining the host is optional and defaults to https://api.agilicus.com
# See configuration.py for a list of all supported configuration parameters.
configuration = agilicus_api.Configuration(
    host = "https://api.agilicus.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): token-valid
configuration = agilicus_api.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with agilicus_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = deployments_api.DeploymentsApi(api_client)
    deployment_template_id = "1234" # str | deployment template id path
    deployment_template = DeploymentTemplate(
        metadata=MetadataWithId(),
        spec=DeploymentTemplateSpec(
            org_id="123",
            name="6bUUG/jNSwg0_bs9ZayIMrKdgNvb6gvxmPb",
            description="description_example",
            template={},
            template_type="model",
        ),
    ) # DeploymentTemplate | 

    # example passing only required values which don't have defaults set
    try:
        # Update a DeploymentTemplate
        api_response = api_instance.update_deployment_template(deployment_template_id, deployment_template)
        pprint(api_response)
    except agilicus_api.ApiException as e:
        print("Exception when calling DeploymentsApi->update_deployment_template: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deployment_template_id** | **str**| deployment template id path |
 **deployment_template** | [**DeploymentTemplate**](DeploymentTemplate.md)|  |

### Return type

[**DeploymentTemplate**](DeploymentTemplate.md)

### Authorization

[token-valid](../README.md#token-valid)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Return updated DeploymentTemplate |  -  |
**400** | The request is invalid |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

