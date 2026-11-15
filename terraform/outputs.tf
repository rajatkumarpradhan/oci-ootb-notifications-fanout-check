output "topic_id" {
  value       = oci_ons_notification_topic.prod_alarms.id
  description = "ID of the Notifications topic (template output; never applied)."
}

output "events_rule_id" {
  value       = oci_events_rule.alarm_state_changes.id
  description = "ID of the Events rule (template output; never applied)."
}
