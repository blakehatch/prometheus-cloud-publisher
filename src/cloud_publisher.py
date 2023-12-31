from prometheus_api_client import PrometheusConnect
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient
from google.cloud import monitoring_v3
from google.api.monitored_resource_pb2 import MonitoredResource
from google.protobuf.timestamp_pb2 import Timestamp
import re
import time
import datetime
import argparse
import json
import os
from dotenv import load_dotenv

load_dotenv()

prometheus_url = os.getenv("PROMETHEUS_URL")
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
region = os.getenv("REGION")
namespace = os.getenv("NAMESPACE")

resource_group = os.getenv("RESOURCE_GROUP")
subscription_id = os.getenv("SUBSCRIPTION_ID")

project_id = os.getenv("PROJECT_ID")
project_name = os.getenv("PROJECT_NAME")


def publish_aws_cloudwatch(metric_names):
    cloudwatch = boto3.client(
        "cloudwatch",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region,
    )

    for metric_name in metric_names:
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


def publish_azure_monitor(metrics_namespace, metric_names):
    credential = DefaultAzureCredential()

    metrics_client = MonitorManagementClient(credential, subscription_id)

    results = []

    for metric_name in metric_names:
        response = metrics_client.query(
            resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}\
            /providers/Microsoft.Compute/virtualMachines/YourVM",
            metric_names=[metric_name],
            timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
            interval="PT1H",
            aggregation=["Average"],
            namespace=metrics_namespace)

        print("Azure RES: " + response)
        results.append(response)

    return results


def publish_google_cloud_monitoring(interval, metric_names):
    client = monitoring_v3.MetricServiceClient()

    monitored_resource = MonitoredResource(
        type="global",
        labels={"project_id": project_id},
    )

    for metric_name in metric_names:
        descriptor = f"projects/{project_name}/metricDescriptors/{metric_name}"

        now = time.time()
        start_time = Timestamp()
        start_time.FromDatetime(datetime.datetime.utcfromtimestamp(now))
        end_time = Timestamp()
        end_time.FromDatetime(start_time.ToDatetime() +
                              datetime.timedelta(seconds=interval))

        point = {
            "interval": {
                "start_time": start_time,
                "end_time": end_time,
            },
            "value": {
                "int64_value": 42,
            },
        }

        series = {
            "metric": descriptor,
            "resource": monitored_resource,
            "points": [point],
        }

        cts = client.create_time_series(
            name=f"projects/{project_name}",
            time_series=[series],
        )

        print(cts)


CLOUD_PROVIDER_PUBLISHERS = [publish_aws_cloudwatch,
                             publish_azure_monitor,
                             publish_google_cloud_monitoring]


def load_metric_names_config():
    with open('config.json', 'r') as config_file:
        metric_names_config = json.load(config_file)
    return metric_names_config


metric_names_config = load_metric_names_config()


def main():
    parser = argparse.ArgumentParser(
        description='Publish Prometheus metrics to cloud services.')

    args = parser.parse_args()

    selected_metric_names = []
    if args.grpc:
        selected_metric_names.extend(metric_names_config["grpc"])
    if args.schedulers:
        selected_metric_names.extend(metric_names_config["schedulers"])
    if args.stores:
        selected_metric_names.extend(metric_names_config["stores"])
    if args.workers:
        selected_metric_names.extend(metric_names_config["workers"])
    if args.global_metrics:
        selected_metric_names.extend(metric_names_config["global"])

    prometheus = PrometheusConnect(url=prometheus_url)

    for metric_name in selected_metric_names:
        query = f'{metric_name}'
        result = prometheus.custom_query(query)
        print(f"Metrics for {metric_name}: {result}")

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
        cloud_provider(selected_metric_names)


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
    input_string = input_string.replace(" ", "")

    pattern = r"^\d+(,\d+)*$"

    return re.match(pattern, input_string)
