from ..decorators import singleton
from multiprocessing import Process, Pipe
from enum import Enum
from dtPyAppFramework.settings import Settings

import threading
import sys
import os
import logging
import uuid

issued_uuids = []


def get_new_uuid():
    """
    Generate a new UUID (Universally Unique Identifier) and ensure it is not already issued.

    Returns:
        str: A new UUID.
    """
    while True:
        new_uuid = str(uuid.uuid4())
        if new_uuid not in issued_uuids:
            issued_uuids.append(new_uuid)
            return new_uuid


@singleton()
class MultiProcessingManager:
    """
    Singleton class for managing multiprocessing operations.

    Attributes:
        log_path (str): Path to the log folder.
    """

    def __init__(self):
        super().__init__()
        self.log_path = None
        self.jobs = {}

    def set_log_path(self, log_path):
        """
        Set the log path for multiprocessing operations.

        Args:
            log_path (str): Path to the log folder.
        """
        self.log_path = log_path

    def get_job(self, job_name):
        if job_name not in self.jobs:
            return None
        return self.jobs[job_name]

    def new_multiprocessing_job(self, job_name, worker_count, target, args=(), kwargs={}):
        """
        Create a new multiprocessing job.

        Args:
            job_name (str): Name of the job.
            worker_count (int): Number of worker processes.
            target (callable): Target function to be executed by each worker.
            args (tuple): Arguments for the target function.
            kwargs (dict): Keyword arguments for the target function.

        Returns:
            MultiProcessingJob: An instance of MultiProcessingJob.
        """
        job = MultiProcessingJob(self.log_path, job_name, worker_count, target, args, kwargs)
        self.jobs[job_name] = job
        return job


class MultiProcessingJob():
    """
    Class representing a multiprocessing job.

    Attributes:
        job_id (str): Unique identifier for the job.
        job_name (str): Name of the job.
        worker_count (int): Number of worker processes.
        target (callable): Target function to be executed by each worker.
        log_path (str): Path to the log folder.
        args (tuple): Arguments for the target function.
        kwargs (dict): Keyword arguments for the target function.
        workers (list): List of worker processes.
    """

    def __init__(self, log_path, job_name, worker_count, target, args=(), kwargs={}):
        super().__init__()
        self.job_id = get_new_uuid()
        self.job_name = job_name
        self.worker_count = worker_count
        self.target = target
        self.log_path = log_path
        self.args = tuple(args)
        self.kwargs = dict(kwargs)
        self.workers = []
        self.instance_control_pipes = []

    def start(self):
        """
        Start the worker processes for the job.
        """
        for _ in range(self.worker_count):
            ctrl_pipe_parent, ctrl_pipe_connection = Pipe()
            self.instance_control_pipes.append(ctrl_pipe_parent)
            worker = DtProcess(self.log_path, self.job_id, self.job_name, self.target, self.job_name,
                               ctrl_pipe_connection, self.args, self.kwargs)
            worker.start()
            logging.info(f'Started Worker {worker.worker_id} for Job ID {self.job_id} ({self.job_name}).')
            self.workers.append(worker)

    def wait(self):
        """
        Wait for all worker processes to finish.
        """
        for worker in self.workers:
            worker.join()
        logging.info(f'All Workers for Job ID {self.job_id} ({self.job_name}) ended.')

    def close(self):
        logging.info('Sending Close CMD to Processes...')
        for conn in self.instance_control_pipes:
            conn.send(ProcessStateCommands.CMD_CLOSE)

class ProcessStateCommands(Enum):
    CMD_CLOSE = 1


class DtProcess(Process):
    """
    Custom multiprocessing Process class with additional attributes.

    Attributes:
        worker_id (str): Unique identifier for the worker process.
        job_id (str): Unique identifier for the job.
        job_name (str): Name of the job.
        parent_log_path (str): Path to the log folder of the parent process.
        multi_processing_job (MultiProcessingJob): Reference to the parent MultiProcessingJob.
    """

    def __init__(self, parent_log_path, job_id, job_name, target=None, name=None,
                 ctrl_pipe_connection=None, args=(), kwargs={}):
        self.worker_id = get_new_uuid()
        self.job_id = job_id
        self.job_name = job_name
        self.parent_log_path = parent_log_path
        self.multi_processing_job = None
        self.running = None
        self.ctrl_pipe_connection = ctrl_pipe_connection

        super(DtProcess, self).__init__(target=target, name=name, args=args, kwargs=kwargs)
        self.state_check_thread = None

    def state_check(self):
        logging.info('Starting Worker State Monitor Thread')
        while True:
            if self.ctrl_pipe_connection.poll():  # Check if there is a message from this pipe
                try:
                    command = self.ctrl_pipe_connection.recv()
                    match command:
                        case ProcessStateCommands.CMD_CLOSE:
                            self.close()
                            break

                        case _:
                            logging.error(
                                f'Unrecognised Request: command = {command}')

                except EOFError as ex:
                    logging.exception(ex)

        logging.info('Worker State Monitor Thread Ended')

    def close(self):
        self.running.clear()
        logging.info('Closed Process')

    def set_parent(self, job):
        """
        Set the parent MultiProcessingJob for the worker process.

        Args:
            job (MultiProcessingJob): Parent MultiProcessingJob.
        """
        self.multi_processing_job = job

    def run(self):
        """
        Run method for the worker process.
        """
        from . import ProcessManager
        self.running = threading.Event()
        self.running.set()
        ProcessManager().__initialise_spawned_application__(self.parent_log_path, self.job_id, self.worker_id,
                                                            self.job_name, self.running)
        print(f'Process ID = {os.getpid()}')
        print(f'worker_id {os.getpid()} = {self.worker_id}')
        print(f'job_id {os.getpid()} = {self.job_id}')
        self.state_check_thread = threading.Thread(target=self.state_check, daemon=True)
        self.state_check_thread.start()
        super().run()
        Settings().secret_manager.close()
