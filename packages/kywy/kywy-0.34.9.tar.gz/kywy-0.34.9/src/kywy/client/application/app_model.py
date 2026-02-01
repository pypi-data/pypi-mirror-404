from .app_variable import Variable
from .app_metric import Metric
from .app_relationship import Relationship


class DataModel:

    def __init__(self, kawa, reporter, name, dataset=None, sheet=None, ai_mode=False, session_id=None):
        self._dataset = dataset
        self._name = name
        self._k = kawa
        self._ai_mode = ai_mode
        self._reporter = reporter
        self._variables = []
        self._selects = []
        self._created_grid_ids = []
        self._sheet = sheet
        self._session_id = session_id

        self._relationships = []
        self._metrics = []
        self._metrics_and_relationships_in_order = []

    @property
    def sheet_id(self):
        return self._sheet['id'] if self._sheet else self._dataset.sheet_id

    @property
    def sheet(self):
        return self._sheet if self._sheet else self._dataset.sheet

    @property
    def name(self):
        return self._name

    @property
    def relationships(self):
        return self._relationships

    @property
    def metrics(self):
        return self._metrics

    def create_variable(self, name, kawa_type, initial_value):
        variable = Variable(
            kawa=self._k,
            reporter=self._reporter,
            sheet_id_supplier=lambda: self.sheet_id,
            name=name,
            kawa_type=kawa_type,
            initial_value=initial_value
        )
        self._variables.append(variable)

    def create_fixed_level_metric(self, name, per, formula):

        intermediary_metric = self.create_metric(
            name='RowLevelIntermediaryComputationFor-' + name,
            description='Intermediary result to compute fixed level ' + name,
            formula=formula,
        )

        if per == 'entire_dataset':
            link = {}
        elif isinstance(per, list):
            link = {str(p): str(p) for p in per}
        else:
            link = {str(per): str(per)}

        rel = self.create_relationship(
            name='rel for ' + name,
            link=link,
            origin_model=self,
        )
        rel.add_column(
            origin_column=intermediary_metric.name,
            aggregation='NOOP',  # Should not matter given that the intermediary metric is at group level.
            new_column_name=name,
        )

    def join(self, name, on, right_model):
        return self.create_relationship(
            name=name,
            link=on,
            target_model=right_model,
        )

    def create_relationship(self,
                            name,
                            link,
                            description=None,
                            # These two are synonyms
                            dataset=None, origin_model=None,
                            target_model=None,
                            ):
        rel = Relationship(
            kawa=self._k,
            reporter=self._reporter,
            model=self,
            name=name,
            description=description,
            dataset=dataset or origin_model,
            target_sheet=target_model.sheet if target_model else None,
            link=link,
            ai_mode=self._ai_mode,
            session_id=self._session_id,
        )
        self._relationships.append(rel)
        self._metrics_and_relationships_in_order.append(rel)
        return rel

    def create_every_level_metric(self, **kwargs):
        self.create_metric(**kwargs)

    def create_metric(self, name, description=None, formula=None, prompt=None, **kwargs):

        sql = None
        if formula:
            normalized = formula.strip().upper()
            if not normalized.startswith("SELECT"):
                sql = f"SELECT {formula}"
            else:
                sql = formula

        metric = Metric(
            kawa=self._k,
            reporter=self._reporter,
            name=name,
            description=description or sql or prompt,
            sql=sql,
            prompt=prompt,
            ai_mode=self._ai_mode,
            session_id=self._session_id,
        )

        self._metrics.append(metric)
        self._metrics_and_relationships_in_order.append(metric)
        return metric

    def select(self, *columns_or_column_names):
        select = self._k.sheet(sheet_id=self.sheet_id).select(*columns_or_column_names).session(self._session_id)
        self._selects.append(select)
        return select

    def create_views(self):
        i = 1
        for select in self._selects:
            created_grid = select.as_grid(
                standalone=False
            )
            self._created_grid_ids.append(created_grid['id'])
            i += 1

        return self._created_grid_ids

    def sync(self):
        for var in self._variables:
            var.sync()

        for rel_or_metric in self._metrics_and_relationships_in_order:
            rel_or_metric.sync(sheet=self.sheet)
