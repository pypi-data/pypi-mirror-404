from .app_synchronizer import Synchronizer
from .application_building_utils import load_sheet, get_column


class TextFilter:

    def __init__(self, kawa, name, session_id=None, reporter=None):
        self._k = kawa
        self._reporter = reporter
        self._name = name
        self._session_id = session_id
        self._columns = []

    @property
    def name(self):
        return self._name

    @property
    def columns(self):
        return self._columns

    def append_column(self, sheet_id_supplier, column_name):
        self._columns.append({
            'sheet_id_supplier': sheet_id_supplier,
            'name': column_name
        })

    def sync(self, extended_application=None, dashboard_id=None):
        TextFilter._Synchronizer(
            kawa=self._k,
            text_filter=self,
            application_id=extended_application['application']['id'] if extended_application else None,
            dashboard_id=dashboard_id,
            control_panel=extended_application['extendedControlPanel'] if extended_application else None,
        ).sync()

    class _Synchronizer(Synchronizer):
        def __init__(self, kawa, text_filter, control_panel=None, session_id=None, application_id=None,
                     dashboard_id=None):
            super().__init__(
                kawa=kawa,
                icon='🚦',
                entity_description=f'Filter "{text_filter.name}"',
            )
            self._filter = text_filter
            self._session_id = session_id
            self._control_panel = control_panel
            self._application_id = application_id
            self._dashboard_id = dashboard_id
            if bool(application_id) == bool(dashboard_id):
                raise Exception('We need one (and only one) of application_id and dashboard_id')

        def _load_state(self):
            if not self._control_panel:
                return None

            filter_controls = {
                c['displayInformation']['displayName']: c
                for c in self._control_panel['controls']
                if c['controlType'] == 'FILTER_CONTROL'
            }
            return filter_controls.get(self._filter.name)

        def _raise_if_state_invalid(self):
            ...

        def _should_create(self):
            return not self._state

        def _create_new_entity(self):
            apply_to = self._build_apply_to()
            command_parameters = {
                "filterConfiguration": {
                    "filterType": "TEXT_FILTER",
                    "applyTo": apply_to,
                    "filterOutNullValues": True
                },
                "controlConfiguration": {
                    "displayInformation": {
                        "displayName": self._filter.name,
                        "description": ""
                    },
                    "controlParameters": {
                        "mode": "ValuesList",
                        "multiSelection": True,
                        "size": "md"
                    }
                }
            }

            if self._application_id:
                command_parameters["applicationId"] = str(self._application_id)
            if self._dashboard_id:
                command_parameters["dashboardId"] = str(self._dashboard_id)

            self._k.commands.run_command('createFilterControlWithLinkedFilter', command_parameters)

        def _update_entity(self):
            ...

        def _build_new_state(self):
            ...

        def _build_apply_to(self):
            apply_to = []
            for column in self._filter.columns:
                sheet_id_supplier = column['sheet_id_supplier']
                column_name = column['name']

                sheet_id = sheet_id_supplier()
                sheet = load_sheet(self._k, sheet_id)
                column = get_column(sheet, column_name, session_id=self._session_id)

                apply_to.append({
                    'columnId': column['columnId'],
                    'sheetId': str(sheet_id),
                })
            return apply_to
