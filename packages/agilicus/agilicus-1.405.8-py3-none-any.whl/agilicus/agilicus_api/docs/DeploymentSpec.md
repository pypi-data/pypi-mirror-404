# DeploymentSpec

Deployment specification 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**org_id** | **str** | Unique identifier | 
**name** | **str** | A name used to unqiuely identify this deployment.  | 
**description** | **str** | A description for this deployment  | [optional] 
**schema** | **{str: (bool, date, datetime, dict, float, int, list, str, none_type)}** |  | [optional] 
**schema_name** | **str** | Lookup a schema by name (in the deployment schemas collection). schema and schema_name can be used together, as schema_name will update the schema with the appropriate includes primitive.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


