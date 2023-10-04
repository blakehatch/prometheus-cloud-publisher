from prometheus_api_client import PrometheusConnect
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient
from google.cloud import monitoring_v3
import re
import time
import datetime
from google.protobuf import duration_pb2
import argparse
import dotenv


def publish_aws_cloudwatch():
    aws_access_key = "YOUR_AWS_ACCESS_KEY"
    aws_secret_key = "YOUR_AWS_SECRET_KEY"
    region = "us-east-1"

    cloudwatch = boto3.client(
        "cloudwatch",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region,
    )

    namespace = "YourNamespace"
    metric_name = "YourMetricName"
    value = 42

    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=[
            {
                "MetricName": metric_name,
                "Value": value,
                "Unit": "Count",
            },
        ],
    )


def publish_azure_monitor(metrics_namespace):
    resource_group = "YourResourceGroup"
    subscription_id = "YourSubscriptionID"

    credential = DefaultAzureCredential()

    metrics_client = MonitorManagementClient(credential, subscription_id)

    metric_name = "YourMetricName"

    response = metrics_client.query(
        resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}\
        /providers/Microsoft.Compute/virtualMachines/YourVM",
        metric_names=[metric_name],
        timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
        interval="PT1H",
        aggregation=["Average"],
        namespace=metrics_namespace)

    print(response)


def publish_google_cloud_monitoring(interval):
    project_id = "YourProjectID"
    client = monitoring_v3.MetricServiceClient()

    project_name = f"projects/{project_id}"
    metric_name = "YourMetricName"

    monitored_resource = monitoring_v3.MonitoredResource(
        type="global",
        labels={"project_id": project_id},
    )

    descriptor = client.metric_descriptor_path(project_name, metric_name)

    now = time.time()
    start_time = datetime.datetime.utcfromtimestamp(now)
    end_time = start_time + datetime.timedelta(seconds=interval)

    point = monitoring_v3.Point(value=42)
    series = monitoring_v3.TimeSeries(
        metric=descriptor,
        resource=monitored_resource,
        points=[point],
    )

    client.create_time_series(
        name=project_name,
        time_series=[series],
        interval=duration_pb2.Duration(seconds=interval),
        start_time=start_time,
        end_time=end_time,
    )

# Example usage:
# publish_azure_monitor("YourMetricsNamespace")
# publish_google_cloud_monitoring(3600)  # 3600 seconds interval
# publish_to_aws_cloudwatch()


CLOUD_PROVIDER_PUBLISHERS = [publish_aws_cloudwatch,
                             publish_azure_monitor,
                             publish_google_cloud_monitoring]


def main():
    parser = argparse.ArgumentParser(
        description='Publish Prometheus metrics to cloud services.')
    parser.add_argument('--all', action='store_true',
                        help='Records metrics to all three cloud services')
    parser.add_argument('--aws', action='store_true',
                        help='Activates AWS metrics')
    parser.add_argument('--azure', action='store_true',
                        help='Activates Azure metrics')
    parser.add_argument('--gc', action='store_true',
                        help='Activates Google Cloud metrics')

    parser.add_argument('--grpc', action='store_true',
                        help='Publish gRPC metrics')
    parser.add_argument('--schedulers', action='store_true',
                        help='Publish scheduler metrics')
    parser.add_argument('--stores', action='store_true',
                        help='Publish store metrics')
    parser.add_argument('--workers', action='store_true',
                        help='Publish worker metrics')
    parser.add_argument('--global', action='store_true',
                        help='Publish global metrics')

    args = parser.parse_args()

    prometheus_url = "http://prometheus.example.com:9090"
    prometheus = PrometheusConnect(url=prometheus_url)

    if args.all:
        cloud_providers_indices = [0, 1, 2]  # AWS, Azure, Google Cloud
    else:
        cloud_providers_indices = []
        if args.aws:
            cloud_providers_indices.append(0)
        if args.azure:
            cloud_providers_indices.append(1)
        if args.gc:
            cloud_providers_indices.append(2)

    selected_cloud_providers = [CLOUD_PROVIDER_PUBLISHERS[i]
                                for i in cloud_providers_indices]

    for cloud_provider in selected_cloud_providers:
        cloud_provider()


if __name__ == "__main__":
    main()


def cloud_service_picker():
    inp = ""

    while not numeric_list_input_valid(inp):

        inp = input("Write a list of the services you'd\
        like to publish prometheus metrics to \
        [ex: choosing GCP and Azure would be \"1, 2\"]:")

        num_list = inp.literal_eval(inp)

        i = 0
        for num in num_list:
            num_list[i] = num - 1
            i += 1

        if numeric_list_input_valid(inp):
            return num_list
        else:
            print("Input format is incorrect")


def numeric_list_input_valid(input_string):
    # Remove spaces from the input string
    input_string = input_string.replace(" ", "")

    # Define a regular expression pattern for the valid format
    pattern = r"^\d+(,\d+)*$"

    # Use re.match to check if the string matches the pattern
    return re.match(pattern, input_string)
