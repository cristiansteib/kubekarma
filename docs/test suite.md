# TestSuite

## Test Suite status

A specific instance of Test Suite (like: [`NetworkTestSuite`](../chart/crds/NetworkTestSuite.yaml)) can be in the following phases:


|   phase   | description                                                     | 
|:---------:|-----------------------------------------------------------------|
|  Pending  | The CRD is waiting to be handled by the controller operator     |
|  Created  | The test suite was scheduled for execution                      |
|  Failed   | The test suite has incorrect definition or there is some error. |
| Suspended | The test suite has been suspended.                              |


The whole test suite execution can be in one of the following steps

| testExecutionStatus | description                                                                                |
|:-------------------:|--------------------------------------------------------------------------------------------|
|       Pending       | Pending a response from the first execution.                                               |
|     Succeeding      | The asserts are working as expected.                                                       |
|       Failing       | The test suite has some asserts failing or there are some errors in the execution runtime. | 


The status of each test case can be in one of the following steps:

| status.testCases[*].status | description                                                                                |
|:--------------------------:|--------------------------------------------------------------------------------------------|
|           Failed           | The assertion is currently failing.                                                        |
|         Succeeded          | The assertion is working as expected.                                                      |
|       NotImplemented       | The assertion is not implemented yet.                                                      |
|           Error            | There is some error in the execution runtime. Also `testCases[*].error` will be populated. |

- `status.testCases[*].name`: The name of the test case.
- `status.testCases[*].executionTime`: The time that the test case took to execute.
- `status.testCases[*].lastExecutionTime`: The last time that the test case was executed.
- `status.testCases[*].lastSucceededTime`: The last time that the test case was executed successfully.
- `status.testCases[*].lastExecutionErrorTime`: The last time that the test case was executed successfully.

Further details could be found in the `status.testCases[*].error` field.


