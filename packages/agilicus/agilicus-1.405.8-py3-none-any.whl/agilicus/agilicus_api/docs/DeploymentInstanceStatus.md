# DeploymentInstanceStatus

Deployment instance status 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | The current status of the deployment instance. | [optional] 
**last_failed_message** | **str** | the last failed message | [optional] 
**resources** | [**[DeploymentInstanceResource]**](DeploymentInstanceResource.md) | A list of all resources associated with this deployment instance.  | [optional] 
**deployment** | [**Deployment**](Deployment.md) |  | [optional] 
**resolved_schema** | [**[DeploymentResolvedSchema]**](DeploymentResolvedSchema.md) | A list of resolved schema templates  | [optional] 
**missing_parameters** | [**[DeploymentParameter]**](DeploymentParameter.md) | A list of missing parameters that caused the instance to fail and are required | [optional] 
**outputs** | [**[DeploymentOutput]**](DeploymentOutput.md) | A list of outputs for this deployment | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


