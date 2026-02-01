import time
from typing import Optional, List, Dict, Any
from .workflow_tasks import (
    WorkflowTask,
    ComputeViewTask,
    PythonScriptTask,
    EmailTask,
    ChartTask,
    EtlTask,
    IfElseTask,
    RoutingTask,
    Condition
)
from .utils import get_indicators_from_structure


class WorkflowBuilder:

    def __init__(self, kawa_client, name: str):
        self._k = kawa_client
        self._name = name
        self._description = ""
        self._tasks: List[WorkflowTask] = []
        self._trigger_type = "MANUAL"
        self._trigger_parameters = []
        self._datasource_ids_for_refresh = []
        self._pending_exports = []
        self._schedule = None
        self._workflow_id = None

    @property
    def workflow_id(self):
        return self._workflow_id

    @property
    def name(self):
        return self._name

    def with_description(self, description: str) -> 'WorkflowBuilder':
        self._description = description
        return self

    def add_task(self, task: WorkflowTask) -> 'WorkflowBuilder':
        self._tasks.append(task)
        return self

    def add_tasks(self, tasks: List[WorkflowTask]) -> 'WorkflowBuilder':
        self._tasks.extend(tasks)
        return self

    def with_manual_trigger(self, trigger_parameters: Optional[List[dict]] = None) -> 'WorkflowBuilder':
        self._trigger_type = "MANUAL"
        self._trigger_parameters = trigger_parameters or []
        return self

    def with_schedule_trigger(self, schedule: Optional[dict] = None) -> 'WorkflowBuilder':
        self._trigger_type = "SCHEDULE"
        self._schedule = schedule
        self._trigger_parameters = []
        return self

    def with_trigger(self, trigger_type: str, parameters: Optional[List[dict]] = None) -> 'WorkflowBuilder':
        self._trigger_type = trigger_type
        if parameters:
            for p in parameters:
                if 'id' not in p and 'name' in p:
                    p['id'] = p['name']
                if 'defaultValue' not in p:
                    p['defaultValue'] = None
                self._trigger_parameters.append(p)
        return self

    def with_data_refresh_trigger(self, datasource_ids: List[str]) -> 'WorkflowBuilder':
        self._trigger_type = "DATA_REFRESH"
        self._datasource_ids_for_refresh = datasource_ids
        self._trigger_parameters = []
        return self

    def with_daily_schedule(self, hour: int, minute: int = 0, timezone: Optional[str] = None) -> 'WorkflowBuilder':
        self._trigger_type = "SCHEDULE"
        self._schedule = {
            "type": "DAILY",
            "hour": hour,
            "minute": minute
        }
        if timezone:
            self._schedule["timezone"] = timezone
        self._trigger_parameters = []
        return self

    def with_weekly_schedule(self, day_of_week: str, hour: int, minute: int = 0, timezone: Optional[str] = None) -> 'WorkflowBuilder':
        self._trigger_type = "SCHEDULE"
        self._schedule = {
            "type": "WEEKLY",
            "dayOfWeek": day_of_week.upper(),
            "hour": hour,
            "minute": minute
        }
        if timezone:
            self._schedule["timezone"] = timezone
        self._trigger_parameters = []
        return self

    def with_cron_schedule(self, cron_expression: str, timezone: Optional[str] = None) -> 'WorkflowBuilder':
        self._trigger_type = "SCHEDULE"
        self._schedule = {
            "type": "CRON",
            "cronExpression": cron_expression
        }
        if timezone:
            self._schedule["timezone"] = timezone
        self._trigger_parameters = []
        return self

    def export_to_datasource(self,
                             source_task: WorkflowTask,
                             datasource_name: str,
                             datasource_description: str = "",
                             loading_mode: str = "RESET_BEFORE_INSERT",
                             default_global_policy: str = "ALLOW_ALL") -> 'WorkflowBuilder':
        if not source_task.output_as_datasource:
            source_task.with_output_as_datasource()

        self._pending_exports.append({
            "source_task": source_task,
            "name": datasource_name,
            "description": datasource_description,
            "loading_mode": loading_mode,
            "default_global_policy": default_global_policy
        })
        return self

    def create(self) -> Dict[str, Any]:
        self._create_output_datasources()
        self._generate_etl_tasks()

        trigger_params = {
            "triggerType": self._trigger_type
        }

        if self._trigger_type == "MANUAL":
            trigger_params["triggerParameters"] = self._trigger_parameters
        elif self._trigger_type == "DATA_REFRESH":
            trigger_params["datasourceIds"] = self._datasource_ids_for_refresh

        command_params = {
            "displayInformation": {
                "displayName": self._name,
                "description": self._description
            },
            "tasks": [task.to_dict() for task in self._tasks],
            "tasksWithControlPanel": [],
            "trigger": trigger_params
        }

        if self._schedule:
            command_params["schedule"] = self._schedule

        workflow = self._k.commands.create_workflow(command_params)
        self._workflow_id = workflow.get("id")

        base_url = self._k.kawa_api_url
        workspace_id = self._k.active_workspace_id
        workflow_url = f"{base_url}/workspaces/{workspace_id}/workflows/{self._workflow_id}"

        print(f"✅ Workflow '{self._name}' created successfully")
        print(f"🔗 URL: {workflow_url}")
        print(f"🆔 ID: {self._workflow_id}")

        return workflow

    def create_and_run(self, trigger_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        workflow = self.create()
        run_result = self.run(trigger_parameters=trigger_parameters)
        return {
            "workflow": workflow,
            "run": run_result
        }

    def update(self, workflow_id: str) -> Dict[str, Any]:
        self._create_output_datasources()
        self._generate_etl_tasks()

        trigger_params = {
            "triggerType": self._trigger_type
        }

        if self._trigger_type == "MANUAL":
            trigger_params["triggerParameters"] = self._trigger_parameters
        elif self._trigger_type == "DATA_REFRESH":
            trigger_params["datasourceIds"] = self._datasource_ids_for_refresh

        command_params = {
            "displayInformation": {
                "displayName": self._name,
                "description": self._description
            },
            "tasks": [task.to_dict() for task in self._tasks],
            "tasksWithControlPanel": [],
            "trigger": trigger_params
        }

        if self._schedule:
            command_params["schedule"] = self._schedule

        result = self._k.commands.update_workflow(workflow_id, command_params)
        workflow = result.get("workflow", {})
        self._workflow_id = workflow.get("id")

        print(f"✅ Workflow '{self._name}' updated successfully")
        print(f"🆔 ID: {self._workflow_id}")

        return workflow

    def _create_output_datasources(self):
        for task in self._tasks:
            if not task.output_as_datasource or task.output_datasource_id:
                continue

            indicators = self._get_task_indicators(task)

            if not indicators:
                raise Exception(f"No indicators found for task {task.task_id}. "
                                f"Ensure the underlying script or view returns valid columns/outputs.")

            ds = self._k.commands.create_workflow_datasource(indicators)
            task.with_output_as_datasource(ds['id'])
            print(f"Created datasource {ds['id']} for task {task.task_id}")

    def _get_task_indicators(self, task):
        from .workflow_tasks import PythonScriptTask, ComputeViewTask

        if isinstance(task, PythonScriptTask):
            script = self._k.entities.scripts().get_entity(task.script_id)
            return get_indicators_from_structure(script, 'script')

        if isinstance(task, ComputeViewTask):
            extended_view = self._k.get(f'{self._k.kawa_api_url}/backoffice/extended-views/{task.view_id}')
            return get_indicators_from_structure(extended_view, 'view')

        return []

    def _generate_etl_tasks(self):
        from .workflow_tasks import EtlTask

        for etl_req in self._pending_exports:
            source_task = etl_req["source_task"]

            if not source_task.output_datasource_id:
                raise Exception(f"Source task {source_task.task_id} does not have an output datasource ID yet.")

            export_ds_result = self._k.commands.create_workflow_etl_datasource(
                workflow_datasource_id=source_task.output_datasource_id,
                display_name=etl_req["name"],
                description=etl_req["description"],
                loading_mode=etl_req["loading_mode"],
                default_global_policy=etl_req["default_global_policy"]
            )
            export_ds_id = export_ds_result['dataSource']['id']
            print(f"Created ETL datasource {export_ds_id} (name: {etl_req['name']})")

            etl_task = EtlTask(
                datasource_id=export_ds_id,
                display_name=f"Export to {etl_req['name']}"
            ).with_input("input_df", source_task.task_id)

            self.add_task(etl_task)

        self._pending_exports = []

    def run(self, workflow_id: Optional[str] = None, trigger_parameters: Optional[Dict[str, Any]] = None) -> Dict[
        str, Any]:
        wf_id = workflow_id or self._workflow_id
        if not wf_id:
            raise ValueError("Workflow ID is required. Either create a workflow first or provide workflow_id.")

        result = self._k.commands.run_workflow(workflow_id=wf_id, trigger_parameters=trigger_parameters)

        print(f"✅ Workflow run started")
        return result

    def wait_for_completion(self, workflow_id: Optional[str] = None, timeout: int = 120) -> Dict[str, Any]:
        wf_id = workflow_id or self._workflow_id
        if not wf_id:
            raise ValueError("Workflow ID is required. Either create a workflow first or provide workflow_id.")

        start_time = time.time()
        while time.time() - start_time < timeout:
            history = self._k.get_workflow_run_history(wf_id)
            if history and len(history) > 0:
                last_run = history[0]
                status = last_run.get('status')
                if status in ['COMPLETED', 'SUCCESS', 'FAILURE']:
                    if status == 'FAILURE':
                        error_code = last_run.get('errorCode', '')
                        error_message = last_run.get('errorMessage', 'No error message provided')
                        error_details = f"Error Code: {error_code}" if error_code else ""
                        full_error = f"Workflow failed: {error_message}"
                        if error_details:
                            full_error += f" ({error_details})"
                        raise Exception(full_error)
                    if 'processInstanceId' in last_run:
                        last_run['id'] = last_run['processInstanceId']
                    print(f"✅ Workflow completed with status: {status}")
                    return last_run
            time.sleep(2)
        raise TimeoutError(f"Workflow {wf_id} did not complete within {timeout} seconds")

    def get_last_run_details(self, workflow_id: Optional[str] = None, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        wf_id = workflow_id or self._workflow_id
        if not wf_id:
            raise ValueError("Workflow ID is required. Either create a workflow first or provide workflow_id.")
        return self._k.get_workflow_run_history(wf_id, run_id)

    def schedule(self, workflow_id: str, schedule: dict) -> Dict[str, Any]:
        result = self._k.commands.run_command("ScheduleWorkflow", {
            "workflowId": workflow_id,
            "schedule": schedule
        })

        print(f"✅ Workflow scheduled")
        return result

    def unschedule(self, workflow_id: str) -> Dict[str, Any]:
        result = self._k.commands.run_command("ScheduleWorkflow", {
            "workflowId": workflow_id
        })

        print(f"✅ Workflow unscheduled")
        return result

    def delete(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        wf_id = workflow_id or self._workflow_id
        if not wf_id:
            raise ValueError("Workflow ID is required. Either create a workflow first or provide workflow_id.")

        result = self._k.commands.run_command("DeleteWorkflow", {
            "workflowId": wf_id
        })

        print(f"✅ Workflow deleted")
        return result


