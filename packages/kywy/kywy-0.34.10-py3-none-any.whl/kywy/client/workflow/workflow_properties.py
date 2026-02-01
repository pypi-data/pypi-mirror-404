class TaskPropertyType:
    
    COMPUTE_TABLE = "TABLE"
    COMPUTE_NUM_ROWS = "NUM_ROWS"
    COMPUTE_SHEET_NAME = "SHEET_NAME"
    COMPUTE_VIEW_URL = "VIEW_URL"
    COMPUTE_VIEW_NAME = "VIEW_NAME"
    
    CHART_CHART = "CHART"
    CHART_IMAGE_URL = "IMAGE_URL"
    CHART_SHEET_NAME = "SHEET_NAME"
    CHART_VIEW_URL = "VIEW_URL"
    CHART_VIEW_NAME = "VIEW_NAME"
    
    PYTHON_TABLE = "TABLE"
    PYTHON_NUM_ROWS = "NUM_ROWS"
    
    AI_GENERATED_CONTENT = "GENERATED_CONTENT"
    
    REPORT_URL = "REPORT_URL"


class TriggerParameterDefinition:
    
    def __init__(self, name: str, param_type: str, default_value=None, description: str = ""):
        self.name = name
        self.id = name.lower().replace(" ", "_")
        self.param_type = param_type
        self.default_value = default_value
        self.description = description

    def to_dict(self):
        param = {
            "name": self.name,
            "id": self.id,
            "type": self.param_type,
            "description": self.description,
            "defaultValue": self.default_value
        }
        return param


class WorkflowTaskInfo:
    
    COMPUTE = {
        "TABLE": {"type": "TEXT", "name": "Grid", "outputBased": True},
        "NUM_ROWS": {"type": "INTEGER", "name": "Number of rows", "outputBased": True},
        "SHEET_NAME": {"type": "TEXT", "name": "Sheet Name", "outputBased": True},
        "VIEW_URL": {"type": "TEXT", "name": "View URL", "outputBased": True},
        "VIEW_NAME": {"type": "TEXT", "name": "View Name", "outputBased": True},
    }
    
    CHART = {
        "CHART": {"type": "TEXT", "name": "Chart", "outputBased": False},
        "IMAGE_URL": {"type": "TEXT", "name": "Image URL", "outputBased": False},
        "SHEET_NAME": {"type": "TEXT", "name": "Sheet Name", "outputBased": False},
        "VIEW_URL": {"type": "TEXT", "name": "View URL", "outputBased": False},
        "VIEW_NAME": {"type": "TEXT", "name": "View Name", "outputBased": False},
    }
    
    PYTHON = {
        "TABLE": {"type": "TEXT", "name": "Grid", "outputBased": True},
        "NUM_ROWS": {"type": "INTEGER", "name": "Number of rows", "outputBased": True},
    }
    
    AI = {
        "GENERATED_CONTENT": {"type": "TEXT", "name": "Generated Content", "outputBased": False},
    }
    
    REPORT = {
        "REPORT_URL": {"type": "TEXT", "name": "Report URL", "outputBased": False},
    }

