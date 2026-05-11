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
        self.verify_url = "https://api.gumroad.com/v2/licenses/verify"
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
        """Gumroad APIを使用してライセンスを有効化する。"""
        logger.info(f"Activating license via Gumroad for machine: {self.fingerprint}")

        payload = {
            "product_id": settings.gumroad_product_id,
            "license_key": license_key,
            "increment_uses_count": "true" # 使用回数をカウントアップ
        }

        try:
            resp = requests.post(self.verify_url, data=payload)
            data = resp.json()

            if resp.status_code == 200 and data.get("success"):
                logger.info("Gumroad license activation successful.")
                # 追加情報としてフィンガープリントとキーを保存
                data["meta"] = {
                    "activated_at": datetime.now().isoformat(),
                    "fingerprint": self.fingerprint,
                    "license_key": license_key
                }
                self._save_to_cache(json.dumps(data))
                return data
            else:
                error_msg = data.get("message", "Unknown error from Gumroad")
                raise Exception(f"Activation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Network error during activation: {e}")
            raise

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

            # Gumroadの成功フラグを確認
            if not data.get("success"):
                return False

            # マシンの一致確認（簡易的なコピー防止）
            meta = data.get("meta", {})
            if meta.get("fingerprint") != self.fingerprint:
                logger.warning("License was activated on a different machine.")
                return False

            # 返金・チャージバック等の確認
            purchase = data.get("purchase", {})
            if purchase.get("refunded") or purchase.get("chargebacked"):
                logger.warning("License has been refunded or chargebacked.")
                return False

            # 最終確認としてオンラインで再検証する（オプション: 毎回ではなく一定期間ごとなど）
            # ここではシンプルにするため、キャッシュがあれば有効とする
            return True
        except Exception as e:
            logger.error(f"Error during local validation: {e}")
            return False

    def get_status_summary(self) -> str:
        """現在のライセンス状態の要約を返す。"""
        if not self.cache_file.exists():
            return "No license activated."
        
        try:
            with open(self.cache_file, encoding="utf-8") as f:
                data = json.load(f)
            
            purchase = data.get("purchase", {})
            email = purchase.get("email", "Unknown")
            valid = self.validate_locally()
            
            status = "VALID" if valid else "INVALID"
            return f"License (Gumroad) | Status: {status} | User: {email}"
        except Exception:
            return "Error reading license status."
