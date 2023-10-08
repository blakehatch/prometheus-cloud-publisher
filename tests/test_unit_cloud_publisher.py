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
        mock_client = Mock()
        mock_metric_service_client.return_value = mock_client

        metric_names = ["metric1", "metric2"]

        publish_google_cloud_monitoring(3600, metric_names)

        # Create a TimeInterval object
        time_interval = any_pb2.Any()
        time_interval.Pack(Timestamp(seconds=0))  # Replace with your desired start time
        end_time = Timestamp(seconds=3600)  # Replace with your desired end time
        time_interval.Pack(end_time)

        # Modify the assertion to check if create_time_series is called for each metric name
        expected_calls = [
            call(ANY, time_series=ANY)
            for metric_name in metric_names
        ]

        # Replace the time_series argument with the created time_interval
        for call_args in expected_calls:
            call_args.kwargs["time_series"].interval.CopyFrom(time_interval)

        mock_client.create_time_series.assert_has_calls(expected_calls, any_order=True)
if __name__ == '__main__':
    unittest.main()
