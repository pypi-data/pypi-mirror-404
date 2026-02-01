# ForwarderSummaryStats

Stats summarising the operations performed by a service forwarder. The meaning of the Note that 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bytes_received** | **int** | The number of bytes received clients | 
**bytes_sent** | **int** | The number of bytes sent to clients | 
**flows_current** | **int** | The number of flows currently running | 
**flows_total** | **int** | The number of flows established or failed | 
**flows_successful** | **int** | The number of flows which succesfully established | 
**flows_failed** | **int** | The number of flows which failed to establish | 
**datagrams_received** | **int** | The number of datagrams received from the server | 
**datagrams_sent** | **int** | The number of datagrams sent to the server | 
**datagrams_dropped** | **int** | The number of datagrams dropped (e.g. due to mtu or congestion). | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


