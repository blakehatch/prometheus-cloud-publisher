# prometheus-cloud-publisher
Script that queries the prometheus metrics backend and publishes the metrics to whatever cloud provider (GCP, AWS, exc...)'s metrics system.

### Flags for picking cloud publishers
--all
Records metrics to all three cloud services.

--aws
Activates AWS metrics.

--azure
Activates azure metrics.

--gc
Activates google cloud metrics.


### Flags for recording published subsets of metrics
--grpc

--schedulers

--stores

--workers

--global

If no flags are present all metrics available will be recorded.

### Usage
Examples:
```sh
python3 src/cloud_publisher.py --aws --global
```
Will record all global metrics to AWS.

```sh
python3 src/cloud_publisher.py --all --schedulers
```
Will record scheduler metrics to all cloud providers.

### Unit Tests
In order to run unit tests use the following command:
```sh
python3 ./tests/test_unit_cloud_publisher.py
```

### Configuration
Add/Modify metrics and categories in the config.json file 

```sh
{
    // ... existing metrics and categories
    new_metric_category: [
        "metric_1", "metric_2", ...
    ], 
}
```
