from .application_building_utils import get_column, load_sheet
from .app_synchronizer import Synchronizer
import re

ACCEPTABLE_AGGREGATIONS = [
    'FIRST',
    'SUM',
    'AVERAGE',
    'COUNT',
    'MEDIAN',
    'COUNT_UNIQUE',
    'MIN',
    'MAX',
    'ARG_MIN',
    'ARG_MAX',
    'NOOP'
]


class Relationship:

    def __init__(self, kawa, reporter, name, model, link,
                 description=None, dataset=None, target_sheet=None,
                 ai_mode=False, session_id=None):
        self._k = kawa
        self._reporter = reporter
        self._name = name
        self._description = description
        self._dataset = dataset
        self._target_sheet = target_sheet
        self._model = model
        self._link = link
        self._cached_sheet = None
        self._columns = []
        self._ai_mode = ai_mode
        self._session_id = session_id

    @property
    def source_sheet(self):
        return self._model.sheet

    @property
    def target_sheet(self):
        return self._target_sheet if self._target_sheet else self._dataset.sheet

    @property
    def name(self):
        return self._name

    def add_join_column(self,
                        aggregation,
                        column_from_right_model,
                        new_column_in_left_model,
                        filters=None,
                        aggregation_argument=None):
        return self.add_column(
            aggregation=aggregation,
            origin_column=column_from_right_model,
            new_column_name=new_column_in_left_model,
            filters=filters,
            aggregation_argument=aggregation_argument,
        )

    def add_column(self,
                   aggregation,
                   new_column_name,
                   filters=None,
                   name=None,
                   origin_column=None,
                   aggregation_argument=None):
        uc_aggregation = aggregation.upper()
        uc_aggregation = 'FIRST' if uc_aggregation == 'ANY_VALUE' else uc_aggregation
        if uc_aggregation not in ACCEPTABLE_AGGREGATIONS:
            raise Exception('The aggregation is not known, please use one of: ' + ','.join(ACCEPTABLE_AGGREGATIONS))

        self._columns.append({
            'name': name or origin_column,
            'aggregation': uc_aggregation,
            'aggregation_argument': aggregation_argument,
            'new_column_name': new_column_name,
            'filters': filters,
        })

    def sync(self, **kwargs):
        if not self._columns:
            return

        if not self._link:
            # Entire dataset link is empty
            self._link = {}

        for column in self._columns:
            Relationship._Synchronizer(
                kawa=self._k,
                ai_mode=self._ai_mode,
                relationship=self,
                column=column,
                session_id=self._session_id,
            ).sync()

        self._reporter.report(
            object_type='Relationship',
            name=self._name,
        )

    def build_join_definition(self):
        joins = []
        for source, target in self._link.items():
            source_column = get_column(
                sheet=self.source_sheet,
                column_name=source,
                kawa=self._k,
                force_refresh_sheet=True,
                session_id=self._session_id,
            )

            target_column = get_column(
                sheet=self.target_sheet,
                column_name=target,
                kawa=self._k,
                force_refresh_sheet=True,
                session_id=self._session_id,
            )

            joins.append({
                "targetColumnId": target_column['columnId'],
                "sourceColumnId": source_column['columnId'],
            })
        return joins

    def to_ascii(self):

        source_sheet_name = self.source_sheet['displayInformation']['displayName']
        target_sheet_name = self.target_sheet['displayInformation']['displayName']

        on_clause_collector = []

        for source, target in self._link.items():
            on_clause = f'"{source_sheet_name}"."{source}"="{target_sheet_name}"."{target}"'
            on_clause_collector.append(on_clause)

        on_clauses = ' and '.join(on_clause_collector)
        ascii_representation = f'"{source_sheet_name}" LINKED WITH "{target_sheet_name}" ON ({on_clauses}):\n'

        ascii_representation += "  |\n"
        for col in self._columns:
            col_ascii = f"  |-> {col['aggregation']}({col['name']})\n"
            ascii_representation += col_ascii

        return ascii_representation.strip()

    class _Synchronizer(Synchronizer):
        def __init__(self, kawa, ai_mode, session_id, relationship, column):
            super().__init__(
                kawa=kawa,
                icon='🔗',
                entity_description=f'Relationship "{relationship.name}"',
            )
            self._relationship = relationship
            self._column = column
            self._ai_mode = ai_mode
            self._session_id = session_id

        def _load_state(self):
            if self._ai_mode:
                # State is not required in AI Mode, we will always be adding new adhoc columns
                return {}
            else:
                existing_columns = {
                    c['displayInformation']['displayName']: c
                    for c in self._relationship.source_sheet['computedColumns']
                    if c['columnNature'] == 'LINKED' and c['columnStatus'] == 'ACTIVE'
                }
                return existing_columns.get(self._column['new_column_name'])

        def _raise_if_state_invalid(self):
            ...

        def _should_create(self):
            if self._ai_mode:
                # Always create in AI Mode, because we create adHoc columns
                return True
            else:
                return self._state is None

        def _create_new_entity(self):
            source_sheet = self._relationship.source_sheet
            target_sheet = self._relationship.target_sheet

            target_column = get_column(
                sheet=target_sheet,
                column_name=self._column['name'],
                kawa=self._k,
                force_refresh_sheet=True,
                session_id=self._session_id,
            )

            column_definition = {
                "columnId": target_column['columnId'],
                "aggregation": self._column['aggregation'],
                "lookupColumnName": self._column['new_column_name'],
            }

            if self._column.get('aggregation_argument'):
                argument_column = get_column(
                    sheet=target_sheet,
                    column_name=self._column['aggregation_argument'],
                    kawa=self._k,
                    force_refresh_sheet=False,
                    session_id=self._session_id,
                )
                column_definition['optionalMeasureColumnId'] = argument_column['columnId']

            joins = self._relationship.build_join_definition()
            filters = [f.to_dict() for f in (self._column.get('filters') or [])]

            self._k.commands.run_command(
                command_name='addLookupField',
                command_parameters={
                    "filters": filters,
                    "layoutId": str(source_sheet['defaultLayoutId']),  # This is the source layout
                    "linkedSheetId": str(target_sheet['id']),  # This is the target sheet
                    "columnDefinitions": [column_definition],
                    "joins": joins,
                    "adHoc": self._ai_mode,
                    "aiContextId": self._session_id,
                }
            )

        def _update_entity(self):
            existing_lookup_column = self._state
            existing_joins = existing_lookup_column['joins']
            new_joins = self._relationship.build_join_definition()

            existing_joins_for_comparison = sorted([(j['sourceColumnId'], j['targetColumnId']) for j in existing_joins])
            new_joins_for_comparison = sorted([(j['sourceColumnId'], j['targetColumnId']) for j in new_joins])
            if existing_joins_for_comparison != new_joins_for_comparison:
                # TODO We need to update the join for this column
                ...

            # TODO: Update aggregation -> Need to upgrade definition view

            # TODO: Update the target column (We need BE support for this)

            ...

        def _build_new_state(self):
            pass
