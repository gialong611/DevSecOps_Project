# Luật PHÁT HIỆN action reference không ghim SHA (D28), chạy bằng Conftest:
#   conftest test -p rules/conftest ../../.github/workflows/ci.yml
# D26-D27 do Checkov github_actions phát hiện; rule ID dưới đây là riêng của đề tài.
package main

import rego.v1

# D28 / DSEC_GHA_001: action tham chiếu mutable (tag/nhánh), không ghim SHA 40 ký tự.
deny contains msg if {
	some name, job in input.jobs
	some step in object.get(job, "steps", [])
	is_string(step.uses)
	not regex.match("^[^@]+@[0-9a-f]{40}$", step.uses)
	msg := sprintf("DSEC_GHA_001: mutable action reference %v in job %v", [step.uses, name])
}
