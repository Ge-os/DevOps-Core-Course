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

{{- define "devops-python-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else if .Values.serviceAccount.create -}}
{{- include "devops-python-app.fullname" . -}}
{{- else -}}
default
{{- end -}}
{{- end -}}

{{- define "devops-python-app.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- include "devops-python-app.fullname" . -}}-secret
{{- end -}}
{{- end -}}

{{- define "devops-python-app.configFileConfigMapName" -}}
{{- if .Values.configMap.file.name -}}
{{- .Values.configMap.file.name -}}
{{- else -}}
{{- include "devops-python-app.fullname" . -}}-config
{{- end -}}
{{- end -}}

{{- define "devops-python-app.configEnvConfigMapName" -}}
{{- if .Values.configMap.env.name -}}
{{- .Values.configMap.env.name -}}
{{- else -}}
{{- include "devops-python-app.fullname" . -}}-env
{{- end -}}
{{- end -}}

{{- define "devops-python-app.pvcName" -}}
{{- if .Values.persistence.name -}}
{{- .Values.persistence.name -}}
{{- else -}}
{{- include "devops-python-app.fullname" . -}}-data
{{- end -}}
{{- end -}}

{{- define "devops-python-app.visitsFilePath" -}}
{{- printf "%s/%s" (.Values.persistence.mountPath | trimSuffix "/") .Values.persistence.visitsFileName -}}
{{- end -}}

{{- define "devops-python-app.commonEnv" -}}
- name: HOST
  value: {{ .Values.appConfig.host | quote }}
- name: PORT
  value: {{ .Values.appConfig.port | quote }}
- name: DEBUG
  value: {{ .Values.appConfig.debug | quote }}
- name: VISITS_FILE
  value: {{ include "devops-python-app.visitsFilePath" . | quote }}
{{- end -}}
