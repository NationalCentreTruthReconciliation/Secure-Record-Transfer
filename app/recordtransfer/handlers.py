import logging
from io import StringIO

from recordtransfer.models import Job


class JobLogHandler(logging.Handler):
    """A logging handler that appends log messages to a Job's message_log field."""

    def __init__(self, job: Job):
        """Initialize with the job to log to.

        Args:
            job (Job): The job to append log messages to
        """
        super().__init__()
        self.job = job
        # Initialize the buffer with existing message log content
        self.log_buffer = StringIO(self.job.message_log or '')

    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record by appending it to the job's message_log.

        Args:
            record (LogRecord): The log record to process
        """
        msg = self.format(record)
        self.log_buffer.write(f"{msg}\n")

        # Update the job's message_log field
        self.job.message_log = self.log_buffer.getvalue()
        self.job.save(update_fields=['message_log'])
