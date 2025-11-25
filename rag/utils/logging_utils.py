# rag/utils/logging_utils.py

import logging
import os
from datetime import datetime
from typing import Optional

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the RAG system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        log_format: Optional custom log format
        
    Returns:
        Configured logger instance
    """
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger('rag_system')
    return logger

def get_rag_logger(name: str = 'rag') -> logging.Logger:
    """
    Get a logger instance for RAG components.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'rag.{name}')

class RAGLogger:
    """
    Custom logger class for RAG operations with structured logging.
    """
    
    def __init__(self, component_name: str):
        self.logger = get_rag_logger(component_name)
        self.component_name = component_name
    
    def log_ingestion_start(self, source: str, file_count: int = None):
        """Log the start of data ingestion."""
        message = f"Starting ingestion from {source}"
        if file_count:
            message += f" ({file_count} files)"
        self.logger.info(message)
    
    def log_ingestion_complete(self, source: str, chunks_created: int):
        """Log successful completion of data ingestion."""
        self.logger.info(f"Ingestion completed from {source}: {chunks_created} chunks created")
    
    def log_ingestion_error(self, source: str, error: str):
        """Log ingestion errors."""
        self.logger.error(f"Ingestion failed from {source}: {error}")
    
    def log_query_processed(self, query: str, documents_retrieved: int):
        """Log query processing."""
        self.logger.info(f"Query processed: '{query[:50]}...' -> {documents_retrieved} documents retrieved")
    
    def log_response_generated(self, query: str, response_length: int):
        """Log response generation."""
        self.logger.info(f"Response generated for query: '{query[:50]}...' ({response_length} chars)")
    
    def log_error(self, operation: str, error: str):
        """Log general errors."""
        self.logger.error(f"Error in {operation}: {error}")
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics."""
        message = f"{operation} completed in {duration:.2f}s"
        if details:
            message += f" - {details}"
        self.logger.info(message)

def log_rag_pipeline(
    operation: str,
    start_time: datetime,
    end_time: datetime,
    success: bool,
    details: dict = None
):
    """
    Log RAG pipeline operations with timing and success metrics.
    
    Args:
        operation: Name of the operation
        start_time: Operation start time
        end_time: Operation end time
        success: Whether the operation was successful
        details: Additional details to log
    """
    duration = (end_time - start_time).total_seconds()
    logger = get_rag_logger('pipeline')
    
    status = "SUCCESS" if success else "FAILED"
    message = f"{operation} - {status} - Duration: {duration:.2f}s"
    
    if details:
        message += f" - Details: {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)

