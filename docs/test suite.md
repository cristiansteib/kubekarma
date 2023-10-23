# TestSuite

## Phases of Test Suite

A specific instance of Test Suite (like [`NetworkTestSuite`](../charts/kubekarma/crds/NetworkTestSuite.yaml)) can be in the following phases:


|   phase   | description                                                   | 
|:---------:|---------------------------------------------------------------|
|  Pending  | Indicates the CRD is not active or seen by the operator.      |
|  Active   | Indicates the test suite is currently active.                 |
|  Failed   | Indicates there are some errors present in the instantiation. |
| Suspended | Indicates the suspension of the test execution.               |

### Overall TestSuite result

The whole test suite execution can be in one of the following steps.
`status.testExecutionStatus`

|   Result   | description                                                                 |
|:----------:|-----------------------------------------------------------------------------|
|  Pending   | Pending a response from the first execution.                                |
| Succeeding | The asserts are working as expected.                                        |
|  Failing   | The test suite has some asserts failing or errors in the execution runtime. | 


### Individual Test Case result
The status of each test case can be in one of the following steps:

`status.testCases[*].status`

|     Result     | description                                                                                 |
|:--------------:|---------------------------------------------------------------------------------------------|
|     Failed     | The assertion is currently failing.                                                         |
|   Succeeded    | The assertion is working as expected.                                                       |
| NotImplemented | The assertion is not implemented yet.                                                       |
|     Error      | There is some error in the execution runtime. Also, `testCases[*].error` will be populated. |

- `status.testCases[*].name`: The name of the test case.
- `status.testCases[*].executionTime`: The time the test case took to execute.
- `status.testCases[*].lastExecutionTime`: The last time of test case execution.
- `status.testCases[*].lastSucceededTime`: The time of the latest success time.
- `status.testCases[*].lastExecutionErrorTime`: The time of the latest error execution.

Further details could be available in the `status.testCases[*].error` field.


## How to define a new TestSuite kind?
