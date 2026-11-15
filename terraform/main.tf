# OCI Monitoring (alarm -> topic destinations) + OCI Notifications fan-out wiring.
# TEMPLATE ONLY: not plan/apply validated. No alarm, topic or subscription was
# created; no notification was published or delivered. Provided as the
# native-service half of this project.
#
# Why an alarm destination and not an Events rule: OCI Monitoring alarm state
# changes notify Notifications topics directly through the alarm's
# `destinations` list. The Events service emits events for alarm *config*
# changes (Alarm - Create/Update/Delete), not for alarm state transitions.

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

# The topic every alarm notification is published to.
resource "oci_ons_notification_topic" "prod_alarms" {
  compartment_id = var.compartment_ocid
  name           = "prod-alarms"
  description    = "Fan-out topic for OCI Monitoring alarm notifications"
}

# Native publishing path: the alarm lists the topic as a destination, so state
# transitions (OK -> FIRING -> OK) publish straight to the topic with no
# Events rule in between.
resource "oci_monitoring_alarm" "high_cpu" {
  compartment_id        = var.compartment_ocid
  display_name          = "high-cpu-prod"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_computeagent"
  query                 = "CpuUtilization[5m].mean() > 90"
  severity              = "CRITICAL"
  message_format        = "PRETTY_JSON"
  destinations          = [oci_ons_notification_topic.prod_alarms.id]
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
