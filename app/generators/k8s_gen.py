import re

def sanitize_k8s_name(name: str) -> str:
    """Sanitize string to comply with Kubernetes DNS-1123 subdomain standards (lowercase, hyphens, alphanumeric)."""
    if not name:
        return "my-app"
    clean = name.lower()
    clean = re.sub(r"[\s_]+", "-", clean)
    clean = re.sub(r"[^a-z0-9\-]", "", clean)
    clean = re.sub(r"-+", "-", clean)
    clean = clean.strip("-")
    return clean[:63] if clean else "my-app"

def generate_k8s_manifests(app_name="my-app", namespace="production", replicas=3, port=8000, ingress_host="app.local"):
    """Generate typical Kubernetes manifests for service deployment."""
    app_name = sanitize_k8s_name(app_name)
    namespace = sanitize_k8s_name(namespace)
    ingress_host = sanitize_k8s_name(ingress_host.replace(".local", "")) + ".local" if "." in ingress_host else sanitize_k8s_name(ingress_host)
    
    deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: custom-registry.io/{app_name}:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: {port}
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "250m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 10
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          runAsNonRoot: true
          runAsUser: 10001
          capabilities:
            drop:
            - ALL
"""

    service = f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {namespace}
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: {port}
    protocol: TCP
  selector:
    app: {app_name}
"""

    ingress = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}-ingress
  namespace: {namespace}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - {ingress_host}
    secretName: {app_name}-tls-secret
  rules:
  - host: {ingress_host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}
            port:
              number: 80
"""

    hpa = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: {replicas}
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
"""

    network_policy = f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {app_name}-net-policy
  namespace: {namespace}
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {{}}
    ports:
    - protocol: TCP
      port: {port}
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
"""

    configmap = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
  namespace: {namespace}
data:
  ENVIRONMENT: "Production"
  LOG_LEVEL: "info"
"""

    namespace_manifest = f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
"""

    return {
        "namespace.yaml": namespace_manifest,
        "deployment.yaml": deployment,
        "service.yaml": service,
        "ingress.yaml": ingress,
        "hpa.yaml": hpa,
        "network-policy.yaml": network_policy,
        "configmap.yaml": configmap
    }
