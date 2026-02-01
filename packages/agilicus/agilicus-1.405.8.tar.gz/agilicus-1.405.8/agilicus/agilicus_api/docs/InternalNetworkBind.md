# InternalNetworkBind

Configures how to expose an internal network 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bind_type** | **str** | How to bind. Possible values:   - &#x60;disabled&#x60;: this network is not exposed at all   - &#x60;local&#x60;: this network is only exposed to the local host   - &#x60;all&#x60;: this network is exposed to any device which can reach the connector  | 
**custom_bind** | [**AgentConnectorLocalBind**](AgentConnectorLocalBind.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


