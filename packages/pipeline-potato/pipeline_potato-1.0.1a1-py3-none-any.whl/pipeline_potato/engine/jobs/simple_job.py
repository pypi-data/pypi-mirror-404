from abc import ABC

from pipeline_potato.core import APotato, APipeline, AJob


class SimpleJob(AJob, ABC):
    def __init__(self, job_name: str, pipeline: APipeline, step_id: int) -> None:
        super().__init__(job_name, step_id)

        self._pipeline = pipeline


    @property
    def pipeline(self) -> APipeline:
        return self._pipeline


    def potato(self) -> APotato:
        return self._pipeline.potato()
