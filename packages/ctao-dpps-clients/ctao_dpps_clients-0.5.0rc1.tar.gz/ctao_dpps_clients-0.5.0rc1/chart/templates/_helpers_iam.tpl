{{/*
this overrides IAM
*/}}
{{- define "indigo-iam.fullname" -}}
{{- .Release.Name }}-iam
{{- end }}
