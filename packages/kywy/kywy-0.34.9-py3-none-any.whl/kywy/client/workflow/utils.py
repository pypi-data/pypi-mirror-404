from typing import List, Dict, Any

def get_indicators_from_structure(structure: Dict[str, Any], structure_type: str = 'view') -> List[Dict[str, Any]]:
    if structure_type == 'script':
        return _get_script_indicators(structure)
    elif structure_type == 'datasource':
        return _get_datasource_indicators(structure)
    elif structure_type == 'layout_sheet':
        return _get_layout_sheet_indicators(structure)
    elif structure_type == 'view':
        return _get_view_indicators(structure)
    return []


def _get_view_indicators(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    indicators = []
    for field in structure.get('fields', []):
        field_id = field.get('fieldId', '')
        display_info = field.get('displayInformation', {})
        indicators.append({
            'indicatorId': field_id,
            'displayInformation': {
                'displayName': display_info.get('displayName', ''),
                'description': display_info.get('description', '')
            },
            'type': field.get('type', 'text'),
            'includedInDefaultLayout': True
        })
    return indicators


def _get_script_indicators(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    indicators = []
    script_metadata = structure.get('scriptMetadata', {})
    type_mapping = {
        'decimal': 'decimal', 'float': 'decimal', 'double': 'decimal',
        'integer': 'integer', 'int': 'integer', 'long': 'integer',
        'boolean': 'boolean', 'bool': 'boolean',
        'date': 'date', 'datetime': 'date', 'timestamp': 'date'
    }
    
    for output in script_metadata.get('outputs', []):
        output_name = output.get('name', '')
        indicators.append({
            'indicatorId': output_name,
            'displayInformation': {'displayName': output_name, 'description': ''},
            'type': type_mapping.get(output.get('type', 'text'), 'text'),
            'includedInDefaultLayout': True
        })
    return indicators


def _get_datasource_indicators(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    indicators = []
    for ind in structure.get('indicators', []):
        indicators.append({
            'indicatorId': ind.get('indicatorId'),
            'displayInformation': {
                'displayName': ind.get('displayInformation', {}).get('displayName', ''),
                'description': ind.get('displayInformation', {}).get('description', '')
            },
            'type': ind.get('type', 'text'),
            'includedInDefaultLayout': True,
            'key': ind.get('key')
        })
    
    if 'columns' in structure:
         columns = structure.get('columns', [])
         for column in columns:
            if column.get('columnType') == 'INDICATOR':
                col_id = column.get('columnId')
                col_id_str = col_id.get('id', '') if isinstance(col_id, dict) else (str(col_id) if col_id else column.get('key', ''))

                indicator = {
                    'indicatorId': col_id_str or column.get('key'),
                    'displayInformation': {
                        'displayName': column.get('displayInformation', {}).get('displayName', ''),
                        'description': column.get('displayInformation', {}).get('description', '')
                    },
                    'type': column.get('type', 'text'),
                    'includedInDefaultLayout': True
                }
                if column.get('key'):
                    indicator['key'] = column.get('key')
                indicators.append(indicator)
    return indicators


def _get_layout_sheet_indicators(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    indicators = []
    layout = structure.get('layout', {})
    sheet = structure.get('sheet', {})
    
    used_column_ids = {
        field.get('columnId', {}).get('id', '') if isinstance(field.get('columnId'), dict) else str(field.get('columnId', ''))
        for field in layout.get('fields', [])
    }
    
    for column in sheet.get('indicatorColumns', []):
        column_id_obj = column.get('columnId', {})
        column_id_str = column_id_obj.get('id', '') if isinstance(column_id_obj, dict) else str(column_id_obj)
        
        if not used_column_ids or column_id_str in used_column_ids:
            indicator = {
                'indicatorId': column_id_str,
                'displayInformation': {
                    'displayName': column.get('displayInformation', {}).get('displayName', ''),
                    'description': column.get('displayInformation', {}).get('description', '')
                },
                'type': column.get('type', 'text'),
                'includedInDefaultLayout': True
            }
            if column.get('key'):
                indicator['key'] = column.get('key')
            indicators.append(indicator)
    return indicators
