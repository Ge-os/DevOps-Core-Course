{{- define "devops-python-app-v2.name" -}}
{{ include "common.name" . }}
{{- end -}}

{{- define "devops-python-app-v2.fullname" -}}
{{ include "common.fullname" . }}
{{- end -}}

{{- define "devops-python-app-v2.labels" -}}
{{ include "common.labels" . }}
app.kubernetes.io/component: api
{{- end -}}

{{- define "devops-python-app-v2.selectorLabels" -}}
{{ include "common.selectorLabels" . }}
{{- end -}}
