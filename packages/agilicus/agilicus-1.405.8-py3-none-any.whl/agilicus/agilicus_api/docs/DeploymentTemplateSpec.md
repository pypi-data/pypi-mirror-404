# DeploymentTemplateSpec

Deployment Template specification 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**org_id** | **str** | Unique identifier | 
**name** | **str** | A name used to unqiuely identify this template. This is used as the &#39;kind&#39; property when creating a schema and inheriting this template with the &#39;kind&#39; property keyword.  | 
**template** | **{str: (bool, date, datetime, dict, float, int, list, str, none_type)}** | Deployment Template object  | 
**template_type** | **str** | The type of template. Template types supported are: - model: the most primitive template type that is based on Agilicus OpenAPI objects          and their creation - schema: utilizes models to build up a set of objects, with composability  | 
**description** | **str** | A description for this deployment template  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


