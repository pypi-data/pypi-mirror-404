from ymvas.config.components.task import Task
from typing import TYPE_CHECKING
from ymvas.utils.files import walker

if TYPE_CHECKING:
    from ymvas.settings import Settings



class YTasksSettings:

    def __init__(self, settings:"Settings" ) -> None:
        self.settings = settings

    
    def list(self):
        stg = self.settings

        tasks = []
        for x in walker(stg.d_tasks):
            tasks.append(Task(x))
        
        return tasks
