# Metadata & Auth Integration Framework

## Purpose
Provide a structured framework to plug in cluster metadata, Loki auth, and network topology details without blocking core LogService development.

## Artifacts
- Config schema: `config/schema/cluster_config.schema.json`
- Example config: `config/examples/cluster.example.json`
- Input worksheet: `docs/metadata_auth_inputs.md`

## Integration Points

### 1) Metadata Provider
Supported provider types:
- `static`: local config file only.
- `http`: metadata service endpoint (CMDB or internal API).
- `k8s`: Kubernetes API discovery.
- `cmdb`: dedicated CMDB connector.

Required fields:
- provider
- endpoint (for http/cmdb)
- auth_ref
- timeout_ms
- cache_ttl_s

### 2) Loki Authentication
Supported auth types:
- token (bearer or custom header)
- basic
- oauth / sso (profile-based)
- none

Required fields:
- base_url
- tenant_header + tenant (if multi-tenant)
- auth.type + ref(s)

### 3) Label Mapping
Provide label keys that map Loki labels to:
- cluster
- namespace
- pod
- component
- (optional) instance, job, container

### 4) Network Topology
Define connection mode and proxy:
- direct
- proxy
- bastion
- vpn

Include:
- proxy address (if any)
- no_proxy list

### 5) Audit & Compliance
- Define required audit headers or request tags.
- Define redaction rules for sensitive fields.

## Runtime Behavior
- LogService loads the config at startup and validates with schema.
- Metadata resolver caches responses by cluster ID with TTL.
- Loki adapter injects tenant/auth headers and label mapping.

