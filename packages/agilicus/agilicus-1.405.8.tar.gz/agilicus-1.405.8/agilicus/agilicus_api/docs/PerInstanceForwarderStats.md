# PerInstanceForwarderStats

Upstream statistics for a given ServiceForwarder as seen by an AgentConnector instance. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**connector_instance_id** | **str** | Unique identifier | 
**forwarder_type** | **str** | The type of forwarder:  - service: a normal service forwarder, tied to an ApplicationService  - internal: an internal network forwarder, pointing at an internal-network hosted by Agilicus    in this case, the forwarder_id represents the purpose/protocol of the forwarder (e.g. ntp)  | 
**forwarder_stats** | [**ForwarderCommonStats**](ForwarderCommonStats.md) |  | 
**forwarder_id** | **str** | Unique identifier | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


