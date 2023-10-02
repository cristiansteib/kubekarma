{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "crd.name" -}}
{{/*
name must match the spec fields below, and be in the form: <plural>.<group>
*/}}
{{- .Values.crd.plural }}.{{ .Values.crd.group }}
{{- end }}


{{- define "svc.headless-grpc-service-name" }}
{{- .Release.Name }}-grpc-headless-service
{{- end}}
