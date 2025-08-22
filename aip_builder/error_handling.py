"""
Enhanced Error Handling cho AIP Builder - Phase 7
Quan ly loi, logging nang cao, va co che recovery
"""

import logging
import traceback
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from contextlib import contextmanager

class ErrorLevel(Enum):
    """Muc do nghiem trong cua loi"""
    INFO = "INFO"
    WARNING = "WARNING"  
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Loai loi"""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_DATA = "INVALID_DATA"
    XML_ERROR = "XML_ERROR"
    PDF_ERROR = "PDF_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    UNKNOWN = "UNKNOWN"

@dataclass
class ErrorDetail:
    """Chi tiet loi"""
    level: ErrorLevel
    category: ErrorCategory
    message: str
    exception: Optional[Exception] = None
    traceback_str: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source_function: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'exception_type': type(self.exception).__name__ if self.exception else None,
            'traceback': self.traceback_str,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'source_function': self.source_function,
            'source_file': self.source_file,
            'line_number': self.line_number,
            'recoverable': self.recoverable
        }

class ErrorCollector:
    """Thu thap va quan ly loi"""
    
    def __init__(self):
        self.errors: List[ErrorDetail] = []
        self.warnings: List[ErrorDetail] = []
        self.info: List[ErrorDetail] = []
        self.critical: List[ErrorDetail] = []
        
    def add_error(self, 
                  message: str,
                  category: ErrorCategory = ErrorCategory.UNKNOWN,
                  exception: Optional[Exception] = None,
                  context: Optional[Dict[str, Any]] = None,
                  recoverable: bool = True,
                  capture_traceback: bool = True) -> ErrorDetail:
        """Them loi vao collector"""
        
        error_detail = ErrorDetail(
            level=ErrorLevel.ERROR,
            category=category,
            message=message,
            exception=exception,
            context=context or {},
            recoverable=recoverable
        )
        
        # Capture traceback
        if capture_traceback and exception:
            error_detail.traceback_str = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
        
        # Capture source info
        frame = sys._getframe(1)
        error_detail.source_function = frame.f_code.co_name
        error_detail.source_file = frame.f_code.co_filename
        error_detail.line_number = frame.f_lineno
        
        self.errors.append(error_detail)
        return error_detail
    
    def add_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> ErrorDetail:
        """Them canh bao"""
        warning = ErrorDetail(
            level=ErrorLevel.WARNING,
            category=ErrorCategory.UNKNOWN,
            message=message,
            context=context or {}
        )
        self.warnings.append(warning)
        return warning
    
    def add_critical(self, 
                    message: str,
                    exception: Optional[Exception] = None,
                    context: Optional[Dict[str, Any]] = None) -> ErrorDetail:
        """Them loi nghiem trong"""
        error_detail = ErrorDetail(
            level=ErrorLevel.CRITICAL,
            category=ErrorCategory.SYSTEM_ERROR,
            message=message,
            exception=exception,
            context=context or {},
            recoverable=False
        )
        
        if exception:
            error_detail.traceback_str = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
        
        self.critical.append(error_detail)
        return error_detail
    
    def has_critical_errors(self) -> bool:
        """Kiem tra co loi nghiem trong khong"""
        return len(self.critical) > 0
    
    def has_errors(self) -> bool:
        """Kiem tra co loi khong"""
        return len(self.errors) > 0 or len(self.critical) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Lay tom tat loi"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_critical': len(self.critical),
            'recoverable_errors': sum(1 for e in self.errors if e.recoverable),
            'categories': self._get_category_counts()
        }
    
    def _get_category_counts(self) -> Dict[str, int]:
        """Dem so loi theo category"""
        counts = {}
        all_errors = self.errors + self.critical
        for error in all_errors:
            category = error.category.value
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def export_to_json(self, file_path: Path):
        """Export loi ra file JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'critical': [c.to_dict() for c in self.critical]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

class EnhancedLogger:
    """Logger nang cao voi error handling"""
    
    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.error_collector = ErrorCollector()
        
        # Setup logging
        if not self.logger.handlers:
            self._setup_logging(log_file)
    
    def _setup_logging(self, log_file: Optional[Path]):
        """Setup logging configuration"""
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info"""
        self.logger.info(message)
        if context:
            self.logger.debug(f"Context: {context}")
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning"""
        self.logger.warning(message)
        self.error_collector.add_warning(message, context)
    
    def error(self, 
             message: str,
             exception: Optional[Exception] = None,
             category: ErrorCategory = ErrorCategory.UNKNOWN,
             context: Optional[Dict[str, Any]] = None,
             recoverable: bool = True):
        """Log error"""
        self.logger.error(message)
        if exception:
            self.logger.debug(f"Exception: {exception}", exc_info=True)
        
        self.error_collector.add_error(
            message=message,
            exception=exception,
            category=category,
            context=context,
            recoverable=recoverable
        )
    
    def critical(self, 
                message: str,
                exception: Optional[Exception] = None,
                context: Optional[Dict[str, Any]] = None):
        """Log critical error"""
        self.logger.critical(message)
        if exception:
            self.logger.critical(f"Critical exception: {exception}", exc_info=True)
        
        self.error_collector.add_critical(
            message=message,
            exception=exception,
            context=context
        )

class RetryConfig:
    """Cau hinh retry"""
    def __init__(self, max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff

class ErrorRecovery:
    """Co che recovery tu loi"""
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
    
    @contextmanager
    def handle_errors(self, 
                     operation_name: str,
                     category: ErrorCategory = ErrorCategory.UNKNOWN,
                     recoverable: bool = True,
                     reraise: bool = False):
        """Context manager de bat loi"""
        try:
            yield
        except Exception as e:
            self.logger.error(
                f"Loi trong operation '{operation_name}': {str(e)}",
                exception=e,
                category=category,
                recoverable=recoverable
            )
            
            if reraise or not recoverable:
                raise
    
    def retry_operation(self, 
                       func: Callable,
                       retry_config: RetryConfig,
                       operation_name: str,
                       *args, **kwargs):
        """Retry operation voi backoff"""
        import time
        
        last_exception = None
        
        for attempt in range(retry_config.max_attempts):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{retry_config.max_attempts} for {operation_name}")
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < retry_config.max_attempts - 1:
                    delay = retry_config.delay * (retry_config.backoff ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {operation_name}, retry in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"All {retry_config.max_attempts} attempts failed for {operation_name}",
                        exception=e,
                        category=ErrorCategory.SYSTEM_ERROR
                    )
        
        raise last_exception

def categorize_exception(exception: Exception) -> ErrorCategory:
    """Phan loai exception thanh category"""
    if isinstance(exception, FileNotFoundError):
        return ErrorCategory.FILE_NOT_FOUND
    elif isinstance(exception, PermissionError):
        return ErrorCategory.PERMISSION_DENIED
    elif isinstance(exception, ValueError):
        return ErrorCategory.INVALID_DATA
    elif isinstance(exception, TimeoutError):
        return ErrorCategory.TIMEOUT_ERROR
    elif isinstance(exception, MemoryError):
        return ErrorCategory.MEMORY_ERROR
    elif 'xml' in str(exception).lower():
        return ErrorCategory.XML_ERROR
    elif 'pdf' in str(exception).lower():
        return ErrorCategory.PDF_ERROR
    else:
        return ErrorCategory.UNKNOWN

def create_enhanced_logger(name: str, log_dir: Optional[Path] = None) -> EnhancedLogger:
    """Tao enhanced logger"""
    if log_dir:
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        log_file = None
    
    return EnhancedLogger(name, log_file)

# Decorator cho error handling
def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 recoverable: bool = True,
                 reraise: bool = False):
    """Decorator de bat loi tu dong"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Tim logger tu args hoac tao moi
                logger = None
                for arg in args:
                    if hasattr(arg, 'logger') and isinstance(arg.logger, EnhancedLogger):
                        logger = arg.logger
                        break
                
                if not logger:
                    logger = create_enhanced_logger(func.__name__)
                
                logger.error(
                    f"Loi trong function '{func.__name__}': {str(e)}",
                    exception=e,
                    category=category,
                    recoverable=recoverable
                )
                
                if reraise or not recoverable:
                    raise
                
                return None
                
        return wrapper
    return decorator
