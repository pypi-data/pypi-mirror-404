from typing import Any, Union, List


def _infer_kawa_type(value: Any) -> str:
    if value is None:
        return "text"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "decimal"
    elif isinstance(value, str):
        return "text"
    else:
        return "text"


class BindingValue:
    def to_dict(self):
        raise NotImplementedError


class StaticValue(BindingValue):
    def __init__(self, value: Any, value_type: str = None):
        self.value = value
        self.value_type = value_type or _infer_kawa_type(value)

    def to_dict(self):
        return {
            "type": "STATIC_VALUE",
            "value": self.value,
            "valueType": self.value_type
        }


class TaskProperty(BindingValue):
    _PROPERTY_TYPES = {
        "TABLE": "text",
        "NUM_ROWS": "integer",
        "SHEET_NAME": "text",
        "VIEW_URL": "text",
        "VIEW_NAME": "text",
        "CHART": "text",
        "IMAGE_URL": "text",
        "GENERATED_CONTENT": "text",
        "REPORT_URL": "text",
        "CSV_TABLE": "text"
    }
    
    def __init__(self, source_task_id: str, property_name: str):
        self.source_task_id = source_task_id
        self.property_name = property_name
        self.value_type = self._PROPERTY_TYPES.get(property_name, "text")

    def to_dict(self):
        return {
            "type": "TASK_PROPERTY",
            "sourceTaskId": self.source_task_id,
            "property": self.property_name,
            "valueType": self.value_type
        }


class TaskColumn(BindingValue):
    def __init__(self, source_task_id: str, column_name: str, value_type: str = "text"):
        self.source_task_id = source_task_id
        self.column_name = column_name
        self.value_type = value_type

    def to_dict(self):
        return {
            "type": "TASK_DATAFRAME_COLUMN",
            "sourceTaskId": self.source_task_id,
            "column": self.column_name,
            "valueType": self.value_type
        }


class TaskColumnAggregation(BindingValue):
    def __init__(self, source_task_id: str, column_name: str, aggregation: str, value_type: str = "decimal"):
        self.source_task_id = source_task_id
        self.column_name = column_name
        self.aggregation = aggregation
        self.value_type = value_type

    def to_dict(self):
        return {
            "type": "TASK_DATAFRAME_COLUMN_AGGREGATION_VALUE",
            "sourceTaskId": self.source_task_id,
            "column": self.column_name,
            "aggregation": self.aggregation,
            "valueType": self.value_type
        }


class TriggerParameter(BindingValue):
    def __init__(self, parameter_id: str, value_type: str = "text"):
        self.parameter_id = parameter_id
        self.value_type = value_type

    def to_dict(self):
        return {
            "type": "TRIGGER_PARAMETER",
            "parameterId": self.parameter_id,
            "valueType": self.value_type
        }


def build_parameter_binding(value: Union[BindingValue, Any, List]) -> dict:
    if isinstance(value, list):
        bindings = []
        for v in value:
            if isinstance(v, BindingValue):
                bindings.append(v.to_dict())
            else:
                bindings.append(StaticValue(v).to_dict())
        return {"bindings": bindings}
    elif isinstance(value, BindingValue):
        return {"bindings": [value.to_dict()]}
    else:
        return {"bindings": [StaticValue(value).to_dict()]}


def build_input_binding(source_task_id: str, column_mapping: dict = None) -> dict:
    return {
        "sourceTaskId": source_task_id,
        "mapping": column_mapping or {}
    }
