# FormInjectionConfig

Configuration specific to form injection 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**username_query_selector** | **str, none_type** | A query selector to run as argument to document.querySelector(), to find the  element associated with the username input.  | [optional] 
**password_query_selector** | **str, none_type** | A query selector to run as argument to document.querySelector(), to find the  element associated with the password input.  | [optional] 
**username_next_selector** | **str** | A next selector specific for a username.  | [optional] 
**password_next_selector** | **str** | A next selector specific for a password.  | [optional] 
**submit_selector** | **str** | A submit selector for certain types of login forms  | [optional] 
**login_selector** | **str** | A login selector for certain types of login forms  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


