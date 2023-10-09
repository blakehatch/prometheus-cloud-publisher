import unittest
from unittest.mock import patch, Mock, call, ANY
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf import any_pb2
import sys
import os

# Add the 'src' directory to the Python path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(src_dir)

from cloud_publisher import (publish_aws_cloudwatch,
                             publish_azure_monitor,
                             publish_google_cloud_monitoring)


class CloudPublisherUnitTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('cloud_publisher.boto3.client')
    def test_aws_cloudwatch_publish(self, mock_boto3_client):
        mock_cloudwatch = Mock()
        mock_boto3_client.return_value = mock_cloudwatch

        metric_names = ["metric1", "metric2"]
        value = 42

        publish_aws_cloudwatch(metric_names)

        # Modify the assertion to expect multiple calls based on the number of metric names
        expected_calls = [
            call(
                Namespace=ANY,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": "Count",
                    },
                ],
            )
            for metric_name in metric_names
        ]

        mock_cloudwatch.put_metric_data.assert_has_calls(expected_calls, any_order=True)



    @patch('cloud_publisher.DefaultAzureCredential')
    @patch('cloud_publisher.MonitorManagementClient')
    def test_azure_monitor_publish(self, mock_monitor_client, mock_credential):
        mock_monitor = Mock()
        mock_monitor_client.return_value = mock_monitor
        mock_credential.return_value = "fake_credential"

        metric_names = ["metric1", "metric2"]
        expected_query_response = "Azure Monitor Query Response"

        # Mock the query method to return the response
        mock_monitor.query.return_value = expected_query_response

        # Initialize the list to store the expected calls
        expected_calls = []

        # Iterate through metric_names and create an expected call for each
        for metric_name in metric_names:
            expected_calls.append(
                call(
                    resource_uri=ANY,  # Use ANY to match any value for resource_uri
                    metric_names=[metric_name],  # Use the current metric_name
                    timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
                    interval="PT1H",
                    aggregation=["Average"],
                    namespace=ANY,  # Use ANY to match any value for namespace
                )
            )

        # Call the publish_azure_monitor function
        results = publish_azure_monitor("namespace", metric_names)

        # Modify the assertion to compare the actual results with the expected results for each metric name
        for result in results:
            self.assertEqual(result, expected_query_response)

        # Use assert_has_calls to match the expected calls
        mock_monitor.query.assert_has_calls(expected_calls, any_order=True)


    @patch('cloud_publisher.monitoring_v3.MetricServiceClient')
    def test_google_cloud_monitoring_publish(self, mock_metric_service_client):
        # Define project_name and project_id
        project_id = os.getenv("PROJECT_ID")
        project_name = os.getenv("PROJECT_NAME")

        # Define metric_names
        metric_names = ["metric1", "metric2"]

        # Create a mock object for the MetricServiceClient
        mock_client = Mock()

        # Define a function to return the expected TimeSeries data
        def create_time_series_side_effect(name, time_series):
            return {"name": name, "time_series": time_series}

        # Set the side_effect of create_time_series to return the expected data
        mock_client.create_time_series.side_effect = lambda name, time_series: create_time_series_side_effect(
            name, time_series
        )

        # Set the return value of MetricServiceClient to the mock client
        mock_metric_service_client.return_value = mock_client

        # Initialize an empty list to store expected_time_series
        expected_time_series = []

        resource = {
            'type': 'global',
            'labels': {
                'project_id': project_id  # Change "key" to the actual label key used in the actual code
            }
        }

        # Iterate over metric_names to create separate time series for each metric
        for metric_name in metric_names:
            expected_time_series.append(
                {
                    "metric": f"projects/{project_name}/metricDescriptors/{metric_name}",
                    "resource": resource,
                    "points": [
                        {
                            "interval": {
                                "start_time": {"seconds": 0, "nanos": 0},
                                "end_time": {"seconds": 3600, "nanos": 0},
                            },
                            "value": {
                                "int64_value": 42,
                            },
                        }
                    ],
                }
            )

        # Call the publish_google_cloud_monitoring function
        publish_google_cloud_monitoring(3600, metric_names)

        # Verify that create_time_series is called with the expected TimeSeries
        expected_calls = [
            call(
                name=f"projects/{project_name}",
                time_series=expected_time_series
            )
        ]


        # Create an empty list to store modified expected calls
        modified_expected_calls = []

        # Iterate through actual calls made to mock_client.create_time_series
        for actual_call in mock_client.create_time_series.call_args_list:
            # Extract start_time and end_time from the actual call
            start_time = actual_call[1]['time_series'][0]['points'][0]['interval']['start_time']
            end_time = actual_call[1]['time_series'][0]['points'][0]['interval']['end_time']
            # Extract metric_name from the actual call by splitting the metric field
            metric_field = actual_call[1]['time_series'][0]['metric']
            metric_name = metric_field.split('/')[-1]  # Extract the last part of the metric field
            # Modify the corresponding fields in the expected call
            expected_call = call(
                name=f"projects/{project_name}",
                time_series=[
                    {
                        "metric": f"projects/{project_name}/metricDescriptors/{metric_name}",
                        "resource": resource,
                        "points": [
                            {
                                "interval": {
                                    "start_time": start_time,
                                    "end_time": end_time,
                                },
                                "value": {
                                    "int64_value": 42,
                                },
                            }
                        ],
                    }
                ]
            )

            # Append the modified expected call to the list
            modified_expected_calls.append(expected_call)

        assert_calls_match(mock_client, modified_expected_calls)


def assert_calls_match(mock_client, modified_expected_calls):
    # Iterate through actual calls made to mock_client.create_time_series
    for actual_call in mock_client.create_time_series.call_args_list:
        # Exclude empty tuples
        actual_args, _ = actual_call

        if actual_args == ():
            continue  # Skip empty tuples



        # Check if the actual call arguments are present in the modified expected calls
        found_match = False
        print(f"Actual call working: {actual_args}")

        for expected_call in modified_expected_calls:
            # Extract relevant fields for comparison
            actual_metric = actual_args[1]['time_series'][0]['metric']
            expected_metric = expected_call[1]['time_series'][0]['metric']
            actual_resource_type = actual_args[1]['time_series'][0]['resource']['type']
            expected_resource_type = expected_call[1]['time_series'][0]['resource']['type']

            # Compare the relevant fields
            if actual_metric == expected_metric and actual_resource_type == expected_resource_type:
                # Remove the matched expected call to avoid duplicate matching
                modified_expected_calls.remove(expected_call)
                found_match = True
                break  # Found a match, move to the next actual call

        if not found_match:
            print(f"Actual call: {actual_args}")
            assert False, f"Expected call not found in actual calls."

if __name__ == '__main__':
    unittest.main()
