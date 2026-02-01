import uuid
from typing import Optional, Dict, List, Any
from ..workflow_bindings import build_parameter_binding, build_input_binding


class WorkflowTask:
    
    def __init__(self, 
                 task_type: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 description: str = ""):
        self.task_type = task_type
        self.task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self.display_name = display_name or task_type
        self.description = description
        self.input_bindings = {}
        self.parameter_bindings = {}
        self.continue_if_empty = True
        self.continue_if_too_many_rows = True
        self.num_rows_limit = 50000
        self.output_as_datasource = False
        self.output_datasource_id = None

    def with_display_name(self, name: str) -> 'WorkflowTask':
        self.display_name = name
        return self

    def with_description(self, description: str) -> 'WorkflowTask':
        self.description = description
        return self

    def with_input(self, input_name: str, source_task_id: str, column_mapping: Optional[Dict[str, str]] = None) -> 'WorkflowTask':
        self.input_bindings[input_name] = build_input_binding(source_task_id, column_mapping)
        return self

    def with_parameter(self, parameter_name: str, value: Any) -> 'WorkflowTask':
        self.parameter_bindings[parameter_name] = build_parameter_binding(value)
        return self

    def with_continue_condition(self, 
                                continue_if_empty: bool = True,
                                continue_if_too_many_rows: bool = True,
                                num_rows_limit: int = 50000) -> 'WorkflowTask':
        self.continue_if_empty = continue_if_empty
        self.continue_if_too_many_rows = continue_if_too_many_rows
        self.num_rows_limit = num_rows_limit
        return self

    def with_output_as_datasource(self, datasource_id: Optional[str] = None) -> 'WorkflowTask':
        self.output_as_datasource = True
        self.output_datasource_id = datasource_id
        return self

    def then(self, next_task: 'WorkflowTask', input_name: str = 'input_df', column_mapping: Optional[Dict[str, str]] = None) -> 'WorkflowTask':
        next_task.with_input(input_name, self.task_id, column_mapping)
        return next_task

    def to_dict(self) -> dict:
        task_dict = {
            "type": self.task_type,
            "id": self.task_id,
            "displayInformation": {
                "displayName": self.display_name,
                "description": self.description
            },
            "continueCondition": {
                "continueIfEmpty": self.continue_if_empty,
                "continueIfTooManyRows": self.continue_if_too_many_rows,
                "numRowsLimit": self.num_rows_limit
            },
            "outputAsDataSource": self.output_as_datasource
        }

        if self.input_bindings:
            task_dict["inputBindings"] = self.input_bindings

        if self.parameter_bindings:
            task_dict["parameterBindings"] = self.parameter_bindings

        if self.output_datasource_id:
            task_dict["outputDataSourceId"] = self.output_datasource_id

        return task_dict


class PythonScriptTask(WorkflowTask):
    
    def __init__(self, 
                 script_id: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="PYTHON",
            task_id=task_id,
            display_name=display_name or "Run Python Script"
        )
        self.script_id = script_id

    def to_dict(self) -> dict:
        task_dict = super().to_dict()
        task_dict["scriptId"] = self.script_id
        return task_dict


class ComputeViewTask(WorkflowTask):
    
    def __init__(self, 
                 view_id: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="COMPUTE",
            task_id=task_id,
            display_name=display_name or "Transform Data"
        )
        self.view_id = view_id

    def to_dict(self) -> dict:
        task_dict = super().to_dict()
        task_dict["viewId"] = self.view_id
        return task_dict


class ChartTask(WorkflowTask):
    
    def __init__(self, 
                 view_id: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="CHART",
            task_id=task_id,
            display_name=display_name or "Create Chart"
        )
        self.view_id = view_id

    def to_dict(self) -> dict:
        task_dict = super().to_dict()
        task_dict["viewId"] = self.view_id
        return task_dict


class AiTask(WorkflowTask):
    
    def __init__(self, 
                 prompt: Any,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="AI",
            task_id=task_id,
            display_name=display_name or "Generate AI Content"
        )
        self.with_parameter("prompt", prompt)

    def to_dict(self) -> dict:
        return super().to_dict()


class EmailTask(WorkflowTask):
    
    def __init__(self, 
                 to: Any,
                 subject: Any,
                 body: Any,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="EMAIL",
            task_id=task_id,
            display_name=display_name or "Send Email"
        )
        self.with_parameter("beneficiaries", to)
        self.with_parameter("subject", subject)
        self.with_parameter("body", body)

    def to_dict(self) -> dict:
        return super().to_dict()


class ReportTask(WorkflowTask):
    
    def __init__(self, 
                 report_id: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="REPORT",
            task_id=task_id,
            display_name=display_name or "Generate Report"
        )
        self.report_id = report_id
        self.report_parameters = {}

    def with_report_parameters(self, parameters: Dict[str, Any]) -> 'ReportTask':
        self.report_parameters.update(parameters)
        return self

    def to_dict(self) -> dict:
        task_dict = super().to_dict()
        task_dict["reportId"] = self.report_id
        if self.report_parameters:
            task_dict["reportParameters"] = self.report_parameters
        return task_dict


class EtlTask(WorkflowTask):
    
    def __init__(self, 
                 datasource_id: str,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="ETL",
            task_id=task_id,
            display_name=display_name or "Export to Datasource"
        )
        self.datasource_id = datasource_id

    def to_dict(self) -> dict:
        task_dict = super().to_dict()
        task_dict["dataSourceId"] = self.datasource_id
        return task_dict


class Condition:
    def __init__(self, join_with: str = "AND"):
        self.join_with = join_with
        self.items = []

    def add_condition_item(self, operator: str, operands: List[Any]) -> 'Condition':
        self.items.append({"operator": operator, "operands": operands})
        return self

    @staticmethod
    def equals(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("EQUALS", [left, right])

    @staticmethod
    def does_not_equal(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("DOES_NOT_EQUAL", [left, right])

    @staticmethod
    def is_empty(value: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_EMPTY", [value])

    @staticmethod
    def is_not_empty(value: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_NOT_EMPTY", [value])

    @staticmethod
    def strictly_greater_than(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("STRICTLY_GREATER_THAN", [left, right])

    @staticmethod
    def strictly_lesser_than(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("STRICTLY_LESSER_THAN", [left, right])

    @staticmethod
    def greater_than_or_equals(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("GREATER_THAN_OR_EQUALS", [left, right])

    @staticmethod
    def lesser_than_or_equals(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("LESSER_THAN_OR_EQUALS", [left, right])

    @staticmethod
    def begins_with(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("BEGINS_WITH", [left, right])

    @staticmethod
    def ends_with(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("ENDS_WITH", [left, right])

    @staticmethod
    def contains(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("CONTAINS", [left, right])

    @staticmethod
    def does_not_begin_with(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("DOES_NOT_BEGIN_WITH", [left, right])

    @staticmethod
    def does_not_end_with(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("DOES_NOT_END_WITH", [left, right])

    @staticmethod
    def does_not_contain(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("DOES_NOT_CONTAIN", [left, right])

    @staticmethod
    def is_after(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_AFTER", [left, right])

    @staticmethod
    def is_before(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_BEFORE", [left, right])

    @staticmethod
    def is_on_or_after(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_ON_OR_AFTER", [left, right])

    @staticmethod
    def is_on_or_before(left: Any, right: Any, join_with: str = "AND") -> 'Condition':
        return Condition(join_with).add_condition_item("IS_ON_OR_BEFORE", [left, right])

    def to_dict(self) -> Dict[str, Any]:
        from ..workflow_bindings import StaticValue, BindingValue

        def _to_binding_dict(op):
            if isinstance(op, dict):
                return op
            if isinstance(op, BindingValue):
                return op.to_dict()
            return StaticValue(op).to_dict()

        return {
            "joinWith": self.join_with,
            "items": [
                {
                    "operator": item["operator"],
                    "operands": [_to_binding_dict(op) for op in item["operands"]]
                }
                for item in self.items
            ]
        }

class Branch:
    def __init__(self, 
                 name: str, 
                 tasks: List[WorkflowTask]):
        self.name = name
        self.tasks = tasks
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "displayInformation": {
                "displayName": self.name,
                "description": ""
            },
            "tasks": [task.to_dict() for task in self.tasks]
        }

class IfElseTask(WorkflowTask):
    def __init__(self, 
                 name: str,
                 task_id: Optional[str] = None):
        super().__init__("IF_ELSE", task_id, name)
        self.conditional_branches = []
        self.else_branch = None

    def add_branch(self, condition, tasks: List[WorkflowTask], name: str = "Branch") -> 'IfElseTask':
        condition_dict = condition.to_dict() if isinstance(condition, Condition) else condition
        branch_dict = {
            "condition": condition_dict,
            "branch": Branch(name, tasks).to_dict()
        }
        self.conditional_branches.append(branch_dict)
        return self

    def set_else_branch(self, tasks: List[WorkflowTask], name: str = "Else") -> 'IfElseTask':
        self.else_branch = Branch(name, tasks).to_dict()
        return self

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["conditionalBranches"] = self.conditional_branches
        if self.else_branch:
            d["elseBranch"] = self.else_branch
        return d


class RoutingTask(WorkflowTask):
    def __init__(self,
                 name: str,
                 task_id: Optional[str] = None):
        super().__init__("ROUTING", task_id, name)
        self.compute_branches = []

    def add_branch(self, compute_task: ComputeViewTask, branch_tasks: List[WorkflowTask], name: str = "Branch") -> 'RoutingTask':
        self.compute_branches.append({
            "compute": compute_task.to_dict(),
            "branch": Branch(name, branch_tasks).to_dict()
        })
        return self

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["computeBranches"] = self.compute_branches
        return d


class GenerateOutputTask(WorkflowTask):
    
    def __init__(self, 
                 content: Any,
                 task_id: Optional[str] = None,
                 display_name: Optional[str] = None):
        super().__init__(
            task_type="GENERATE_OUTPUT",
            task_id=task_id,
            display_name=display_name or "Generate Output"
        )
        self.with_parameter("param_content", content)

    def to_dict(self) -> dict:
        return super().to_dict()
