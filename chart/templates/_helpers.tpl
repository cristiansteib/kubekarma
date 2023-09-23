{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "crd.name" -}}
{{/*
name must match the spec fields below, and be in the form: <plural>.<group>
*/}}
{{- .Values.crd.plural }}.{{ .Values.crd.group }}
{{- end }}


{{- define "svc.headless-service-name" }}
{{- .Release.Name }}-headless-service
{{- end}}

{{- define "svc.headless-service-url" }}http://{{- include "svc.headless-service-name" . }}.{{ .Release.Namespace }}.svc.cluster.local:8000
{{- end}}