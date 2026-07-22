from typing import Dict
from app.core.logger import logger

def generate_helm_chart(
    app_name: str = "my-app",
    namespace: str = "production",
    replica_count: int = 3,
    image_repo: str = "custom-registry.io/my-app",
    tag: str = "latest",
    port: int = 8000
) -> Dict[str, str]:
    """Generate standardized Helm Chart files."""
    
    chart_yaml = f"""apiVersion: v2
name: {app_name}
description: Enterprise Helm chart for {app_name} deployment
type: application
version: 0.1.0
appVersion: "{tag}"
"""

    values_yaml = f"""# Default values for {app_name}.
replicaCount: {replica_count}

image:
  repository: {image_repo}
  pullPolicy: IfNotPresent
  tag: "{tag}"

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {{}}
  name: ""

podAnnotations: {{}}
podSecurityContext: {{}}

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  runAsNonRoot: true
  runAsUser: 10001
  capabilities:
    drop:
    - ALL

service:
  type: ClusterIP
  port: 80
  targetPort: {port}

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: {app_name}.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 75
"""

    helpers_tpl = f"""{{/*
Expand the name of the chart.
*/}}
{{{{- define "{app_name}.name" -}}}}
{{{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}}}
{{{{- end -}}}}

{{/*
Create a default fully qualified app name.
*/}}
{{{{- define "{app_name}.fullname" -}}}}
{{{{- if .Values.fullnameOverride -}}}}
{{{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}}}
{{{{- else -}}}}
{{{{- $name := default .Chart.Name .Values.nameOverride -}}}}
{{{{- if contains $name .Release.Name -}}}}
{{{{- .Release.Name | trunc 63 | trimSuffix "-" -}}}}
{{{{- else -}}}}
{{{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}}}
{{{{- end -}}}}
{{{{- end -}}}}
{{{{- end -}}}}
"""

    deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
  namespace: {namespace}
  labels:
    app: {{{{ include "{app_name}.name" . }}}}
spec:
  {{{{- if not .Values.autoscaling.enabled }}}}
  replicas: {{{{ .Values.replicaCount }}}}
  {{{{- end }}}}
  selector:
    matchLabels:
      app: {{{{ include "{app_name}.name" . }}}}
  template:
    metadata:
      labels:
        app: {{{{ include "{app_name}.name" . }}}}
    spec:
      containers:
        - name: {{{{ .Chart.Name }}}}
          securityContext:
            {{{{- toYaml .Values.securityContext | nindent 12 }}}}
          image: "{{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag | default .Chart.AppVersion }}}}"
          imagePullPolicy: {{{{ .Values.image.pullPolicy }}}}
          ports:
            - name: http
              containerPort: {{{{ .Values.service.targetPort }}}}
              protocol: TCP
          resources:
            {{{{- toYaml .Values.resources | nindent 12 }}}}
"""

    service_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
  namespace: {namespace}
spec:
  type: {{{{ .Values.service.type }}}}
  ports:
    - port: {{{{ .Values.service.port }}}}
      targetPort: {{{{ .Values.service.targetPort }}}}
      protocol: TCP
      name: http
  selector:
    app: {{{{ include "{app_name}.name" . }}}}
"""

    return {
        "Chart.yaml": chart_yaml,
        "values.yaml": values_yaml,
        "templates/_helpers.tpl": helpers_tpl,
        "templates/deployment.yaml": deployment_yaml,
        "templates/service.yaml": service_yaml
    }
