"""
Batch Processor cho AIP Builder - Xu ly dong loat nhieu package
Ket noi voi Phase 6 cua ke hoach phat trien 8 giai doan
"""

import concurrent.futures
import logging
import multiprocessing
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from queue import Queue

from .models import HoSo
from .package_builder import PackageBuilder
from .validator import CSIPValidator, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """Cau hinh xu ly batch"""
    max_workers: int = None  # None = tu dong theo CPU cores
    chunk_size: int = 5  # So luong ho so trong 1 batch
    validate_after_build: bool = True  # Validation sau khi build
    continue_on_error: bool = True  # Tiep tuc khi co loi
    output_parallel: bool = False  # Cho phep ghi file parallel
    memory_limit_mb: int = 1024  # Gioi han memory (MB)
    timeout_per_package: int = 300  # Timeout cho 1 package (seconds)

@dataclass
class BatchResult:
    """Ket qua xu ly batch"""
    total_packages: int = 0
    successful_packages: int = 0
    failed_packages: int = 0
    validation_passed: int = 0
    validation_failed: int = 0
    total_time: float = 0.0
    total_size_mb: float = 0.0
    errors: List[str] = None
    package_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.package_results is None:
            self.package_results = []

class BatchProgressCallback:
    """Callback cho progress reporting"""
    
    def __init__(self):
        self.callbacks: List[Callable] = []
        self.lock = threading.Lock()
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Them callback function"""
        with self.lock:
            self.callbacks.append(callback)
    
    def report_progress(self, data: Dict[str, Any]):
        """Bao cao tien do"""
        with self.lock:
            for callback in self.callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

class BatchProcessor:
    """Xu ly dong loat nhieu AIP package voi parallel processing"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        if self.config.max_workers is None:
            self.config.max_workers = min(multiprocessing.cpu_count(), 4)
        
        self.progress_callback = BatchProgressCallback()
        self._stop_event = threading.Event()
        
        logger.info(f"Khoi tao BatchProcessor voi {self.config.max_workers} workers")
    
    def add_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Them callback cho progress reporting"""
        self.progress_callback.add_callback(callback)
    
    def stop(self):
        """Dung batch processing"""
        self._stop_event.set()
        logger.info("Nhan lenh dung batch processing")
    
    def build_packages_parallel(self, 
                              ho_so_list: List[HoSo], 
                              output_dir: Path,
                              pdf_root: Path) -> BatchResult:
        """Xay dung nhieu package parallel"""
        
        start_time = time.time()
        result = BatchResult(total_packages=len(ho_so_list))
        
        logger.info(f"Bat dau xay dung {len(ho_so_list)} packages voi {self.config.max_workers} workers")
        
        # Chia thanh cac chunk nho
        chunks = self._create_chunks(ho_so_list, self.config.chunk_size)
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                
                # Submit tat ca tasks
                future_to_chunk = {}
                for i, chunk in enumerate(chunks):
                    if self._stop_event.is_set():
                        break
                        
                    future = executor.submit(
                        self._process_chunk,
                        chunk, 
                        output_dir, 
                        pdf_root,
                        i + 1,
                        len(chunks)
                    )
                    future_to_chunk[future] = (i, chunk)
                
                # Xu ly ket qua
                for future in concurrent.futures.as_completed(future_to_chunk, timeout=self.config.timeout_per_package * len(ho_so_list)):
                    if self._stop_event.is_set():
                        logger.info("Nhan lenh dung, huy cac task con lai")
                        break
                        
                    chunk_index, chunk = future_to_chunk[future]
                    
                    try:
                        chunk_result = future.result()
                        self._merge_chunk_result(result, chunk_result)
                        
                        # Report progress
                        self.progress_callback.report_progress({
                            'type': 'chunk_completed',
                            'chunk_index': chunk_index + 1,
                            'total_chunks': len(chunks),
                            'successful': chunk_result['successful'],
                            'failed': chunk_result['failed'],
                            'total_completed': result.successful_packages + result.failed_packages,
                            'total_packages': result.total_packages
                        })
                        
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Chunk {chunk_index + 1} timeout")
                        result.errors.append(f"Chunk {chunk_index + 1} timeout")
                        if not self.config.continue_on_error:
                            break
                            
                    except Exception as e:
                        logger.error(f"Loi xu ly chunk {chunk_index + 1}: {e}")
                        result.errors.append(f"Chunk {chunk_index + 1}: {str(e)}")
                        if not self.config.continue_on_error:
                            break
                
        except KeyboardInterrupt:
            logger.info("Nhan Ctrl+C, dung batch processing")
            self.stop()
        
        result.total_time = time.time() - start_time
        
        logger.info(f"Hoan thanh batch processing trong {result.total_time:.2f}s")
        logger.info(f"Thanh cong: {result.successful_packages}/{result.total_packages}")
        
        return result
    
    def _create_chunks(self, ho_so_list: List[HoSo], chunk_size: int) -> List[List[HoSo]]:
        """Chia danh sach ho so thanh cac chunk"""
        chunks = []
        for i in range(0, len(ho_so_list), chunk_size):
            chunk = ho_so_list[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
    
    def _process_chunk(self, 
                      chunk: List[HoSo], 
                      output_dir: Path, 
                      pdf_root: Path,
                      chunk_index: int,
                      total_chunks: int) -> Dict[str, Any]:
        """Xu ly 1 chunk ho so"""
        
        logger.info(f"Xu ly chunk {chunk_index}/{total_chunks} voi {len(chunk)} ho so")
        
        from .config import Config
        config = Config()
        builder = PackageBuilder(config)
        chunk_result = {
            'successful': 0,
            'failed': 0,
            'total_size_mb': 0.0,
            'packages': [],
            'errors': []
        }
        
        for ho_so in chunk:
            if self._stop_event.is_set():
                break
                
            try:
                # Build package
                package_result = builder.build_single_package_dict(ho_so, output_dir, pdf_root)
                
                if package_result['success']:
                    chunk_result['successful'] += 1
                    chunk_result['total_size_mb'] += package_result.get('size_mb', 0)
                    
                    # Validation neu can
                    if self.config.validate_after_build:
                        validation_result = self._validate_package(package_result['package_path'])
                        package_result['validation'] = validation_result
                else:
                    chunk_result['failed'] += 1
                    chunk_result['errors'].append(package_result.get('error', 'Unknown error'))
                
                chunk_result['packages'].append(package_result)
                
            except Exception as e:
                logger.error(f"Loi xu ly ho so {ho_so.id}: {e}")
                chunk_result['failed'] += 1
                chunk_result['errors'].append(f"Ho so {ho_so.id}: {str(e)}")
                
                if not self.config.continue_on_error:
                    break
        
        logger.info(f"Hoan thanh chunk {chunk_index}: {chunk_result['successful']} thanh cong, {chunk_result['failed']} loi")
        return chunk_result
    
    def _validate_package(self, package_path: Path) -> ValidationResult:
        """Validate 1 package"""
        try:
            validator = CSIPValidator()
            return validator.validate_package(package_path)
        except Exception as e:
            logger.warning(f"Loi validation package {package_path.name}: {e}")
            result = ValidationResult(package_path.name)
            result.add_error(f"Validation error: {str(e)}")
            return result
    
    def _merge_chunk_result(self, batch_result: BatchResult, chunk_result: Dict[str, Any]):
        """Merge ket qua chunk vao batch result"""
        batch_result.successful_packages += chunk_result['successful']
        batch_result.failed_packages += chunk_result['failed']
        batch_result.total_size_mb += chunk_result['total_size_mb']
        batch_result.errors.extend(chunk_result['errors'])
        batch_result.package_results.extend(chunk_result['packages'])
        
        # Count validation results
        for pkg in chunk_result['packages']:
            if 'validation' in pkg:
                validation: ValidationResult = pkg['validation']
                if validation.is_valid:
                    batch_result.validation_passed += 1
                else:
                    batch_result.validation_failed += 1

class BatchMonitor:
    """Monitor cho batch processing"""
    
    def __init__(self):
        self.start_time = None
        self.last_report_time = None
        self.processed_count = 0
        self.lock = threading.Lock()
    
    def start(self):
        """Bat dau monitor"""
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.processed_count = 0
    
    def progress_callback(self, data: Dict[str, Any]):
        """Xu ly progress callback"""
        with self.lock:
            current_time = time.time()
            
            if data['type'] == 'chunk_completed':
                self.processed_count = data['total_completed']
                total = data['total_packages']
                
                # Tinh toan thong ke
                elapsed = current_time - self.start_time
                if self.processed_count > 0:
                    avg_time = elapsed / self.processed_count
                    estimated_remaining = (total - self.processed_count) * avg_time
                    
                    progress_pct = (self.processed_count / total) * 100
                    
                    logger.info(
                        f"Progress: {self.processed_count}/{total} ({progress_pct:.1f}%) "
                        f"- Elapsed: {elapsed:.1f}s "
                        f"- Est. remaining: {estimated_remaining:.1f}s"
                    )
                
                self.last_report_time = current_time

def create_batch_processor(max_workers: int = None, 
                         validate: bool = True,
                         chunk_size: int = 5) -> BatchProcessor:
    """Tao BatchProcessor voi cau hinh mac dinh"""
    config = BatchConfig(
        max_workers=max_workers,
        chunk_size=chunk_size,
        validate_after_build=validate,
        continue_on_error=True
    )
    return BatchProcessor(config)
