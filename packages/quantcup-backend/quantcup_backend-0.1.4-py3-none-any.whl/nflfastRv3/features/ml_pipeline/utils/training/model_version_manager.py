"""
Model Version Manager

Manages model versions, tags, and metadata for ML pipeline v2.
Enables version tracking, selection, and comparison.

Pattern: Static utility class
Complexity: 3 points (file I/O + JSON handling + bucket integration)
"""

import json
import os
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Union

import joblib

from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter


class ModelVersionManager:
    """
    Manage model versions and selection.
    
    Provides version control for trained models:
    - Save models with version tags and metadata
    - Load specific model versions
    - List all available versions
    - Get latest version
    
    Storage structure:
        ml/models/{model_name}/
            {tag}/
                model.joblib
            versions.json
    """
    
    @staticmethod
    def save_model(model: Any, model_name: str, tag: str, metadata: Dict[str, Any]) -> str:
        """
        Save model with version tag and metadata.
        
        Args:
            model: Trained model to save
            model_name: Name of the model (e.g., 'game_outcome')
            tag: Version tag (e.g., 'week9_3yr', 'latest')
            metadata: Metadata dictionary containing:
                - metrics: Model performance metrics
                - config: Training configuration
                - test_games: Number of test games
                - train_games: Number of training games
                - num_features: Number of features used
                
        Returns:
            str: Path where model was saved
            
        Example:
            >>> metadata = {
            ...     'metrics': {'accuracy': 0.586, 'auc': 0.612},
            ...     'config': {'train_seasons': '2021-2023', 'test_week': 9},
            ...     'test_games': 14,
            ...     'train_games': 765,
            ...     'num_features': 42
            ... }
            >>> path = ModelVersionManager.save_model(model, 'game_outcome', 'week9_3yr', metadata)
        """
        logger = get_logger('nflfastRv3.model_version_manager')
        
        try:
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Verify bucket is available
            if not bucket_adapter._is_available():
                raise ValueError("Bucket storage not available - cannot save model")
            
            # Create version path
            version_path = f"ml/models/{model_name}/{tag}/"
            model_filename = f"{version_path}model.joblib"
            
            # Save model to bucket
            logger.info(f"Saving model to bucket: {model_filename}")
            
            # Serialize model to bytes
            buffer = io.BytesIO()
            joblib.dump(model, buffer)
            buffer.seek(0)
            model_bytes = buffer.read()
            
            # Write to bucket using put_object (s3_client guaranteed not None by _is_available check)
            assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
            bucket_adapter.s3_client.put_object(
                Bucket=bucket_adapter.bucket_name,
                Key=model_filename,
                Body=model_bytes,
                ContentType='application/octet-stream'
            )
            
            # Update versions metadata
            versions_file = f"ml/models/{model_name}/versions.json"
            
            # Load existing versions or create new
            try:
                assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                response = bucket_adapter.s3_client.get_object(
                    Bucket=bucket_adapter.bucket_name,
                    Key=versions_file
                )
                versions_bytes = response['Body'].read()
                versions = json.loads(versions_bytes.decode('utf-8'))
            except Exception:
                versions = {}
            
            # Add new version
            versions[tag] = {
                'created_at': datetime.now().isoformat(),
                'model_path': model_filename,
                'metrics': metadata.get('metrics', {}),
                'training_config': metadata.get('config', {}),
                'test_games': metadata.get('test_games', 0),
                'train_games': metadata.get('train_games', 0),
                'num_features': metadata.get('num_features', 0),
                'is_deployed': False
            }
            
            # Update latest pointer
            versions['latest'] = tag
            
            # Save versions metadata
            versions_json = json.dumps(versions, indent=2)
            assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
            bucket_adapter.s3_client.put_object(
                Bucket=bucket_adapter.bucket_name,
                Key=versions_file,
                Body=versions_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            # Extract key metrics for compact console logging
            metrics = metadata.get('metrics', {})
            accuracy = metrics.get('accuracy', 0)
            auc = metrics.get('auc', 0)
            home_bias = metrics.get('home_win_bias', 0)
            num_features = metadata.get('num_features', 0)
            test_games = metadata.get('test_games', 0)
            
            logger.info(f"✓ Model saved with version tag: {tag}")
            logger.info(f"   Path: {model_filename}")
            logger.info(f"   Metrics Summary:")
            logger.info(f"      Performance: Accuracy={accuracy:.3f} | AUC={auc:.3f} | Bias={home_bias:+.1%}")
            logger.info(f"      Dataset: {num_features} features | {test_games} test games")
            logger.info(f"      Full metrics saved to versions.json")
            
            return model_filename
            
        except Exception as e:
            logger.error(f"Failed to save model version: {e}", exc_info=True)
            raise ValueError(f"Failed to save model version: {e}") from e
    
    @staticmethod
    def load_model(model_name: str, version: str = 'latest') -> Tuple[Any, Dict[str, Any]]:
        """
        Load specific model version.
        
        Args:
            model_name: Name of the model to load
            version: Version tag to load (default: 'latest')
            
        Returns:
            Tuple of (model, metadata)
            
        Raises:
            ValueError: If model version not found
            
        Example:
            >>> model, metadata = ModelVersionManager.load_model('game_outcome', 'week9_3yr')
            >>> print(f"Accuracy: {metadata['metrics']['accuracy']}")
        """
        logger = get_logger('nflfastRv3.model_version_manager')
        
        try:
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Verify bucket is available
            if not bucket_adapter._is_available():
                raise ValueError("Bucket storage not available - cannot load model")
            
            # Load versions metadata
            versions_file = f"ml/models/{model_name}/versions.json"
            
            try:
                assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                response = bucket_adapter.s3_client.get_object(
                    Bucket=bucket_adapter.bucket_name,
                    Key=versions_file
                )
                versions_bytes = response['Body'].read()
                versions = json.loads(versions_bytes.decode('utf-8'))
            except Exception:
                # If versions.json is missing, check if we can load 'latest' directly
                if version == 'latest':
                    direct_path = f"ml/models/{model_name}/latest/model.joblib"
                    logger.info(f"versions.json not found, attempting to load latest model directly from {direct_path}")
                    
                    try:
                        assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                        response = bucket_adapter.s3_client.get_object(
                            Bucket=bucket_adapter.bucket_name,
                            Key=direct_path
                        )
                        model_bytes = response['Body'].read()
                        buffer = io.BytesIO(model_bytes)
                        model = joblib.load(buffer)
                        
                        logger.info(f"✓ Model loaded successfully from direct path")
                        return model, {'model_path': direct_path, 'created_at': 'unknown', 'metrics': {}}
                    except Exception as direct_e:
                        raise ValueError(
                            f"No versions found for model '{model_name}' and direct load failed. "
                            f"Train a model first using: quantcup ml train {model_name}"
                        ) from direct_e
                else:
                    raise ValueError(
                        f"No versions found for model '{model_name}'. "
                        f"Train a model first using: quantcup ml train {model_name}"
                    )

            # Resolve version tag
            if version == 'latest':
                # Check if 'latest' is a key in versions (legacy) or a pointer
                if 'latest' in versions and isinstance(versions['latest'], str):
                     version = versions['latest']
                elif 'latest' not in versions:
                     # Fallback: check if there is a 'latest' folder in the bucket
                     # This handles the case where versions.json exists but doesn't have a 'latest' pointer
                     # but the file structure has a latest folder
                     pass

            if version == 'latest' and version not in versions:
                 # Try direct load for latest if resolution failed
                 direct_path = f"ml/models/{model_name}/latest/model.joblib"
                 logger.info(f"Resolving 'latest' failed, attempting direct load from {direct_path}")
                 try:
                    assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                    response = bucket_adapter.s3_client.get_object(
                        Bucket=bucket_adapter.bucket_name,
                        Key=direct_path
                    )
                    model_bytes = response['Body'].read()
                    buffer = io.BytesIO(model_bytes)
                    model = joblib.load(buffer)
                    logger.info(f"✓ Model loaded successfully from direct path")
                    return model, {'model_path': direct_path, 'created_at': 'unknown', 'metrics': {}}
                 except Exception:
                     raise ValueError(f"No 'latest' version found for model '{model_name}'")

            if version not in versions:
                available = [v for v in versions.keys() if v != 'latest']
                raise ValueError(
                    f"Model version '{version}' not found for '{model_name}'. "
                    f"Available versions: {available}"
                )
            
            # Get version metadata
            version_metadata = versions[version]
            
            # Handle legacy/corrupted versions where value is just the path string
            if isinstance(version_metadata, str):
                model_path = version_metadata
                version_metadata = {'model_path': model_path}
            else:
                model_path = version_metadata['model_path']
            
            # Load model from bucket
            logger.info(f"Loading model: {model_name} (version: {version})")
            assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
            
            try:
                response = bucket_adapter.s3_client.get_object(
                    Bucket=bucket_adapter.bucket_name,
                    Key=model_path
                )
                model_bytes = response['Body'].read()
                
                # Deserialize model
                buffer = io.BytesIO(model_bytes)
                model = joblib.load(buffer)
                
                logger.info(f"✓ Model loaded successfully")
                logger.info(f"   Version: {version}")
                logger.info(f"   Created: {version_metadata.get('created_at', 'unknown')}")
                # Handle potential string metadata for metrics
                metrics = version_metadata.get('metrics', {}) if isinstance(version_metadata, dict) else {}
                if not isinstance(metrics, dict):
                    metrics = {}
                logger.info(f"   Accuracy: {metrics.get('accuracy', 'unknown')}")
                
                return model, version_metadata
                
            except Exception as e:
                # If loading specific version fails, and we wanted latest, try direct path
                if version == 'latest' or (isinstance(versions, dict) and versions.get('latest') == version):
                    direct_path = f"ml/models/{model_name}/latest/model.joblib"
                    logger.warning(f"Failed to load resolved path {model_path}, attempting direct load from {direct_path}")
                    
                    try:
                        assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                        response = bucket_adapter.s3_client.get_object(
                            Bucket=bucket_adapter.bucket_name,
                            Key=direct_path
                        )
                        model_bytes = response['Body'].read()
                        buffer = io.BytesIO(model_bytes)
                        model = joblib.load(buffer)
                        
                        logger.info(f"✓ Model loaded successfully from direct path")
                        return model, {'model_path': direct_path, 'created_at': 'unknown', 'metrics': {}}
                    except Exception:
                        raise e # Raise original error if direct load also fails
                raise e

        except Exception as e:
            logger.error(f"Failed to load model version: {e}", exc_info=True)
            raise
    
    @staticmethod
    def list_versions(model_name: str) -> Dict[str, Dict[str, Any]]:
        """
        List all versions for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict mapping version tags to metadata
            
        Example:
            >>> versions = ModelVersionManager.list_versions('game_outcome')
            >>> for tag, meta in versions.items():
            ...     if tag != 'latest':
            ...         print(f"{tag}: {meta['metrics']['accuracy']:.3f}")
        """
        logger = get_logger('nflfastRv3.model_version_manager')
        
        try:
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Verify bucket is available
            if not bucket_adapter._is_available():
                logger.warning(f"Bucket storage not available")
                return {}
            
            # Load versions metadata
            versions_file = f"ml/models/{model_name}/versions.json"
            
            try:
                assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                response = bucket_adapter.s3_client.get_object(
                    Bucket=bucket_adapter.bucket_name,
                    Key=versions_file
                )
                versions_bytes = response['Body'].read()
                versions = json.loads(versions_bytes.decode('utf-8'))
                
                # Remove 'latest' pointer from listing
                latest_tag = versions.pop('latest', None)
                
                logger.info(f"Found {len(versions)} versions for {model_name}")
                if latest_tag:
                    logger.info(f"Latest version: {latest_tag}")
                
                return versions
                
            except Exception as e:
                logger.warning(f"No versions found for model '{model_name}': {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to list model versions: {e}")
            return {}
    
    @staticmethod
    def get_latest_version(model_name: str) -> Optional[str]:
        """
        Get the latest version tag for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Latest version tag or None if not found
            
        Example:
            >>> latest = ModelVersionManager.get_latest_version('game_outcome')
            >>> print(f"Latest version: {latest}")
        """
        logger = get_logger('nflfastRv3.model_version_manager')
        
        try:
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Verify bucket is available
            if not bucket_adapter._is_available():
                return None
            
            # Load versions metadata
            versions_file = f"ml/models/{model_name}/versions.json"
            
            try:
                assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
                response = bucket_adapter.s3_client.get_object(
                    Bucket=bucket_adapter.bucket_name,
                    Key=versions_file
                )
                versions_bytes = response['Body'].read()
                versions = json.loads(versions_bytes.decode('utf-8'))
                return versions.get('latest')
            except Exception:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest version: {e}")
            return None
    
    @staticmethod
    def cleanup_old_versions(model_name: Optional[str] = None, keep_count: int = 5) -> Dict[str, Any]:
        """
        Clean up old model versions in bucket, keeping most recent versions.
        
        Args:
            model_name: Specific model to clean up (None = all models)
            keep_count: Number of versions to keep per model (default: 5)
            
        Returns:
            dict: Result with deleted count and file list
            
        Example:
            >>> result = ModelVersionManager.cleanup_old_versions('game_outcome', keep_count=3)
            >>> print(f"Deleted {result['deleted_count']} old versions")
        """
        logger = get_logger('nflfastRv3.model_version_manager')
        
        try:
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Verify bucket is available
            if not bucket_adapter._is_available():
                logger.warning("Bucket not available - cannot cleanup models")
                return {'status': 'error', 'message': 'Bucket not available', 'deleted_count': 0}
            
            assert bucket_adapter.s3_client is not None and bucket_adapter.bucket_name is not None
            
            # Get all model versions
            if model_name:
                models_to_clean = [model_name]
            else:
                # List all models
                prefix = 'ml/models/'
                response = bucket_adapter.s3_client.list_objects_v2(
                    Bucket=bucket_adapter.bucket_name,
                    Prefix=prefix,
                    Delimiter='/'
                )
                models_to_clean = []
                for common_prefix in response.get('CommonPrefixes', []):
                    model = common_prefix['Prefix'].rstrip('/').split('/')[-1]
                    models_to_clean.append(model)
            
            deleted_count = 0
            deleted_files = []
            
            for model in models_to_clean:
                try:
                    # Load versions for this model
                    versions_file = f"ml/models/{model}/versions.json"
                    response = bucket_adapter.s3_client.get_object(
                        Bucket=bucket_adapter.bucket_name,
                        Key=versions_file
                    )
                    versions_bytes = response['Body'].read()
                    versions = json.loads(versions_bytes.decode('utf-8'))
                    
                    # Get all version tags (excluding 'latest' pointer)
                    latest_pointer = versions.pop('latest', None)
                    version_list = []
                    
                    for tag, metadata in versions.items():
                        if isinstance(metadata, dict) and 'created_at' in metadata:
                            version_list.append({
                                'tag': tag,
                                'created_at': metadata['created_at'],
                                'model_path': metadata.get('model_path', f"ml/models/{model}/{tag}/model.joblib")
                            })
                    
                    # Sort by creation date (newest first)
                    version_list.sort(key=lambda v: v['created_at'], reverse=True)
                    
                    # Delete old versions beyond keep_count
                    for old_version in version_list[keep_count:]:
                        try:
                            # Delete model file
                            bucket_adapter.s3_client.delete_object(
                                Bucket=bucket_adapter.bucket_name,
                                Key=old_version['model_path']
                            )
                            deleted_files.append(old_version['model_path'])
                            deleted_count += 1
                            
                            # Remove from versions.json
                            versions.pop(old_version['tag'], None)
                            
                            logger.info(f"Deleted old version: {model}/{old_version['tag']}")
                        except Exception as e:
                            logger.warning(f"Failed to delete {old_version['model_path']}: {e}")
                    
                    # Update versions.json if we deleted anything
                    if version_list[keep_count:]:
                        # Re-add latest pointer
                        if latest_pointer:
                            versions['latest'] = latest_pointer
                        
                        versions_json = json.dumps(versions, indent=2)
                        bucket_adapter.s3_client.put_object(
                            Bucket=bucket_adapter.bucket_name,
                            Key=versions_file,
                            Body=versions_json.encode('utf-8'),
                            ContentType='application/json'
                        )
                        logger.info(f"Updated versions.json for {model}")
                    
                except Exception as e:
                    logger.warning(f"Failed to cleanup versions for model {model}: {e}")
                    continue
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'deleted_files': deleted_files,
                'models_processed': len(models_to_clean)
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup model versions: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'deleted_count': 0
            }


__all__ = ['ModelVersionManager']