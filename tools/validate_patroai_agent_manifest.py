#!/usr/bin/env python3
"""Verificação LOCAL e SOMENTE LEITURA de metadados candidatos PatroAI.
Não importa módulos do backend, não executa agentes e não escreve no DB/GitHub.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

class ManifestError(ValueError):
    pass

GATES = ("runtime_enabled", "execute", "create_agent", "activate_agent",
         "publish_knowledge", "grant_roles", "allow_cross_tenant",
         "allow_secrets", "financial_knowledge_public")

def validate(manifest: dict, catalog: dict, catalog_raw: bytes) -> dict:
    if manifest.get("artifact_kind") != "PATROAI_AGENT_AFFILIATION_PROPOSAL_METADATA_ONLY":
        raise ManifestError("ARTIFACT_KIND_INVALID")
    if manifest.get("scope") != "PREPARATORY_METADATA_ONLY":
        raise ManifestError("SCOPE_MUST_BE_PROPOSAL_ONLY")
    if manifest.get("organization", {}).get("actual_tenant_id") is not None:
        raise ManifestError("BROWSER_TENANT_BINDING_FORBIDDEN")
    if manifest["organization"].get("tenant_binding") != "MUST_RESOLVE_SERVER_SIDE_FROM_AUTHENTICATED_PRINCIPAL":
        raise ManifestError("TENANT_AUTHORITY_REQUIRED")
    if manifest.get("source_catalog_version") != catalog.get("catalog_version"):
        raise ManifestError("SOURCE_CATALOG_VERSION_MISMATCH")
    if manifest.get("source_catalog_sha256") != hashlib.sha256(catalog_raw).hexdigest():
        raise ManifestError("SOURCE_CATALOG_SHA256_MISMATCH")
    if manifest.get("approval", {}).get("publication") != "NO_GO":
        raise ManifestError("PUBLICATION_MUST_REMAIN_NO_GO")
    if manifest.get("approval", {}).get("runtime_activation") != "NO_GO":
        raise ManifestError("RUNTIME_MUST_REMAIN_NO_GO")
    safety = manifest.get("safety", {})
    if any(safety.get(gate) is not False for gate in GATES):
        raise ManifestError("UNAUTHORIZED_ENABLED_CAPABILITY")
    if safety.get("no_client_supplied_tenant_authority") is not True:
        raise ManifestError("CLIENT_TENANT_AUTHORITY_FORBIDDEN")
    expected = {a["agent_id"]: a for a in catalog.get("agents", [])}
    actual = manifest.get("agents", [])
    if len(expected) != 33 or len(actual) != len(expected) or manifest.get("agent_count") != 33:
        raise ManifestError("AGENT_COUNT_MISMATCH")
    seen = set()
    for agent in actual:
        slug = agent.get("agent_id")
        if not slug or slug in seen or slug not in expected:
            raise ManifestError("UNKNOWN_OR_DUPLICATE_AGENT")
        seen.add(slug)
        source = expected[slug]
        for key in ("canonical_name", "display_name", "role_code", "department"):
            if agent.get(key) != source.get(key):
                raise ManifestError("AGENT_SOURCE_DRIFT:" + slug + ":" + key)
        if agent.get("affiliation_target") != "PATROAI_CONSULTECH":
            raise ManifestError("AFFILIATION_INVALID")
        if agent.get("affiliation_status") != "PROPOSED_NOT_RUNTIME_ENABLED":
            raise ManifestError("PREMATURE_RUNTIME_STATUS")
        if agent.get("role_scope") != "ADVISORY_ONLY_NO_NEW_CAPABILITIES":
            raise ManifestError("NEW_CAPABILITY_NOT_ALLOWED")
        if any(key in agent for key in ("tenant_id", "permissions", "secrets", "token", "password", "api_key")):
            raise ManifestError("PRIVILEGED_FIELD_FORBIDDEN")
    if seen != set(expected):
        raise ManifestError("SOURCE_AGENT_SET_MISMATCH")
    return {"status":"PASS_LOCAL_METADATA_ONLY", "agents_checked":len(seen),
            "runtime_activation":"NO_GO", "publication":"NO_GO",
            "catalog_sha256":hashlib.sha256(catalog_raw).hexdigest()}

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--catalog",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
        raw=args.catalog.read_bytes()
        catalog=json.loads(raw.decode("utf-8"))
        result=validate(manifest,catalog,raw)
    except (ManifestError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
