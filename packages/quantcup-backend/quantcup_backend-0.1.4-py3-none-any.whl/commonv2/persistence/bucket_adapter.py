"""
Bucket Adapter for S3/Sevalla Object Storage

Provides clean interface for bucket operations following V3 architecture constraints:
- Maximum 2 complexity points (DI + business logic)
- Simple dependency injection with fallbacks
- Supports both AWS S3 and Sevalla (S3-compatible)

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 3 (Infrastructure)
"""

import os
import io
import re
import tempfile
import uuid
from typing import Optional, Dict, Any, Union
import pandas as pd
import boto3
from botocore.client import Config, BaseClient
from botocore.exceptions import ClientError, NoCredentialsError
from commonv2 import get_logger

# Import for streaming parquet writes
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

# Module-level logger
_logger = get_logger('commonv2.persistence.bucket_adapter')


def normalize_timestamp(timestamp: str) -> str:
    """
    Normalize timestamp to consistent YYYYMMDDTHHMMSSZ format.
    
    Handles various ISO-8601 formats:
    - YYYY-MM-DDTHH:MM:SSZ (standard ISO with hyphens)
    - YYYY-MM-DDTHH:MM:SS+00:00 (timezone offset format)
    - YYYYMMDDTHHMMSSZ (compact ISO)
    - Mixed formats
    
    Args:
        timestamp: ISO-8601 timestamp string
        
    Returns:
        Normalized timestamp in YYYYMMDDTHHMMSSZ format
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    # First, normalize timezone suffix to 'Z' format (handles +00:00, +0000)
    timestamp = timestamp.replace('+00:00', 'Z').replace('+0000', 'Z')
    
    # Remove hyphens and colons
    clean = timestamp.replace('-', '').replace(':', '')
    
    # Ensure 'T' separator exists
    if 'T' not in clean:
        # If no T found, assume format is YYYYMMDDHHMMSS
        if len(clean) >= 14:
            clean = clean[:8] + 'T' + clean[8:]
        else:
            raise ValueError(f"Invalid timestamp format (missing date/time separator): {timestamp}")
    
    # Ensure 'Z' suffix
    if not clean.endswith('Z'):
        clean += 'Z'
    
    # Validate format: exactly 16 chars (8 date + T + 6 time + Z)
    if len(clean) != 16:
        raise ValueError(f"Invalid timestamp length after normalization: {clean} (expected 16 chars)")
    
    return clean


def extract_date_part(timestamp: str) -> str:
    """
    Extract YYYYMMDD date from any ISO-8601 timestamp format.
    
    Uses regex to handle both hyphenated and compact formats:
    - YYYY-MM-DD... → YYYYMMDD
    - YYYYMMDD... → YYYYMMDD
    
    Args:
        timestamp: ISO-8601 timestamp string
        
    Returns:
        Date in YYYYMMDD format
        
    Raises:
        ValueError: If date cannot be extracted
    """
    # Match YYYY-MM-DD or YYYYMMDD at start of string
    match = re.match(r'(\d{4})-?(\d{2})-?(\d{2})', timestamp)
    if not match:
        raise ValueError(f"Cannot extract date from timestamp: {timestamp}")
    
    # Join matched groups without separators
    return ''.join(match.groups())


class BucketAdapter:
    """
    S3/Sevalla bucket operations adapter.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    - DI with fallback (1 point)
    - Business logic (1 point)
    
    Supports both standard AWS S3 and Sevalla object storage.
    """
    
    def __init__(self, config=None, logger=None):
        """
        Initialize bucket adapter with optional configuration.
        
        Args:
            config: Optional bucket configuration dict
            logger: Optional logger instance (uses module logger if not provided)
        """
        # Simple DI with fallback (1 complexity point)
        self.config = config or self._get_bucket_config()
        self.logger = logger or _logger  # DI with module-level fallback
        
        # Business logic (1 complexity point)
        self.s3_client: Optional[BaseClient] = self._create_s3_client()
        self.bucket_name: Optional[str] = self.config.get('bucket_name')
        
        if not self.bucket_name:
            self.logger.warning("No bucket name configured - bucket operations will be disabled")
    
    def _get_env_with_fallbacks(self, *var_names: str) -> Optional[str]:
        """
        Get environment variable value checking multiple names in priority order.
        """
        for var_name in var_names:
            value = os.getenv(var_name)
            if value and value.strip():
                return value.strip()
        return None

    def _get_bucket_config(self) -> Dict[str, Any]:
        """
        Get bucket configuration from environment variables.
        """
        config = {
            'bucket_name': self._get_env_with_fallbacks(
                'BUCKET_NAME', 
                'SEVALLA_BUCKET_NAME'
            ),
            'endpoint_url': self._get_env_with_fallbacks(
                'BUCKET_ENDPOINT_URL', 
                'SEVALLA_BUCKET_ENDPOINT'
            ),
            'access_key': self._get_env_with_fallbacks(
                'BUCKET_ACCESS_KEY', 
                'AWS_ACCESS_KEY_ID',
                'SEVALLA_BUCKET_ACCESS_KEY_ID'
            ),
            'secret_key': self._get_env_with_fallbacks(
                'BUCKET_SECRET_KEY', 
                'AWS_SECRET_ACCESS_KEY',
                'SEVALLA_BUCKET_SECRET_ACCESS_KEY'
            ),
            'region': self._get_env_with_fallbacks(
                'BUCKET_REGION', 
                'SEVALLA_BUCKET_REGION'
            ) or 'us-east-1'
        }
        
        return config
    
    def _create_s3_client(self) -> Optional[BaseClient]:
        """
        Create S3 client for AWS S3 or Sevalla.
        """
        try:
            # Check if this is Sevalla (has custom endpoint)
            if self.config.get('endpoint_url'):
                self.logger.info(f"Using Sevalla object storage: {self.config['endpoint_url']}")
                return boto3.client(
                    's3',
                    endpoint_url=self.config['endpoint_url'],
                    aws_access_key_id=self.config['access_key'],
                    aws_secret_access_key=self.config['secret_key'],
                    config=Config(signature_version='s3v4'),
                    region_name=self.config.get('region', 'us-east-1')
                )
            else:
                # Standard AWS S3
                self.logger.info("Using AWS S3")
                client_kwargs = {
                    'service_name': 's3'
                }
                
                if self.config.get('access_key') and self.config.get('secret_key'):
                    client_kwargs.update({
                        'aws_access_key_id': self.config['access_key'],
                        'aws_secret_access_key': self.config['secret_key']
                    })
                
                if self.config.get('region'):
                    client_kwargs['region_name'] = self.config['region']
                
                return boto3.client(**client_kwargs)
                
        except Exception as e:
            self.logger.error(f"Failed to create S3 client: {e}")
            return None
    
    def _df_to_parquet_bytes(self, df: pd.DataFrame) -> bytes:
        """
        Convert DataFrame to parquet bytes safely.
        """
        if not HAS_PYARROW:
            raise RuntimeError("pyarrow not installed; cannot write parquet bytes safely")
        
        buf = io.BytesIO()
        df.to_parquet(buf, index=False, engine='pyarrow')
        return buf.getvalue()
    
    def store_data(self, df: pd.DataFrame, table_name: str, schema: str = 'raw_nflfastr',
                   partition_by_year: bool = False, timestamp: Optional[str] = None,
                   part_id: Optional[str] = None) -> bool:
        """
        Store DataFrame in bucket (primary storage).
        """
        if not self._is_available():
            self.logger.warning(f"Bucket not available - skipping storage for {table_name}")
            return False
        
        try:
            # Priority 1: Timestamp-partitioned storage
            if timestamp:
                try:
                    normalized_ts = normalize_timestamp(timestamp)
                    date_part = extract_date_part(timestamp)
                except ValueError as e:
                    self.logger.error(f"Invalid timestamp format: {e}")
                    return False
                
                if part_id:
                    key = f"{schema}/{table_name}/date={date_part}/timestamp={normalized_ts}/part={part_id}/data.parquet"
                else:
                    part_uuid = uuid.uuid4().hex[:8]
                    key = f"{schema}/{table_name}/date={date_part}/timestamp={normalized_ts}/data_{part_uuid}.parquet"
                
                self.logger.debug(f"Storing {len(df):,} rows with timestamp partitioning: {key}")
                body = self._df_to_parquet_bytes(df)
                
                assert self.s3_client is not None and self.bucket_name is not None
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=body,
                    ContentType='application/octet-stream'
                )
                return True
            
            # Priority 2: Year-partitioned storage
            elif partition_by_year and 'season' in df.columns:
                return self._store_partitioned_by_year(df, table_name, schema)
            
            # Priority 3: Single-file storage
            else:
                key = f"{schema}/{table_name}/data.parquet"
                self.logger.debug(f"Storing {len(df):,} rows to bucket: {key}")
                body = self._df_to_parquet_bytes(df)
                
                assert self.s3_client is not None and self.bucket_name is not None
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=body,
                    ContentType='application/octet-stream'
                )
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to store {table_name} in bucket: {e}")
            return False
    
    def _store_partitioned_by_year(self, df: pd.DataFrame, table_name: str, schema: str) -> bool:
        """
        Store DataFrame partitioned by year.
        """
        if 'season' not in df.columns:
            self.logger.error(f"Cannot partition {table_name} by year - no 'season' column")
            return False
        
        try:
            years = sorted(df['season'].unique())
            success_count = 0
            for year in years:
                year_df = df[df['season'] == year]
                key = f"{schema}/{table_name}/season={year}/{table_name}_{year}.parquet"
                body = self._df_to_parquet_bytes(year_df)
                
                assert self.s3_client is not None and self.bucket_name is not None
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=body,
                    ContentType='application/octet-stream'
                )
                success_count += 1
            return success_count == len(years)
        except Exception as e:
            self.logger.error(f"Failed partitioned storage for {table_name}: {e}")
            return False
    
    def store_data_streaming(self, df: pd.DataFrame, table_name: str, schema: str = 'raw_nflfastr',
                           year: Optional[int] = None, rows_per_group: int = 100_000) -> int:
        """
        Store DataFrame in bucket using streaming parquet writes.
        """
        if not self._is_available():
            return 0
        
        if not HAS_PYARROW:
            return len(df) if self.store_data(df, table_name, schema) else 0
        
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            if year:
                key = f"{schema}/{table_name}/season={year}/{table_name}_{year}.parquet"
            else:
                key = f"{schema}/{table_name}/data.parquet"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as temp_file:
                temp_path = temp_file.name
            
            try:
                total_rows = len(df)
                written_rows = 0
                pa_schema = pa.Schema.from_pandas(df, preserve_index=False)
                
                with pq.ParquetWriter(temp_path, pa_schema) as writer:
                    for start in range(0, total_rows, rows_per_group):
                        end = min(start + rows_per_group, total_rows)
                        batch_df = df.iloc[start:end].copy()
                        batch_table = pa.Table.from_pandas(batch_df, preserve_index=False)
                        writer.write_table(batch_table)
                        written_rows += len(batch_df)
                        del batch_df, batch_table
                
                assert self.s3_client is not None and self.bucket_name is not None
                with open(temp_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=key,
                        Body=f,
                        ContentType='application/octet-stream'
                    )
                return written_rows
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        except Exception as e:
            self.logger.error(f"Failed to stream {table_name} to bucket: {e}")
            return 0

    def upload_file(self, local_path: str, bucket_key: str) -> bool:
        """Upload a local file to bucket."""
        if not self._is_available():
            return False
        try:
            assert self.s3_client is not None and self.bucket_name is not None
            with open(local_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=bucket_key,
                    Body=f,
                    ContentType='application/octet-stream'
                )
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload file {local_path} to {bucket_key}: {e}")
            return False
    
    def read_data(self, table_name: str, schema: str = 'raw_nflfastr', filters=None, columns=None) -> pd.DataFrame:
        """Read DataFrame from bucket."""
        if not self._is_available():
            return pd.DataFrame()
        
        try:
            partition_year = None
            if filters:
                for col, op, val in filters:
                    if col == 'season' and op == '==':
                        partition_year = val
                        break
            
            if table_name == 'play_by_play' and partition_year:
                key = f"{schema}/{table_name}/season={partition_year}/{table_name}_{partition_year}.parquet"
                return self._read_single_parquet(key, filters, columns)

            key = f"{schema}/{table_name}/data.parquet"
            return self._read_single_parquet(key, filters, columns)
        except Exception as e:
            self.logger.error(f"Failed to read {table_name} from bucket: {e}")
            return pd.DataFrame()

    def _read_single_parquet(self, key: str, filters=None, columns=None) -> pd.DataFrame:
        """Read a single parquet file from bucket."""
        try:
            assert self.s3_client is not None and self.bucket_name is not None
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            parquet_bytes = response['Body'].read()
            
            if filters or columns:
                df = pd.read_parquet(
                    io.BytesIO(parquet_bytes),
                    engine='pyarrow',
                    filters=filters,
                    columns=columns
                )
            else:
                df = pd.read_parquet(io.BytesIO(parquet_bytes), engine='pyarrow')
            return df
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                self.logger.error(f"Failed to read {key}: {e}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to read {key}: {e}")
            return pd.DataFrame()
    
    def list_tables(self, schema: str = 'raw_nflfastr') -> list:
        """List tables available in bucket."""
        if not self._is_available():
            return []
        try:
            assert self.s3_client is not None and self.bucket_name is not None
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{schema}/",
                Delimiter='/'
            )
            tables = []
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    prefix_path = prefix['Prefix'].rstrip('/')
                    table_name = prefix_path.split('/')[-1]
                    tables.append(table_name)
            return tables
        except Exception as e:
            self.logger.error(f"Failed to list tables in bucket: {e}")
            return []

    def list_files(self, prefix: str = '') -> list:
        """List all files in the bucket."""
        if not self._is_available():
            return []
        try:
            assert self.s3_client is not None and self.bucket_name is not None
            files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in bucket: {e}")
            return []
    
    def list_timestamps(self, table_name: str, schema: str = 'raw_nflfastr') -> list:
        """List all timestamps for a timestamp-partitioned table."""
        if not self._is_available():
            return []
        try:
            prefix = f"{schema}/{table_name}/"
            assert self.s3_client is not None and self.bucket_name is not None
            timestamps = set()
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if '/timestamp=' in key:
                            parts = key.split('/timestamp=')
                            if len(parts) >= 2:
                                timestamp_part = parts[1].split('/')[0]
                                timestamps.add(timestamp_part)
            return sorted(list(timestamps))
        except Exception as e:
            self.logger.error(f"Failed to list timestamps for {table_name}: {e}")
            return []
    
    def read_timestamp_partitioned_table(self, table_name: str, schema: str, max_rows: int = 100) -> pd.DataFrame:
        """Read timestamp-partitioned table."""
        prefix = f"{schema}/{table_name}/"
        files = self.list_files(prefix)
        parquet_files = [f for f in files if f.endswith('.parquet')]
        if not parquet_files:
            return pd.DataFrame()
        
        dfs = []
        total_rows = 0
        for file_key in parquet_files:
            if total_rows >= max_rows:
                break
            try:
                df_part = self._read_single_parquet(file_key)
                if not df_part.empty:
                    dfs.append(df_part)
                    total_rows += len(df_part)
            except Exception as e:
                self.logger.warning(f"Failed to read partition {file_key}: {e}")
        
        if not dfs:
            return pd.DataFrame()
        combined = pd.concat(dfs, ignore_index=True)
        return combined.head(max_rows)

    def table_exists(self, table_name: str, schema: str = 'raw_nflfastr',
                     check_partitioned: bool = True) -> bool:
        """Check if table exists in bucket."""
        if not self._is_available():
            return False
        try:
            key = f"{schema}/{table_name}/data.parquet"
            assert self.s3_client is not None and self.bucket_name is not None
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            if check_partitioned:
                try:
                    prefix = f"{schema}/{table_name}/"
                    assert self.s3_client is not None and self.bucket_name is not None
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=prefix,
                        MaxKeys=1
                    )
                    return response.get('KeyCount', 0) > 0
                except Exception:
                    return False
            return False
        except Exception:
            return False
    
    def _is_available(self) -> bool:
        """Check if bucket operations are available."""
        return (
            self.s3_client is not None and 
            self.bucket_name is not None and
            self.bucket_name.strip() != ""
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get bucket adapter status."""
        status = {
            'available': self._is_available(),
            'bucket_name': self.bucket_name,
            'endpoint_url': self.config.get('endpoint_url'),
            'has_credentials': bool(self.config.get('access_key')),
            'client_created': self.s3_client is not None
        }
        if self._is_available():
            try:
                assert self.s3_client is not None and self.bucket_name is not None
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                status['bucket_accessible'] = True
            except Exception as e:
                status['bucket_accessible'] = False
                status['bucket_error'] = str(e)
        return status


def get_bucket_adapter(config=None, logger=None) -> BucketAdapter:
    """Factory function to create bucket adapter."""
    return BucketAdapter(config=config, logger=logger)


__all__ = ['BucketAdapter', 'get_bucket_adapter', 'normalize_timestamp', 'extract_date_part']
