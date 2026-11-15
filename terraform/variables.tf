variable "compartment_ocid" {
  type        = string
  description = "Compartment that owns the rule, topic and subscriptions."
}

variable "oncall_email" {
  type        = string
  description = "Email address that receives alarm notifications."
}

variable "webhook_url" {
  type        = string
  description = "HTTPS endpoint that receives alarm notifications for automation."
}
