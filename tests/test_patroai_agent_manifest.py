"""Testes locais de invariantes documentais e fail-closed.
Não dependem de API, DB, cloud ou produção.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "validate_patroai_agent_manifest.py"
MANIFEST = ROOT / "docs" / "patroai" / "agents_affiliation_candidate.json"
spec = importlib.util.spec_from_file_location("patroai_preflight", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class AgentAffiliationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.catalog = {
          "catalog_version": cls.base["source_catalog_version"],
          "agents": [{k: a[k] for k in ("agent_id","canonical_name","display_name","role_code","department")}
                     for a in cls.base["agents"]]
        }
        cls.raw = json.dumps(cls.catalog, ensure_ascii=False).encode("utf-8")

    def fresh(self):
        m=deepcopy(self.base)
        m["source_catalog_sha256"]=hashlib.sha256(self.raw).hexdigest()
        return m

    def test_valid_metadata_passes_but_does_not_enable(self):
        result=mod.validate(self.fresh(),self.catalog,self.raw)
        self.assertEqual(result["agents_checked"],33)
        self.assertEqual(result["runtime_activation"],"NO_GO")

    def test_enabled_runtime_rejected(self):
        m=self.fresh()
        m["safety"]["runtime_enabled"]=True
        with self.assertRaisesRegex(mod.ManifestError,"UNAUTHORIZED_ENABLED"):
            mod.validate(m,self.catalog,self.raw)

    def test_publish_knowledge_rejected(self):
        m=self.fresh()
        m["safety"]["publish_knowledge"]=True
        with self.assertRaises(mod.ManifestError):
            mod.validate(m,self.catalog,self.raw)

    def test_unknown_agent_rejected(self):
        m=self.fresh()
        m["agents"][0]["agent_id"]="invented_superadmin"
        with self.assertRaises(mod.ManifestError):
            mod.validate(m,self.catalog,self.raw)

    def test_cross_tenant_auth_claim_rejected(self):
        m=self.fresh()
        m["organization"]["actual_tenant_id"]="caller_supplied"
        with self.assertRaisesRegex(mod.ManifestError,"BROWSER_TENANT"):
            mod.validate(m,self.catalog,self.raw)

    def test_source_hash_drift_rejected(self):
        m=self.fresh()
        m["source_catalog_sha256"]="0"*64
        with self.assertRaisesRegex(mod.ManifestError,"SOURCE_CATALOG_SHA256"):
            mod.validate(m,self.catalog,self.raw)

    def test_role_escalation_rejected(self):
        m=self.fresh()
        m["agents"][0]["role_code"]="platform_owner"
        with self.assertRaisesRegex(mod.ManifestError,"SOURCE_DRIFT"):
            mod.validate(m,self.catalog,self.raw)

    def test_secret_field_rejected(self):
        m=self.fresh()
        m["agents"][0]["token"]="not-a-real-token"
        with self.assertRaisesRegex(mod.ManifestError,"PRIVILEGED_FIELD"):
            mod.validate(m,self.catalog,self.raw)

    def test_activation_status_fails_closed(self):
        m=self.fresh()
        m["approval"]["runtime_activation"]="GO"
        with self.assertRaisesRegex(mod.ManifestError,"RUNTIME_MUST_REMAIN_NO_GO"):
            mod.validate(m,self.catalog,self.raw)

if __name__ == "__main__":
    unittest.main()
