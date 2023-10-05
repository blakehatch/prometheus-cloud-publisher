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


### Flags for recording publishing subsets of metrics
--grpc

--schedulers

--stores

--workers

--global

If no flags are present all metrics available will be published.

### Usage
Examples:
```sh
python3 src/__main__.py --aws --global
```
Will publish all global metrics to AWS

```sh
python3 src/__main__.py --all --schedulers
```
Will publish scheduler metrics to all cloud providers.


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
