import json
import os
import platform
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from ripen.common.config import settings
from ripen.common.utils import get_logger

logger = get_logger("licensing")

class LicenseManager:
    def __init__(self):
        self.base_url = f"https://api.keygen.sh/v1/accounts/{settings.keygen_account_id}"
        self.cache_file = settings.base_dir / "license.cache"
        self.fingerprint = self._get_machine_fingerprint()

    def _get_machine_fingerprint(self) -> str:
        """マシン固有のIDを生成する。"""
        # 1. Try to get system UUID (Windows/macOS/Linux)
        try:
            if platform.system() == "Windows":
                cmd = "wmic csproduct get uuid"
                uuid_str = subprocess.check_output(cmd, shell=True).decode().split("\n")[1].strip()
                if uuid_str:
                    return uuid_str
            elif platform.system() == "Darwin":
                cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E 'IOPlatformUUID'"
                uuid_str = subprocess.check_output(cmd, shell=True).decode().split('"')[-2]
                if uuid_str:
                    return uuid_str
        except Exception:
            logger.debug("Failed to get system UUID, falling back to node ID")

        # 2. Fallback to MAC address based node ID
        return str(uuid.getnode())

    def activate(self, license_key: str) -> dict:
        """ライセンスを有効化し、このマシンを登録する。"""
        logger.info(f"Activating license for machine: {self.fingerprint}")

        # 1. Validate the key first
        validate_url = f"{self.base_url}/licenses/actions/validate-key"
        headers = {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
        payload = {
            "meta": {
                "key": license_key,
                "scope": {
                    "fingerprint": self.fingerprint
                }
            }
        }

        resp = requests.post(validate_url, headers=headers, json=payload)
        data = resp.json()

        if resp.status_code != 200:
            raise Exception(f"Validation failed: {data.get('errors', [{}])[0].get('detail', 'Unknown error')}")

        code = data["meta"]["code"]
        
        # 2. If valid but no machine, register it
        if code == "NO_MACHINES":
            logger.info("Machine not registered. Registering...")
            
            # We need a token to register a machine. 
            # In a production app, you might use a temporary License Token.
            # For simplicity in this step, we assume the user has a way to register or the policy allows it.
            # Actually, Keygen allows 'machine.create' via a special flow or a Product Token.
            # But the 'validate-key' response contains the license ID which we can use.
            
            license_id = data["data"]["id"]
            register_url = f"{self.base_url}/machines"
            
            # To register, we typically need authentication. 
            # We'll use the license key itself as a token if Keygen is configured for it, 
            # or we might need a Product Token.
            # Since we want to avoid embedding Product Tokens, we'll try to use the License Key.
            
            reg_headers = {
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
                "Authorization": f"License {license_key}"
            }
            reg_payload = {
                "data": {
                    "type": "machines",
                    "attributes": {
                        "fingerprint": self.fingerprint,
                        "name": f"{platform.node()} ({platform.system()})"
                    },
                    "relationships": {
                        "license": {
                            "data": {"type": "licenses", "id": license_id}
                        }
                    }
                }
            }
            
            reg_resp = requests.post(register_url, headers=reg_headers, json=reg_payload)
            if reg_resp.status_code != 201:
                reg_data = reg_resp.json()
                raise Exception(f"Machine registration failed: {reg_data.get('errors', [{}])[0].get('detail', 'Unknown error')}")
            
            logger.info("Machine registered successfully.")
            # Re-validate to get the latest info
            resp = requests.post(validate_url, headers=headers, json=payload)
            data = resp.json()

        license_id = data["data"]["id"]
        
        # 3. Get the SIGNED validation response using the license action
        # This endpoint is more robust for getting signatures
        logger.info("Fetching signed validation response...")
        action_url = f"{self.base_url}/licenses/{license_id}/actions/validate"
        action_payload = {
            "meta": {
                "scope": {
                    "fingerprint": self.fingerprint
                }
            }
        }
        
        # The validate action also needs authentication
        action_headers = {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
            "Authorization": f"License {license_key}"
        }
        
        final_resp = requests.post(action_url, headers=action_headers, json=action_payload)
        
        import sys
        sys.stderr.write(f"[DEBUG] Action Response Headers: {dict(final_resp.headers)}\n")
        
        if final_resp.status_code == 200:
            final_data = final_resp.json()
            
            # Capture HTTP Signature details
            keygen_sig = final_resp.headers.get("Keygen-Signature")
            if keygen_sig:
                import re
                match = re.search(r'signature="([^"]+)"', keygen_sig)
                if match:
                    sig = match.group(1)
                    if "meta" not in final_data:
                        final_data["meta"] = {}
                    final_data["meta"]["signature"] = sig
                    # Store signing context
                    final_data["meta"]["signing_context"] = {
                        "date": final_resp.headers.get("Date"),
                        "digest": final_resp.headers.get("Digest"),
                        "host": "api.keygen.sh",
                        "path": f"/v1/accounts/{settings.keygen_account_id}/licenses/{license_id}/actions/validate"
                    }
                    logger.info("Successfully extracted signature and context from Keygen-Signature header.")
            
            self._save_to_cache(json.dumps(final_data))
            return final_data
        else:
            # Fallback
            logger.warning(f"Failed to get signed response via action ({final_resp.status_code}), falling back.")
            self._save_to_cache(resp.text)
            return data

    def _save_to_cache(self, raw_data: str):
        """認証情報をローカルにキャッシュする。"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(raw_data)
            logger.info(f"License information cached to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to cache license: {e}")

    def validate_locally(self) -> bool:
        """ローカルキャッシュを使用してライセンスを検証する。"""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # 1. Verify Signature
            if not self._verify_signature(data):
                logger.warning("Local license signature is invalid!")
                return False

            # 2. Check Expiry
            attr = data.get("data", {}).get("attributes", {})
            expiry_str = attr.get("expiry")
            if expiry_str:
                expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                if expiry_dt < datetime.now(expiry_dt.tzinfo):
                    logger.warning(f"License has expired: {expiry_dt}")
                    return False

            # 3. Check Fingerprint
            scope = data.get("meta", {}).get("scope", {})
            if scope.get("fingerprint") != self.fingerprint:
                logger.warning(f"License fingerprint mismatch: {scope.get('fingerprint')} vs {self.fingerprint}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error during local validation: {e}")
            return False

    def _verify_signature(self, data: dict) -> bool:
        """Keygenからのデジタル署名を検証する(Ed25519対応)。"""
        signature = data.get("meta", {}).get("signature")
        if not signature:
            return False

        try:
            import base64
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            # Load Ed25519 Public Key from Base64 DER
            public_key_bytes = base64.b64decode(settings.keygen_public_key)
            public_key = serialization.load_der_public_key(public_key_bytes)
            
            sig_bytes = base64.b64decode(signature)

            # Determine signing message
            ctx = data.get("meta", {}).get("signing_context")
            if ctx:
                # Reconstruct HTTP Signing String: (request-target) host date digest
                signing_string = (
                    f"(request-target): post {ctx['path']}\n"
                    f"host: {ctx['host']}\n"
                    f"date: {ctx['date']}\n"
                    f"digest: {ctx['digest']}"
                )
                message = signing_string.encode()
            else:
                # Fallback to plain data object
                message = json.dumps(data["data"], separators=(",", ":")).encode()
            
            if isinstance(public_key, ed25519.Ed25519PublicKey):
                public_key.verify(sig_bytes, message)
                return True
        except InvalidSignature:
            logger.debug("Signature verification failed (InvalidSignature)")
            return False
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
        
        return False

    def get_status_summary(self) -> str:
        """現在のライセンス状態の要約を返す。"""
        if not self.cache_file.exists():
            return "No license activated."
        
        try:
            with open(self.cache_file, encoding="utf-8") as f:
                data = json.load(f)
            
            attr = data.get("data", {}).get("attributes", {})
            name = attr.get("name", "Standard")
            expiry = attr.get("expiry", "Never")
            valid = self.validate_locally()
            
            status = "VALID" if valid else "INVALID"
            return f"License: {name} | Status: {status} | Expires: {expiry}"
        except Exception:
            return "Error reading license status."
