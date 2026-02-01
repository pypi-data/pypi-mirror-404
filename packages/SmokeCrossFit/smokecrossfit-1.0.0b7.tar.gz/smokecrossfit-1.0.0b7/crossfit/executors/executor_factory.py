from crossfit.models.executor_models import ExecutorType
from crossfit.executors.local_executor import LocalExecutor

def create_executor(executor_type: ExecutorType, logger = None, catch: bool = True, **kwargs):
    if executor_type == ExecutorType.Local:
        return LocalExecutor(logger, catch, **kwargs)
    else:
        raise ValueError(f"Unknown executor type: {executor_type}")
