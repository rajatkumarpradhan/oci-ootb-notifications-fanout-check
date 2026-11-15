# OCI Events + OCI Notifications fan-out wiring.
# TEMPLATE ONLY: not plan/apply validated. No rule, topic or subscription was
# created; no message was published or delivered. Provided as the native-service
# half of this project.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  # Configure via environment (OCI_CLI_AUTH / config file) in a real deployment.
}

# The topic every alarm event is published to.
resource "oci_ons_notification_topic" "prod_alarms" {
  compartment_id = var.compartment_ocid
  name           = "prod-alarms"
  description    = "Fan-out topic for OCI Monitoring alarm state changes"
}

# Native event matching: route Monitoring alarm state changes into the topic.
resource "oci_events_rule" "alarm_state_changes" {
  compartment_id = var.compartment_ocid
  display_name   = "alarm-state-changes-to-topic"
  is_enabled     = true

  condition = jsonencode({
    eventType = ["com.oraclecloud.monitoring.alarmstatechange"]
  })

  actions {
    actions {
      action_type = "ONS"
      topic_id    = oci_ons_notification_topic.prod_alarms.id
      is_enabled  = true
    }
  }
}

# Subscribers: email for humans, HTTPS webhook for automation.
resource "oci_ons_subscription" "oncall_email" {
  compartment_id = var.compartment_ocid
  topic_id       = oci_ons_notification_topic.prod_alarms.id
  protocol       = "EMAIL"
  endpoint       = var.oncall_email
}

resource "oci_ons_subscription" "automation_webhook" {
  compartment_id = var.compartment_ocid
  topic_id       = oci_ons_notification_topic.prod_alarms.id
  protocol       = "HTTPS"
  endpoint       = var.webhook_url
}
