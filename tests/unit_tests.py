import unittest
from unittest.mock import patch, Mock
from cloud_publisher import (publish_aws_cloudwatch,
                             publish_azure_monitor,
                             publish_google_cloud_monitoring)


class CloudPublisherUnitTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('your_script.boto3.client')
    def test_aws_cloudwatch_publish(self, mock_boto3_client):
        mock_cloudwatch = Mock()
        mock_boto3_client.return_value = mock_cloudwatch

        metric_names = ["metric1", "metric2"]
        value = 42

        publish_aws_cloudwatch(metric_names)

        mock_cloudwatch.put_metric_data.assert_called_once_with(
            Namespace="YourNamespace",
            MetricData=[
                {
                    "MetricName": "metric1",
                    "Value": value,
                    "Unit": "Count",
                },
                {
                    "MetricName": "metric2",
                    "Value": value,
                    "Unit": "Count",
                },
            ],
        )

    @patch('your_script.DefaultAzureCredential')
    @patch('your_script.MonitorManagementClient')
    def test_azure_monitor_publish(self, mock_monitor_client, mock_credential):

        mock_monitor = Mock()
        mock_monitor_client.return_value = mock_monitor
        mock_credential.return_value = "fake_credential"

        metric_names = ["metric1", "metric2"]
        expected_query_response = "Azure Monitor Query Response"

        mock_monitor.query.return_value = expected_query_response

        publish_azure_monitor("YourMetricsNamespace", metric_names)

        mock_monitor.query.assert_called_once_with(
            resource_uri=("/subscriptions/YourSubscriptionID/resourceGroups"
                          "YourResourceGroup/providers/Microsoft.Compute"
                          "virtualMachines/YourVM"),
            metric_names=["metric1", "metric2"],
            timespan="2023-10-01T00:00:00Z/2023-10-02T00:00:00Z",
            interval="PT1H",
            aggregation=["Average"],
            namespace="YourMetricsNamespace",
        )

        self.assertEqual(
            mock_monitor.query.call_args_list[0][1]['metric_names'],
            expected_query_response)

    @patch('your_script.monitoring_v3.MetricServiceClient')
    def test_google_cloud_monitoring_publish(self,
                                             mock_metric_service_client):
        mock_client = Mock()
        mock_metric_service_client.return_value = mock_client

        metric_names = ["metric1", "metric2"]

        publish_google_cloud_monitoring(3600, metric_names)

        mock_client.create_time_series.assert_called_once()


if __name__ == '__main__':
    unittest.main()
