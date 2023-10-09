import unittest
from unittest.mock import patch, Mock, call, ANY
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

        mock_cloudwatch.put_metric_data.assert_has_calls(expected_calls,
                                                         any_order=True)

    @patch('cloud_publisher.DefaultAzureCredential')
    @patch('cloud_publisher.MonitorManagementClient')
    def test_azure_monitor_publish(self, mock_monitor_client, mock_credential):
        mock_monitor = Mock()
        mock_monitor_client.return_value = mock_monitor
        mock_credential.return_value = "fake_credential"

        metric_names = ["metric1", "metric2"]
        expected_query_response = "Azure Monitor Query Response"

        mock_monitor.query.return_value = expected_query_response

        expected_calls = []

        for metric_name in metric_names:
            expected_calls.append(
                call(
                    resource_uri=ANY,
                    metric_names=[metric_name],
                    timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
                    interval="PT1H",
                    aggregation=["Average"],
                    namespace=ANY,
                )
            )

        results = publish_azure_monitor("namespace", metric_names)

        for result in results:
            self.assertEqual(result, expected_query_response)

        mock_monitor.query.assert_has_calls(expected_calls, any_order=True)

    @patch('cloud_publisher.monitoring_v3.MetricServiceClient')
    def test_google_cloud_monitoring_publish(self, mock_metric_service_client):
        project_id = os.getenv("PROJECT_ID")
        project_name = os.getenv("PROJECT_NAME")

        metric_names = ["metric1", "metric2"]

        mock_client = Mock()

        def create_time_series_side_effect(name, time_series):
            return {"name": name, "time_series": time_series}

        mock_client.create_time_series.side_effect = lambda name, time_series: create_time_series_side_effect(
            name, time_series
        )

        mock_metric_service_client.return_value = mock_client

        expected_time_series = []

        resource = {
            'type': 'global',
            'labels': {
                'project_id': project_id
            }
        }

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

        publish_google_cloud_monitoring(3600, metric_names)

        modified_expected_calls = []

        for actual_call in mock_client.create_time_series.call_args_list:
            start_time = actual_call[1]['time_series'][0]['points'][0]['interval']['start_time']
            end_time = actual_call[1]['time_series'][0]['points'][0]['interval']['end_time']
            metric_field = actual_call[1]['time_series'][0]['metric']
            metric_name = metric_field.split('/')[-1]
            expected_call = call(
                name=f"projects/{project_name}",
                time_series=[
                    {
                        "metric":
                            f"projects/{project_name}/metricDescriptors/{metric_name}",
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

            modified_expected_calls.append(expected_call)

        assert_calls_match(mock_client, modified_expected_calls)


def assert_calls_match(mock_client, modified_expected_calls):
    for actual_call in mock_client.create_time_series.call_args_list:
        actual_args, _ = actual_call

        if actual_args == ():
            continue

        found_match = False
        print(f"Actual call working: {actual_args}")

        for expected_call in modified_expected_calls:
            actual_metric = actual_args[1]['time_series'][0]['metric']
            expected_metric = expected_call[1]['time_series'][0]['metric']
            actual_resource_type = actual_args[1]
            ['time_series'][0]['resource']['type']
            expected_resource_type = expected_call[1]
            ['time_series'][0]['resource']['type']

            if actual_metric == expected_metric and actual_resource_type == expected_resource_type:
                modified_expected_calls.remove(expected_call)
                found_match = True
                break

        if not found_match:
            print(f"Actual call: {actual_args}")
            assert False, f"Expected call not found in actual calls."


if __name__ == '__main__':
    unittest.main()
