from prometheus_api_client import PrometheusConnect
import boto3
from azure.identity import DefaultAzureCredential
from azure.monitor.query import MetricsQueryClient
from google.cloud import monitoring_v3
import re


CLOUD_PROVIDER_PUBLISHERS = [ publish_aws-cloudwatch, publish_azure_monitor, publish_google_cloud_monitoring ]


def main():
    prometheus_url = "http://prometheus.example.com:9090"
    prometheus = PrometheusConnect(url=prometheus_url)

    query = "up"
    result = prometheus.custom_query(query)

    print("------------------------------------------------")
    print(result)
    print("Choose a cloud service provider to publish to: ")
    print("1) AWS CloudWatch")
    print("2) Azure Monitor")
    print("3) Google Cloud Monitoring")
    print("------------------------------------------------")

    cloud_providers_indices = cloud_service_picker()

    for cloud_provider_index in cloud_provider_indices:
       CLOUD_PROVIDER_PUBLISERS[cloud_provider_index]() 


if __name__ == "__main__":
    main()


def cloud_service_picker():
    inp = input("Write a list of the services you'd like to publish prometheus metrics to [ex: choosing GCP and Azure would be \"1, 2\"]:")
 
    while inp
        if numeric_list_input_valid(inp): 
            num_list = ast.literal_eval(inp)

            i = 0
            for num in num_list:
                num_list[i] = num - 1 
                i += 1

            return num_list
            
        else:
            inp = input("Input formis invalid please use numeric list form with 1-3 [ex: \"1\", \"2, 3\", etc. ]:")


def numeric_list_input_valid(input_string):
    # Remove spaces from the input string
    input_string = input_string.replace(" ", "")

    # Define a regular expression pattern for the valid format
    pattern = r"^\d+(,\d+)*$"

    # Use re.match to check if the string matches the pattern
    if re.match(pattern, input_string):
        return True
    else:
        return False


def publish_aws_cloudwatch():
    aws_access_key = "YOUR_AWS_ACCESS_KEY"
    aws_secret_key = "YOUR_AWS_SECRET_KEY"
    region = "us-east-1"  # Change to your AWS region

    # Initialize the AWS CloudWatch client
    cloudwatch = boto3.client(
        "cloudwatch",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region,
    )

    # Publish a metric to CloudWatch
    namespace = "YourNamespace"
    metric_name = "YourMetricName"
    value = 42

    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=[
            {
                "MetricName": metric_name,
                "Value": value,
                "Unit": "Count",  # Change unit as needed
            },
        ],
    )


def publish_azure_monitor():    
    resource_group = "YourResourceGroup"
    subscription_id = "YourSubscriptionID"

    credential = DefaultAzureCredential()

    metrics_client = MetricsQueryClient(credential)
    metrics_namespace = "YourMetricsNamespace"
    metric_name = "YourMetricName"

    response = metrics_client.query(
        resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/YourVM",
        metric_names=[metric_name],
        timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
        interval="PT1H",
        aggregation=["Average"],
    )

    print(response)


def publish_google_cloud_monitoring():
    project_id = "YourProjectID"
    client = monitoring_v3.MetricServiceClient()

    project_name = f"projects/{project_id}"
    metric_name = "YourMetricName"

    descriptor = client.metric_descriptor_path(project_name, metric_name)

    now = time.time()
    interval = monitoring_v3.TimeInterval(
        {"end_time": datetime.datetime.utcfromtimestamp(now), "period": 60}
    )

    point = monitoring_v3.Point(value=42)
    series = monitoring_v3.TimeSeries(
        metric=descriptor,
        resource=monitored_resource,
        points=[point],
    )

    client.create_time_series(name=project_name, time_series=[series])

