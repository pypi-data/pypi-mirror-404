# UpstreamBufferControl

Configuration properties for upstream buffer control. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**upstream_buffer_tuning** | **bool** | Enables upstream buffer tunning by monitoring socket buffer size and overall latency. When enabled, this will help reduce overall memory consuption by reducing the amount of memory that could be consumed by large socket buffers.  | [optional] 
**min_latency** | **int** | When upstream_buffer_tuning is enabled, this sets the lowest latency before the control  algorithm will determine to increase the size of the buffer. Unless set, this value will be predefined by the system.  | [optional] 
**max_latency** | **int** | When upstream_buffer_tuning is enabled, this sets the highest latency before the control  algorithm will determine to decreases the size of the buffer. Unless set, this value will be predefined by the system.  | [optional] 
**rmem_max** | **int** | Set the size of the rmem_max (the receive buffer size for new upstream connections) Unless set, this value will be predefined by the system.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


