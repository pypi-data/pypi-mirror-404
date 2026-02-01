# guardianhub_sdk/workflows/muscle_factory.py

from temporalio.worker import Worker
from .mission_skeleton import SpecialistMissionWorkflow
from guardianhub.config.settings import settings
class MuscleFactory:
    """
    Utilities to turn a Brain into a Worker.
    The Agent Service calls this to get a pre-configured Temporal Worker.
    """
    @staticmethod
    def create_worker(temporal_client, agent_instance) -> Worker:
        """
        Assembles the worker using the SDK's skeleton
        and the Specialist's domain activities.
        """
        return Worker(
            temporal_client,
            task_queue=settings.temporal_settings.task_queue,
            workflows=[SpecialistMissionWorkflow],
            activities=agent_instance.get_activities()
        )