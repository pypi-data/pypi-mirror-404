"""
Centralized logging configuration for quantcup-simple projects.

Provides standardized logging setup across all modules with consistent
formatting, rotation, and level management.

Enhanced with command session timestamped folders for organized logging.
"""

import logging
import logging.handlers
import os
import sys
import threading
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Load .env file variables into environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass


class LazyFileHandler(logging.Handler):
    """
    A file handler that only creates the log file when the first log record is emitted.
    
    This prevents empty log files from being created for modules that set up loggers
    but never actually log anything during execution.
    """
    
    def __init__(self, filename, mode='a', encoding=None, maxBytes=10*1024*1024, backupCount=5):
        """
        Initialize the lazy file handler.
        
        Args:
            filename: Log file path
            mode: File mode (default 'a' for append)
            encoding: File encoding
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self._handler = None
        self._lock = threading.Lock()
    
    def _ensure_handler(self):
        """Create the actual file handler if it doesn't exist yet."""
        if self._handler is None:
            with self._lock:
                if self._handler is None:
                    # Ensure directory exists
                    Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create the actual rotating file handler
                    self._handler = logging.handlers.RotatingFileHandler(
                        self.filename,
                        mode=self.mode,
                        maxBytes=self.maxBytes,
                        backupCount=self.backupCount,
                        encoding=self.encoding
                    )
                    
                    # Copy our formatter to the actual handler
                    if hasattr(self, 'formatter') and self.formatter:
                        self._handler.setFormatter(self.formatter)
                    
                    # Copy our level to the actual handler
                    self._handler.setLevel(self.level)
    
    def emit(self, record):
        """
        Emit a record. Creates the file handler on first emission.
        
        Args:
            record: LogRecord to emit
        """
        try:
            self._ensure_handler()
            if self._handler:
                self._handler.emit(record)
        except Exception:
            self.handleError(record)
    
    def setFormatter(self, fmt):
        """Set formatter on both this handler and the actual handler if it exists."""
        super().setFormatter(fmt)
        if self._handler:
            self._handler.setFormatter(fmt)
    
    def setLevel(self, level):
        """Set level on both this handler and the actual handler if it exists."""
        super().setLevel(level)
        if self._handler:
            self._handler.setLevel(level)
    
    def close(self):
        """Close the actual handler if it exists."""
        try:
            if self._handler:
                self._handler.close()
        except Exception:
            pass
        finally:
            super().close()
    
    def flush(self):
        """Flush the actual handler if it exists."""
        if self._handler:
            self._handler.flush()


class LoggingSessionManager:
    """
    Manage command execution sessions for organized timestamped logging.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Thread-safe singleton for session coordination.
    
    ENHANCED: Phase 1 - Contextual Logging with Correlation IDs
    """
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.session_folder = None
        self.session_active = False
        self.session_name = None
        self._initialized = False
        self._api_context = None  # For lazy API session naming
        self._pending_session = False  # Flag for sessions waiting for context
        
        # ENHANCED: Correlation tracking for forensic analysis
        self.correlation_id = None  # Session-wide correlation ID
        self.execution_context = {}  # Context propagation for debugging
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def set_api_context(self, context):
        """
        Set API context for lazy session naming.
        
        This allows API functions to specify their context (e.g., 'ml_pipeline', 'data_pipeline')
        before session initialization occurs, enabling specific session folder naming.
        
        Args:
            context (str): API context name (e.g., 'ml_pipeline', 'data_pipeline', 'analytics')
        """
        with self._lock:
            self._api_context = context
            
            # If we have a pending generic session, rename it to specific session
            if self._pending_session and self.session_active and self.session_folder:
                # Extract timestamp from current session name
                if self.session_name and 'nflfastrv3_api_generic_' in self.session_name:
                    timestamp = self.session_name.split('_')[-2:]  # Get last two parts (date_time)
                    timestamp_str = '_'.join(timestamp)
                    
                    # Create new specific session name
                    new_session_name = f"nflfastrv3_api_{context}_{timestamp_str}"
                    new_session_folder = self.session_folder.parent / new_session_name
                    
                    try:
                        # Rename the session folder
                        if self.session_folder.exists():
                            self.session_folder.rename(new_session_folder)
                            self.session_name = new_session_name
                            self.session_folder = new_session_folder
                            self._pending_session = False
                            
                            # Update session.log with the context change
                            session_log = new_session_folder / 'session.log'
                            if session_log.exists():
                                with open(session_log, 'a') as f:
                                    f.write(f"[{datetime.now()}] Session renamed to specific context: {context}\n")
                    except Exception:
                        # If renaming fails, just continue with generic session
                        pass
    
    def get_session_log_dir(self):
        """
        Get the appropriate log directory for current session.
        
        Returns:
            Path: Session folder if active, otherwise base logs folder
        """
        if not self._initialized:
            self._initialize_session()
        
        if self.session_active and self.session_folder:
            return self.session_folder
        else:
            return self._get_project_logs_dir()
    
    def get_execution_context(self):
        """
        Get current execution context for logging correlation.
        
        ENHANCED: Phase 1 - Context propagation for forensic analysis
        
        Returns:
            dict: Execution context with correlation ID and session info
        """
        if not self._initialized:
            self._initialize_session()
        
        if self.session_active and self.execution_context:
            return self.execution_context.copy()
        else:
            # Return minimal context for non-session logging
            return {
                'session_id': 'no_session',
                'correlation_id': 'no_correlation',
                'start_time': datetime.now().isoformat()
            }
    
    def get_session_output_dir(self):
        """
        Get session directory for saving any command outputs (reports, files, etc.).
        
        This allows scripts to save all outputs (logs, reports, data files) 
        in the same timestamped session folder for complete organization.
        
        Returns:
            Path: Session folder if active, otherwise current directory
        """
        if not self._initialized:
            self._initialize_session()
        
        if self.session_active and self.session_folder:
            # Ensure the session folder exists
            self.session_folder.mkdir(parents=True, exist_ok=True)
            return self.session_folder
        else:
            # Return current directory for backward compatibility
            return Path('.')
    
    def _get_project_logs_dir(self):
        """
        Find and return the main project logs directory.
        
        This ensures all logs go to the main project logs folder regardless
        of the current working directory when the command is executed.
        
        Returns:
            Path: Main project logs directory
        """
        # Start from current working directory and walk up to find project root
        current = Path.cwd()
        
        # Look for project indicators (prioritized by reliability)
        project_indicators = [
            '.git',           # Git repository root
            'pyproject.toml', # Python project file
            'quantcup',       # Main quantcup module directory
            'commonv2',       # CommonV2 module directory
            'nflfastRv3',     # NFLfastRv3 module directory
        ]
        
        # Check current directory and all parent directories
        for parent in [current] + list(current.parents):
            for indicator in project_indicators:
                if (parent / indicator).exists():
                    # Found project root, return its logs directory
                    logs_dir = parent / 'logs'
                    return logs_dir
        
        # Fallback: if no project indicators found, use current directory logs
        # This maintains backward compatibility
        return current / 'logs'
    
    def _initialize_session(self):
        """Initialize session based on command detection."""
        self._initialized = True
        
        # Buffer debug info during session detection
        debug_buffer = []
        debug_buffer.append(f"\n[{datetime.now()}] Session initialization starting\n")
        debug_buffer.append(f"LOG_TO_FILES: {os.getenv('LOG_TO_FILES', 'not set')}\n")
        
        script_name, is_command = self._detect_command_session(debug_buffer)
        
        debug_buffer.append(f"Detection result: script_name={script_name}, is_command={is_command}\n")
        
        # Check if we should create a session
        log_to_files_enabled = os.getenv("LOG_TO_FILES", "0") == "1"
        is_quantcup_session = is_command and script_name and script_name.startswith("quantcup_")
        is_nflfastrv3_session = is_command and script_name and script_name.startswith("nflfastrv3_")
        
        debug_buffer.append(f"log_to_files_enabled: {log_to_files_enabled}\n")
        debug_buffer.append(f"is_quantcup_session: {is_quantcup_session}\n")
        debug_buffer.append(f"is_nflfastrv3_session: {is_nflfastrv3_session}\n")
        
        # Create sessions when:
        # 1. LOG_TO_FILES is explicitly enabled, OR
        # 2. We detect quantcup CLI execution (always create sessions for unified CLI), OR
        # 3. We detect nflfastRv3 CLI execution (always create sessions for nflfastRv3)
        should_create_session = log_to_files_enabled or is_quantcup_session or is_nflfastrv3_session
        
        if not should_create_session:
            debug_buffer.append("Session creation conditions not met, skipping\n")
            # Write debug info to global file since no session created
            self._write_debug_info(debug_buffer, use_global=True)
            return
        
        if is_command and script_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.session_name = f"{script_name}_{timestamp}"
            # Use project-aware logs directory instead of relative path
            project_logs_dir = self._get_project_logs_dir()
            self.session_folder = project_logs_dir / self.session_name
            self.session_active = True
            
            # ENHANCED: Generate correlation ID for session tracking
            import uuid
            self.correlation_id = str(uuid.uuid4())[:8]  # Short correlation ID
            
            # ENHANCED: Initialize execution context for debugging
            self.execution_context = {
                'session_id': self.session_name,
                'correlation_id': self.correlation_id,
                'start_time': datetime.now().isoformat(),
                'script_name': script_name,
                'command_args': sys.argv[1:] if len(sys.argv) > 1 else []
            }
            
            debug_buffer.append(f"Session created: {self.session_name}\n")
            debug_buffer.append(f"Session folder: {self.session_folder}\n")
            debug_buffer.append(f"Correlation ID: {self.correlation_id}\n")
            
            # Write debug info to session.log in the session folder
            self._write_debug_info(debug_buffer, use_global=False)
            
            # Schedule automatic log cleanup with configurable retention
            self._schedule_cleanup()
        else:
            debug_buffer.append("No session created - using default logs folder\n")
            # Write debug info to global file since no session created
            self._write_debug_info(debug_buffer, use_global=True)
    
    def _write_debug_info(self, debug_buffer, use_global=False):
        """
        Write debug info to appropriate location.
        
        Args:
            debug_buffer (list): List of debug messages to write
            use_global (bool): If True, write to global debug file; otherwise use session.log
        """
        try:
            if use_global or not (self.session_active and self.session_folder):
                # Write to global debug file in project logs directory
                project_logs_dir = self._get_project_logs_dir()
                debug_file = project_logs_dir / 'session_debug.log'
            else:
                # Write to session.log in the session folder
                self.session_folder.mkdir(parents=True, exist_ok=True)
                debug_file = self.session_folder / 'session.log'
            
            # Ensure parent directory exists
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write all buffered debug info
            with open(debug_file, 'a') as f:
                for line in debug_buffer:
                    f.write(line)
        except Exception:
            # If debug writing fails, don't break logging - continue silently
            pass
    
    def _schedule_cleanup(self):
        """Schedule automatic cleanup of old logs (runs in background)."""
        try:
            # Get retention period from environment with sensible default
            retention_days = int(os.getenv("LOG_RETENTION_DAYS", "14"))
            
            # Run cleanup in a separate thread to avoid blocking session initialization
            cleanup_thread = threading.Thread(
                target=self._cleanup_old_logs, 
                args=(retention_days,),
                daemon=True  # Don't prevent program exit
            )
            cleanup_thread.start()
        except Exception:
            # If cleanup fails, don't break logging - just continue silently
            pass
    
    def _cleanup_old_logs(self, retention_days):
        """
        Clean up log files and session folders older than retention period.
        
        Args:
            retention_days (int): Number of days to retain logs
        """
        try:
            # Use project-aware logs directory
            logs_dir = self._get_project_logs_dir()
            if not logs_dir.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            cleanup_logger = logging.getLogger('commonv2.log_retention')
            deleted_count = 0
            
            # Clean up session folders (timestamped directories)
            for item in logs_dir.iterdir():
                if item.is_dir() and self._is_session_folder(item):
                    try:
                        # Check folder modification time
                        folder_time = datetime.fromtimestamp(item.stat().st_mtime)
                        if folder_time < cutoff_time:
                            shutil.rmtree(item)
                            deleted_count += 1
                            cleanup_logger.info(f"Cleaned up old session folder: {item.name}")
                    except Exception:
                        # If we can't delete a folder (in use, permissions), skip it
                        continue
            
            # Clean up individual log files (legacy logs)
            for item in logs_dir.iterdir():
                if item.is_file() and self._is_log_file(item):
                    try:
                        # Check file modification time
                        file_time = datetime.fromtimestamp(item.stat().st_mtime)
                        if file_time < cutoff_time:
                            item.unlink()
                            deleted_count += 1
                            cleanup_logger.info(f"Cleaned up old log file: {item.name}")
                    except Exception:
                        # If we can't delete a file (in use, permissions), skip it
                        continue
            
            if deleted_count > 0:
                cleanup_logger.info(f"Log retention cleanup completed: {deleted_count} items removed (>{retention_days} days old)")
                
        except Exception:
            # If entire cleanup fails, fail silently to not break logging
            pass
    
    def _is_session_folder(self, path):
        """
        Check if a directory is a session folder we created.
        
        Pattern: script_name_YYYYMMDD_HHMMSS
        Examples: performance_benchmark_20251018_161534, cli_data_process_20251015_143022
        """
        if not path.is_dir():
            return False
        
        # Match pattern: script_name_YYYYMMDD_HHMMSS
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*_\d{8}_\d{6}$'
        return re.match(pattern, path.name) is not None
    
    def _is_log_file(self, path):
        """
        Check if a file is a log file we should manage.
        
        Patterns: *.log files in logs directory
        """
        if not path.is_file():
            return False
        
        return path.suffix == '.log'
    
    def _detect_command_session(self, debug_buffer):
        """
        Detect if we're in a main command execution.
        
        Args:
            debug_buffer (list): Buffer to append debug info to
        
        Returns:
            tuple: (script_name, is_command_session)
        """
        try:
            debug_buffer.append(f"[{datetime.now()}] Session detection starting\n")
            debug_buffer.append(f"sys.argv: {sys.argv}\n")
            
            # First, check if this is an API call (higher priority than main module detection)
            api_session = self._detect_api_call(debug_buffer)
            if api_session[1]:  # If is_api_session is True
                return api_session
            
            main_module = sys.modules.get('__main__')
            main_file = None
            main_path = None
            
            # Handle both direct script execution and module execution (python -m module)
            if main_module and hasattr(main_module, '__file__') and main_module.__file__:
                main_file = main_module.__file__
                main_path = Path(main_file)
                debug_buffer.append(f"main_path: {main_path}\n")
                debug_buffer.append(f"path_parts: {main_path.parts}\n")
            elif len(sys.argv) >= 1 and sys.argv[0] == '-m':
                # Module execution: python -m nflfastRv3.cli.main
                debug_buffer.append("Module execution detected (python -m)\n")
                
                # Check if this is nflfastRv3 CLI execution based on multiple indicators
                main_module_name = getattr(main_module, '__name__', '') if main_module else ''
                main_module_spec = getattr(main_module, '__spec__', None)
                main_module_spec_name = main_module_spec.name if main_module_spec else ''
                main_module_package = getattr(main_module, '__package__', '') if main_module else ''
                
                debug_buffer.append(f"main_module_name: {main_module_name}\n")
                debug_buffer.append(f"main_module_spec_name: {main_module_spec_name}\n")
                debug_buffer.append(f"main_module_package: {main_module_package}\n")
                
                # Check for nflfastRv3 CLI patterns in any of the module identifiers (handle None values)
                is_nflfastrv3_module = (
                    (main_module_spec_name and 'nflfastRv3' in main_module_spec_name) or
                    (main_module_package and 'nflfastRv3' in main_module_package) or
                    (main_module_spec and 'nflfastRv3' in str(main_module_spec))
                )
                
                is_cli_module = (
                    (main_module_spec_name and 'cli' in main_module_spec_name) or
                    (main_module_package and 'cli' in main_module_package) or
                    (main_module_spec and 'cli' in str(main_module_spec))
                )
                
                debug_buffer.append(f"is_nflfastrv3_module: {is_nflfastrv3_module}\n")
                debug_buffer.append(f"is_cli_module: {is_cli_module}\n")
                
                # Additional heuristic: Check if we're executing nflfastRv3 CLI based on loaded modules
                is_nflfastrv3_execution = False
                try:
                    # Get all loaded modules for debugging
                    all_modules = list(sys.modules.keys())
                    nflfastrv3_modules = [name for name in all_modules if 'nflfastRv3' in name]
                    nflfastrv3_cli_modules = [name for name in nflfastrv3_modules if 'cli' in name]
                    
                    debug_buffer.append(f"All loaded modules count: {len(all_modules)}\n")
                    debug_buffer.append(f"nflfastRv3 modules loaded: {nflfastrv3_modules}\n")
                    debug_buffer.append(f"nflfastRv3 CLI modules loaded: {nflfastrv3_cli_modules}\n")
                    
                    # Check if ANY nflfastRv3 modules are loaded (not just CLI)
                    if nflfastrv3_modules:
                        is_nflfastrv3_execution = True
                        debug_buffer.append(f"nflfastRv3 execution detected via loaded modules\n")
                    
                    # Fallback: Check call stack
                    if not is_nflfastrv3_execution:
                        import inspect
                        frame = inspect.currentframe()
                        while frame:
                            frame_filename = frame.f_code.co_filename
                            if 'nflfastRv3' in frame_filename and 'cli' in frame_filename:
                                is_nflfastrv3_execution = True
                                debug_buffer.append(f"Found nflfastRv3 CLI in call stack: {frame_filename}\n")
                                break
                            frame = frame.f_back
                except Exception as e:
                    debug_buffer.append(f"nflfastRv3 execution detection failed: {e}\n")
                
                debug_buffer.append(f"is_nflfastrv3_execution: {is_nflfastrv3_execution}\n")
                
                if (is_nflfastrv3_module and is_cli_module) or is_nflfastrv3_execution:
                    debug_buffer.append("NFLfastRv3 CLI module execution detected!\n")
                    # Extract command from sys.argv: ['-m', 'system', 'info', '--detailed']
                    if len(sys.argv) >= 3:  # ['-m', 'command', 'subcommand']
                        command = sys.argv[1]
                        subcommand = sys.argv[2]
                        return f"nflfastrv3_{command}_{subcommand}", True
                    elif len(sys.argv) >= 2:  # ['-m', 'command']
                        command = sys.argv[1]
                        return f"nflfastrv3_{command}", True
                    else:
                        return "nflfastrv3", True
            else:
                debug_buffer.append("No main module, __file__ attribute, or recognizable module execution\n")
                return None, False
            
            if not main_path:
                debug_buffer.append("No main_path available\n")
                # At this point, if we haven't returned already, we don't have a valid main_path
                # but we might have handled module execution above
                return None, False
            
            # Pattern 1: QuantCup Unified CLI
            # python -m quantcup -> quantcup/__main__.py or quantcup/cli.py
            # OR installed binary -> /path/to/bin/quantcup
            path_parts = main_path.parts
            is_quantcup_cli = (
                len(path_parts) >= 2 and 
                path_parts[-2] == 'quantcup' and 
                main_path.name in ['__main__.py', 'cli.py']
            ) or (
                len(path_parts) >= 1 and 
                path_parts[-1] == 'quantcup.py'
            ) or (
                len(path_parts) >= 1 and 
                main_path.name == 'quantcup'  # Installed binary
            )
            
            if is_quantcup_cli:
                debug_buffer.append("QuantCup CLI detected!\n")
                debug_buffer.append(f"sys.argv length: {len(sys.argv)}\n")
                for i, arg in enumerate(sys.argv):
                    debug_buffer.append(f"sys.argv[{i}]: {arg}\n")
                
                # Extract command structure from sys.argv
                # Examples: quantcup nflfastr pipeline, quantcup nflfastrv3 data process, etc.
                if len(sys.argv) >= 4:  # [script, module, command, subcommand]
                    module_name = sys.argv[1]
                    command = sys.argv[2]
                    subcommand = sys.argv[3]
                    session_name = f"quantcup_{module_name}_{command}_{subcommand}"
                    debug_buffer.append(f"Creating session: {session_name}\n")
                    # Add additional subcommand if present
                    if len(sys.argv) >= 5 and not sys.argv[4].startswith('-'):
                        sub_subcommand = sys.argv[4]
                        session_name = f"quantcup_{module_name}_{command}_{subcommand}_{sub_subcommand}"
                        debug_buffer.append(f"Extended session: {session_name}\n")
                        return session_name, True
                    else:
                        return session_name, True
                elif len(sys.argv) >= 3:  # [script, module, command]
                    module_name = sys.argv[1]
                    command = sys.argv[2]
                    session_name = f"quantcup_{module_name}_{command}"
                    debug_buffer.append(f"Creating session: {session_name}\n")
                    return session_name, True
                elif len(sys.argv) >= 2:  # [script, module]
                    module_name = sys.argv[1]
                    session_name = f"quantcup_{module_name}"
                    debug_buffer.append(f"Creating session: {session_name}\n")
                    return session_name, True
                else:
                    debug_buffer.append("Creating session: quantcup\n")
                    return "quantcup", True
            
            # Pattern 2: NFLfastRv3 CLI execution
            # python -m nflfastRv3.cli -> nflfastRv3/cli/__main__.py or main.py
            is_nflfastrv3_cli = (
                'nflfastRv3' in path_parts and 
                ('cli' in path_parts or main_path.name in ['__main__.py', 'main.py']) and
                not is_quantcup_cli  # Not executed via quantcup
            )
            if is_nflfastrv3_cli:
                # Extract CLI command details from sys.argv
                if len(sys.argv) >= 3:  # [script, command, subcommand]
                    command = sys.argv[1]
                    subcommand = sys.argv[2]
                    return f"nflfastrv3_{command}_{subcommand}", True
                elif len(sys.argv) >= 2:  # [script, command]
                    command = sys.argv[1]
                    return f"nflfastrv3_{command}", True
                else:
                    return "nflfastrv3", True
            
            # Pattern 3: NFLfastRv2 CLI execution
            # python -m nflfastRv2.cli -> nflfastRv2/cli/__main__.py or main.py
            is_nflfastrv2_cli = (
                'nflfastRv2' in path_parts and 
                ('cli' in path_parts or main_path.name in ['__main__.py', 'main.py']) and
                not is_quantcup_cli  # Not executed via quantcup
            )
            if is_nflfastrv2_cli:
                # Extract CLI command details from sys.argv
                if len(sys.argv) >= 3:  # [script, command, subcommand]
                    command = sys.argv[1]
                    subcommand = sys.argv[2]
                    return f"nflfastrv2_{command}_{subcommand}", True
                elif len(sys.argv) >= 2:  # [script, command]
                    command = sys.argv[1]
                    return f"nflfastrv2_{command}", True
                else:
                    return "nflfastrv2", True
            
            # Pattern 4: Odds API CLI execution
            # python -m odds_api.cli or direct odds_api/cli.py execution
            is_odds_api_cli = (
                'odds_api' in path_parts and
                (main_path.name in ['cli.py', '__main__.py', 'pipeline.py'] or 'cli' in path_parts) and
                not is_quantcup_cli  # Not executed via quantcup
            )
            if is_odds_api_cli:
                # Extract command from sys.argv
                if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
                    command = sys.argv[1]
                    # Add subcommand if present (e.g., odds pipeline --sport nfl)
                    if len(sys.argv) >= 3 and not sys.argv[2].startswith('-'):
                        subcommand = sys.argv[2]
                        return f"odds_api_{command}_{subcommand}", True
                    else:
                        return f"odds_api_{command}", True
                else:
                    return "odds_api", True
            
            # Pattern 5: Odds Scraper CLI execution
            # python -m odds_scraper.cli or direct odds_scraper/cli.py or odds_scraper/pipeline.py execution
            is_odds_scraper_cli = (
                'odds_scraper' in path_parts and
                (main_path.name in ['cli.py', '__main__.py', 'pipeline.py', 'scraper.py', 'scraperv2.py'] or 'cli' in path_parts) and
                not is_quantcup_cli  # Not executed via quantcup
            )
            if is_odds_scraper_cli:
                # Extract command from sys.argv
                if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
                    command = sys.argv[1]
                    # Add subcommand if present
                    if len(sys.argv) >= 3 and not sys.argv[2].startswith('-'):
                        subcommand = sys.argv[2]
                        return f"odds_scraper_{command}_{subcommand}", True
                    else:
                        return f"odds_scraper_{command}", True
                else:
                    # Detect specific scraper script execution
                    if main_path.name == 'scraperv2.py':
                        return "odds_scraper_v2", True
                    elif main_path.name == 'scraper.py':
                        return "odds_scraper_v1", True
                    elif main_path.name == 'pipeline.py':
                        return "odds_scraper_pipeline", True
                    else:
                        return "odds_scraper", True
            
            # Pattern 6: NOAA CLI execution
            # python -m noaa.cli or direct noaa/cli.py execution
            is_noaa_cli = (
                'noaa' in path_parts and 
                (main_path.name in ['cli.py', '__main__.py'] or 'cli' in path_parts) and
                not is_quantcup_cli  # Not executed via quantcup
            )
            if is_noaa_cli:
                # Extract command from sys.argv
                if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
                    command = sys.argv[1]
                    return f"noaa_{command}", True
                else:
                    return "noaa", True
            
            # Pattern 6: Direct script execution (performance benchmark, etc.)
            # python nflfastRv3/performance_benchmark.py
            if main_path.name == 'performance_benchmark.py':
                return 'performance_benchmark', True
            
            # Pattern 7: Other standalone scripts in quantcup ecosystem
            # Direct execution of .py files in project modules
            project_modules = ['nflfastRv3', 'odds_api', 'odds_scraper', 'noaa', 'analytics', 'scripts', 'api_sports', 'commonv2']
            if any(module in str(main_path) for module in project_modules) and main_path.suffix == '.py':
                # Extract module and script name
                path_parts = main_path.parts
                for i, part in enumerate(path_parts):
                    if part in project_modules:
                        module_name = part.lower()
                        script_name = main_path.stem
                        # Create meaningful session name
                        if script_name in ['__main__', 'main']:
                            return module_name, True
                        else:
                            return f"{module_name}_{script_name}", True
            
            # Pattern 8: Legacy CLI patterns (backward compatibility)
            if main_path.name == '__main__.py' and 'nflfastR' in str(main_path):
                # Extract CLI command details from sys.argv
                if len(sys.argv) >= 3:  # [script, data, process]
                    return f"cli_{sys.argv[1]}_{sys.argv[2]}", True
                elif len(sys.argv) >= 2:  # [script, data]
                    return f"cli_{sys.argv[1]}", True
                else:
                    return "cli", True
            
        except Exception as e:
            # If detection fails, fall back to no session
            debug_buffer.append(f"Session detection failed: {e}\n")
            pass
        
        debug_buffer.append("No session detected\n")
        return None, False
    
    def _detect_api_call(self, debug_buffer):
        """
        Detect if we're in an nflfastRv3 API function call.
        
        Args:
            debug_buffer (list): Buffer to append debug info to
        
        Returns:
            tuple: (api_session_name, is_api_session)
        """
        try:
            debug_buffer.append(f"[{datetime.now()}] API call detection starting\n")
            
            import inspect
            
            # Get the current call stack
            stack = inspect.stack()
            debug_buffer.append(f"Call stack depth: {len(stack)}\n")
            
            # Look for nflfastRv3 API functions in the call stack
            nflfastr_api_functions = {
                'run_data_pipeline': 'data_pipeline',
                'run_ml_pipeline': 'ml_pipeline', 
                'run_analytics': 'analytics',
                'build_warehouse': 'warehouse'  # Legacy API
            }
            
            for frame_info in stack:
                frame_filename = frame_info.filename
                frame_function = frame_info.function
                
                debug_buffer.append(f"Frame: {frame_filename} -> {frame_function}\n")
                
                # Check if this frame is from nflfastRv3 API
                if ('nflfastRv3' in frame_filename and 
                    '__init__.py' in frame_filename and 
                    frame_function in nflfastr_api_functions):
                    
                    api_function_type = nflfastr_api_functions[frame_function]
                    session_name = f"nflfastrv3_api_{api_function_type}"
                    
                    debug_buffer.append(f"nflfastRv3 API call detected: {frame_function}\n")
                    debug_buffer.append(f"API session name: {session_name}\n")
                    
                    return session_name, True
            
            # Second pass: Look for API functions in the entire stack more aggressively
            debug_buffer.append("Looking for API functions in full call stack...\n")
            for frame_info in stack:
                frame_filename = frame_info.filename
                frame_function = frame_info.function
                
                # Check if ANY frame mentions our API functions, even in different contexts
                if frame_function in nflfastr_api_functions:
                    api_function_type = nflfastr_api_functions[frame_function]
                    session_name = f"nflfastrv3_api_{api_function_type}"
                    
                    debug_buffer.append(f"nflfastRv3 API call detected in broader search: {frame_function}\n")
                    debug_buffer.append(f"API session name: {session_name}\n")
                    
                    return session_name, True
            
            # Third pass: Check for API functions in the call stack using globals/locals
            debug_buffer.append("Checking for API execution context...\n")
            try:
                # Look at the command line to see if it contains API function calls
                if len(sys.argv) >= 1 and sys.argv[0] == '-c':
                    # This is a python -c execution
                    # Look at frame locals/globals for evidence of API calls
                    for frame_info in stack:
                        frame = frame_info.frame
                        if frame:
                            # Check frame locals and globals for our API functions
                            for var_name, var_value in frame.f_locals.items():
                                if hasattr(var_value, '__name__') and var_value.__name__ in nflfastr_api_functions:
                                    api_function_type = nflfastr_api_functions[var_value.__name__]
                                    session_name = f"nflfastrv3_api_{api_function_type}"
                                    
                                    debug_buffer.append(f"API function found in frame locals: {var_value.__name__}\n")
                                    debug_buffer.append(f"API session name: {session_name}\n")
                                    
                                    return session_name, True
            except Exception as e:
                debug_buffer.append(f"Frame inspection failed: {e}\n")
            
            # Check for API context environment variable (highest priority)
            api_context = os.getenv('NFLFASTRV3_API_CONTEXT')
            if api_context:
                session_name = f"nflfastrv3_api_{api_context}"
                debug_buffer.append(f"API context from environment: {api_context}\n")
                debug_buffer.append(f"API session name: {session_name}\n")
                return session_name, True
            
            # Check for lazy API context (set by API functions before logger creation)
            if self._api_context:
                session_name = f"nflfastrv3_api_{self._api_context}"
                debug_buffer.append(f"API context from lazy setting: {self._api_context}\n")
                debug_buffer.append(f"API session name: {session_name}\n")
                return session_name, True
            
            # Check if nflfastRv3 modules are loaded (alternative detection)
            all_modules = list(sys.modules.keys())
            nflfastrv3_modules = [name for name in all_modules if 'nflfastRv3' in name]
            
            debug_buffer.append(f"nflfastRv3 modules loaded: {nflfastrv3_modules}\n")
            
            # If nflfastRv3 modules are loaded but we're not in CLI, might be API usage
            if nflfastrv3_modules:
                # Check if this is NOT a CLI execution
                is_cli_execution = any('cli' in module for module in nflfastrv3_modules)
                main_module = sys.modules.get('__main__')
                is_module_execution = (len(sys.argv) >= 1 and sys.argv[0] == '-m')
                
                debug_buffer.append(f"is_cli_execution: {is_cli_execution}\n")
                debug_buffer.append(f"is_module_execution: {is_module_execution}\n")
                
                # If nflfastRv3 is loaded but not via CLI, likely API usage
                if nflfastrv3_modules and not (is_cli_execution and is_module_execution):
                    debug_buffer.append("nflfastRv3 API usage detected via loaded modules\n")
                    # Mark as pending since we don't have specific context yet
                    self._pending_session = True
                    return "nflfastrv3_api_generic", True
            
            debug_buffer.append("No API call detected\n")
            return None, False
            
        except Exception as e:
            debug_buffer.append(f"API call detection failed: {e}\n")
            return None, False


def setup_logger(module_name, log_file=None, verbose=None, project_name=None):
    """
    Set up standardized logging for quantcup-simple modules.
    
    Console-first logging for production visibility with optional file logging.
    
    Args:
        module_name (str): Name of the module (e.g., 'nflfastr', 'warehouse', 'features', 'odds_api', 'nfl_data_py')
        log_file (str, optional): Custom log file path. If None, uses logs/{module_name}.log
        verbose (bool, optional): Enable verbose console output. If None, checks environment variables
        project_name (str, optional): Project name for environment variable lookup (e.g., 'NFLFASTR', 'ODDS_API')
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(module_name)
    
    # Avoid duplicate handlers on reload
    if logger.handlers:
        return logger
    
    # Determine verbose mode from environment variables
    if verbose is None:
        # Try project-specific verbose flag first, then fall back to generic
        env_vars_to_check = []
        if project_name:
            env_vars_to_check.append(f'{project_name}_VERBOSE')
        env_vars_to_check.extend(['QUANTCUP_VERBOSE', 'VERBOSE'])
        
        verbose = False
        for env_var in env_vars_to_check:
            if os.getenv(env_var, '0') == '1':
                verbose = True
                break
    
    # Controls
    log_to_files = os.getenv("LOG_TO_FILES", "1") == "1"  # Default on with automatic cleanup
    level = logging.DEBUG if verbose else logging.INFO
    
    logger.setLevel(level)
    
    # Console handler → STDOUT (production platforms collect this)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # Optional file logs (disabled by default in production)
    if log_to_files:
        # Get session-aware log directory (enhanced with timestamped folders)
        session_manager = LoggingSessionManager.get_instance()
        log_dir = session_manager.get_session_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine log file path
        if log_file is None:
            log_file = log_dir / f'{module_name}.log'
        else:
            log_file = Path(log_file)
            # If custom log_file provided, still use session directory
            if session_manager.session_active:
                log_file = log_dir / log_file.name
        
        # Lazy file handler with rotation - only creates file when first log is written
        file_handler = LazyFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    # Let uvicorn/gunicorn also see these logs
    logger.propagate = True
    
    return logger


def get_logger(module_name, project_name=None):
    """
    Get an existing logger or create a new one with default settings.

    Args:
        module_name (str): Name of the module
        project_name (str, optional): Project name for environment variable lookup

    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        # Logger doesn't exist yet, create it with default settings
        return setup_logger(module_name, project_name=project_name)

    # Ensure propagation is enabled for existing loggers (for production logging)
    logger.propagate = True
    return logger


# Project-specific convenience functions (backward compatibility)
# Note: These are kept for existing code; prefer setup_logger(module_name, project_name='PROJECT') directly.
def setup_nflfastr_logger(module_name, log_file=None, verbose=None):
    """
    Convenience function for nflfastR logging (maintains backward compatibility).
    
    Args:
        module_name (str): Name of the module
        log_file (str, optional): Custom log file path
        verbose (bool, optional): Enable verbose console output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(module_name, log_file=log_file, verbose=verbose, project_name='NFLFASTR')


def setup_odds_api_logger(module_name, log_file=None, verbose=None):
    """
    Convenience function for odds API logging.
    
    Args:
        module_name (str): Name of the module
        log_file (str, optional): Custom log file path
        verbose (bool, optional): Enable verbose console output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(module_name, log_file=log_file, verbose=verbose, project_name='ODDS_API')


def setup_nfl_data_py_logger(module_name, log_file=None, verbose=None):
    """
    Convenience function for nfl_data_py logging.
    
    Args:
        module_name (str): Name of the module
        log_file (str, optional): Custom log file path
        verbose (bool, optional): Enable verbose console output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(module_name, log_file=log_file, verbose=verbose, project_name='NFL_DATA_PY')


def get_session_output_dir():
    """
    Convenience function to get the current session output directory.
    
    This allows any script to save outputs (reports, data files, etc.) 
    in the same timestamped folder as the logs for complete organization.
    
    Returns:
        Path: Session folder if active, otherwise current directory
        
    Example:
        >>> from commonv2.core.logging import get_session_output_dir
        >>> output_dir = get_session_output_dir()
        >>> report_file = output_dir / "my_report.md"
        >>> with open(report_file, 'w') as f:
        ...     f.write("Report content")
    """
    session_manager = LoggingSessionManager.get_instance()
    return session_manager.get_session_output_dir()
