# InternalNetworkForwarder

The detailed information used to program a connector to forward to an InternalNetwork 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**purpose** | **str** | A name identifying the protocol carried by this internal network | 
**config** | [**NetworkServiceConfig**](NetworkServiceConfig.md) |  | 
**routes** | [**[ConnectorRoute]**](ConnectorRoute.md) | The routes by which to reach this InternalNetwork. These routes can be joined with the locations to build the full tunnel URI.  | 
**locations** | [**[ApplicationServiceLocation]**](ApplicationServiceLocation.md) | The locations by which an end-user may reach the InternalNetwork  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


