output "topic_id" {
  value       = oci_ons_notification_topic.prod_alarms.id
  description = "ID of the Notifications topic (template output; never applied)."
}

output "alarm_id" {
  value       = oci_monitoring_alarm.high_cpu.id
  description = "ID of the Monitoring alarm publishing to the topic (template output; never applied)."
}
