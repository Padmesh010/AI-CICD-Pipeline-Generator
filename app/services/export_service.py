import os
import zipfile
import tarfile
import hashlib
from typing import Dict, Any, Optional
from app.core.logger import logger
from app.core.security import security_manager
from app.core.exceptions import ConfigurationError, ErrorHandler
from app.database.db import db_manager

class ExportService:
    """Enterprise multi-format export and release packaging service."""

    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        """Compute SHA256 checksum hash for release verification."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def export_single_file(self, target_path: str, content: str) -> Dict[str, Any]:
        """Export single raw configuration file safely."""
        sanitized_path = security_manager.sanitize_filepath(target_path)
        os.makedirs(os.path.dirname(sanitized_path), exist_ok=True)

        try:
            with open(sanitized_path, "w", encoding="utf-8") as f:
                f.write(content)

            checksum = self.calculate_sha256(sanitized_path)
            db_manager.log_audit("export_single_file", "SUCCESS", f"Exported: {sanitized_path} | SHA256: {checksum}")
            logger.info(f"Exported single file: {sanitized_path}")

            return {
                "status": "success",
                "filepath": sanitized_path,
                "sha256": checksum,
                "size_bytes": os.path.getsize(sanitized_path)
            }
        except Exception as e:
            ErrorHandler.handle_exception(
                ConfigurationError(f"Failed to export file to '{target_path}': {e}", e),
                show_dialog=False
            )
            raise e

    def export_zip_bundle(self, output_zip_path: str, files_dict: Dict[str, str]) -> Dict[str, Any]:
        """Package multiple files into a clean .zip repository structure."""
        sanitized_zip = security_manager.sanitize_filepath(output_zip_path)
        os.makedirs(os.path.dirname(sanitized_zip), exist_ok=True)

        try:
            with zipfile.ZipFile(sanitized_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for rel_file_path, file_content in files_dict.items():
                    zipf.writestr(rel_file_path.replace("\\", "/"), file_content)

            checksum = self.calculate_sha256(sanitized_zip)
            db_manager.log_audit("export_zip_bundle", "SUCCESS", f"Bundle: {sanitized_zip} | Files: {len(files_dict)}")
            logger.info(f"Exported ZIP repository bundle: {sanitized_zip} ({len(files_dict)} files)")

            return {
                "status": "success",
                "archive_path": sanitized_zip,
                "file_count": len(files_dict),
                "sha256": checksum,
                "size_bytes": os.path.getsize(sanitized_zip)
            }
        except Exception as e:
            ErrorHandler.handle_exception(
                ConfigurationError(f"Failed to create ZIP bundle '{output_zip_path}': {e}", e),
                show_dialog=False
            )
            raise e

    def export_targz_bundle(self, output_tar_path: str, files_dict: Dict[str, str]) -> Dict[str, Any]:
        """Package multiple files into a compressed .tar.gz archive."""
        sanitized_tar = security_manager.sanitize_filepath(output_tar_path)
        os.makedirs(os.path.dirname(sanitized_tar), exist_ok=True)

        try:
            with tarfile.open(sanitized_tar, "w:gz") as tar:
                for rel_file_path, file_content in files_dict.items():
                    data_bytes = file_content.encode("utf-8")
                    ti = tarfile.TarInfo(name=rel_file_path.replace("\\", "/"))
                    ti.size = len(data_bytes)
                    import io
                    tar.addfile(ti, io.BytesIO(data_bytes))

            checksum = self.calculate_sha256(sanitized_tar)
            db_manager.log_audit("export_targz_bundle", "SUCCESS", f"Tarball: {sanitized_tar}")
            logger.info(f"Exported TAR.GZ archive: {sanitized_tar}")

            return {
                "status": "success",
                "archive_path": sanitized_tar,
                "file_count": len(files_dict),
                "sha256": checksum,
                "size_bytes": os.path.getsize(sanitized_tar)
            }
        except Exception as e:
            ErrorHandler.handle_exception(
                ConfigurationError(f"Failed to create TAR.GZ bundle '{output_tar_path}': {e}", e),
                show_dialog=False
            )
            raise e

# Global export service instance
export_service = ExportService()
