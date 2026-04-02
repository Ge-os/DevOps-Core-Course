{{/*
Wrapper helpers so app templates are clear while labels remain shared via library chart.
*/}}
{{- define "devops-python-app.name" -}}
{{ include "common.name" . }}
{{- end -}}

{{- define "devops-python-app.fullname" -}}
{{ include "common.fullname" . }}
{{- end -}}

{{- define "devops-python-app.labels" -}}
{{ include "common.labels" . }}
app.kubernetes.io/component: api
{{- end -}}

{{- define "devops-python-app.selectorLabels" -}}
{{ include "common.selectorLabels" . }}
{{- end -}}
