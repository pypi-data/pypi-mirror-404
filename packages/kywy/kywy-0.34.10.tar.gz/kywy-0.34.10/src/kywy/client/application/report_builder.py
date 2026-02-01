import json
from dataclasses import asdict
from .application_building_utils import info
from .report_blocks import ReportBlock
from .app_filter import TextFilter
from .app_widget import WidgetFactory
from datetime import datetime
from uuid import uuid4

NUM_COLUMNS = 32


class ReportBuilder:

    def __init__(self, kawa_client, name, layout_type, session_id=None):
        self._k = kawa_client
        self._name = name
        self._dashboard_id = None
        self._layout_type = layout_type
        self._text_filters = {}
        self._sections = []
        self._session_id = session_id
        self._widget_factory = WidgetFactory(
            kawa=kawa_client,
            dashboard_id_supplier=lambda: self._dashboard_id,
            default_sheet_id_supplier=None
        )

    def create_section(self, num_columns=1):
        new_section = ReportSection(
            widget_factory=self._widget_factory,
            num_columns=num_columns
        )
        self._sections.append(new_section)
        cols = new_section.columns
        return tuple(new_section.columns) if len(cols) > 1 else cols[0]

    def create_text_filter(self, name, filtered_column=None, sheet_id=None):
        # Merges filters with the same name
        if name not in self._text_filters:
            self._text_filters[name] = TextFilter(
                kawa=self._k,
                name=name,
                session_id=self._session_id,
            )

        self._text_filters[name].append_column(
            sheet_id_supplier=lambda: sheet_id,
            # If filtered column is not specified, rever to name
            column_name=filtered_column or name,
        )

    def publish(self):
        self._sync()
        meta = self._meta()
        return json.dumps(meta)

    def _sync(self):
        if not self._sections:
            raise Exception('No sections were added')

        self._create_dashboard()

        for text_filter in self._text_filters.values():
            text_filter.sync(
                dashboard_id=self._dashboard_id
            )

        for widget in self._get_all_widgets():
            widget.sync()

        if self._layout_type == 'REPORT':
            self._sync_report()
        elif self._layout_type == 'ONE_PAGE':
            self._sync_one_page_dashboard()

    def _sync_report(self):
        now = datetime.now()
        self._k.commands.run_command(
            command_name='replaceDashboardBlockEditorLayout',
            command_parameters={
                'dashboardId': self._dashboard_id,
                'blockEditorLayout': {
                    'version': "2.31.0-rc.7",
                    'time': round(now.timestamp() * 1000),
                    'blocks': [asdict(block) for block in self._get_all_blocks()],
                }
            }
        )

    def _sync_one_page_dashboard(self):
        current_y = 0

        # Propagate layout down to the widgets
        for section in self._sections:
            section.set_y_position(y=current_y)
            current_y = section.set_layout()

        dashboard_layout = [w.position() for w in self._get_all_widgets()]
        self._k.commands.run_command('ReplaceDashboardLayout', {
            "dashboardId": str(self._dashboard_id),
            "dashboardLayout": dashboard_layout,
        })

    def _create_dashboard(self):
        info(f"Creating new dashboard with name={self._name}")
        extended_dashboard = self._k.commands.run_command(
            command_name='createDashboard',
            command_parameters={
                "displayInformation": {
                    "displayName": self._name,
                },
                "layoutType": self._layout_type,
            }
        )
        self._dashboard_id = extended_dashboard['dashboard']['id']

    def _meta(self):
        return {
            'dashboardId': f'{self._dashboard_id}'
        }

    def _get_all_widgets(self):
        all_widgets = []
        for section in self._sections:
            all_widgets.extend(section.widgets)
        return all_widgets

    def _get_all_blocks(self):
        blocks = []
        for section in self._sections:
            blocks.extend(section.blocks)
        return blocks


class ReportSection:

    def __init__(self, widget_factory, num_columns=1):
        self._columns = []
        self._y_position = None
        for i in range(num_columns):
            column = SectionColumn(
                widget_factory=widget_factory,
                column_width=NUM_COLUMNS // num_columns,
                x_position=i * NUM_COLUMNS // num_columns,
                parent_section=self,
            )
            self._columns.append(column)

    @property
    def columns(self):
        return self._columns

    @property
    def blocks(self):
        all_blocks = []
        for column in self._columns:
            all_blocks.extend(column.blocks)
        return all_blocks

    @property
    def widgets(self):
        all_widgets = []
        for column in self._columns:
            all_widgets.extend(column.widgets)
        return all_widgets

    @property
    def y_position(self):
        return self._y_position

    def set_y_position(self, y):
        self._y_position = y

    def set_layout(self):
        max_y = 0
        for column in self._columns:
            y = column.set_layout()
            if y > max_y:
                max_y = y

        # Will be used to position the next section
        return max_y


class SectionColumn:

    def __init__(self, widget_factory, parent_section, x_position, column_width):
        self._blocks = []
        self._widgets = []
        self._widget_factory = widget_factory

        # Pointer to the section to which the section belongs
        # (Will be used to retrieve its position)
        self._parent_section = parent_section

        # Position of the column on the x-axis and width of the column
        self._current_x = x_position
        self._width = column_width

        # This will be used to track the position of the current widget
        # And incremented each time we add a new one within that column
        self._current_y = 0

    @property
    def widgets(self):
        return self._widgets

    @property
    def blocks(self):
        return self._blocks

    def header1(self, content):
        self._add_block(ReportBlock.header(1, content))

    def header2(self, content):
        self._add_block(ReportBlock.header(2, content))

    def header3(self, content):
        self._add_block(ReportBlock.header(3, content))

    def paragraph(self, content):
        self._add_block(ReportBlock.content('paragraph', 'text', content))

    def widget_description(self, widgets=None):
        widget_singular_or_plural = "charts" if len(widgets) != 1 else "chart"
        prompt = f'Generate a concise and precise one paragraph summary of the above {widget_singular_or_plural}'
        widget = self._widget_factory.ai_widget(
            prompt=prompt,
            widget_id_list=[w.widget_id for w in widgets],
        )
        self._add_block(self._init_block(widget, block_type='aiBlock'))
        return widget

    def code(self, content):
        self._add_block(ReportBlock.content('code', 'code', content))

    def line_chart(self, **kwargs):
        chart = self._widget_factory.line_chart(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def bar_chart(self, **kwargs):
        chart = self._widget_factory.bar_chart(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def indicator_chart(self, **kwargs):
        chart = self._widget_factory.indicator_chart(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def boxplot(self, **kwargs):
        chart = self._widget_factory.boxplot(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def scatter_chart(self, **kwargs):
        chart = self._widget_factory.scatter_chart(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def pie_chart(self, **kwargs):
        chart = self._widget_factory.pie_chart(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def table(self, **kwargs):
        chart = self._widget_factory.table(**kwargs)
        self._add_block(self._init_block(chart, block_type='kawaEmbed'))
        return chart

    def get_widget(self, block_id):
        return self._block_id_to_widget_dict.get(block_id)

    def set_layout(self):
        self._current_y = self._parent_section.y_position
        for widget in self.widgets:
            widget.set_position(
                x=self._current_x,
                y=self._current_y,
                width=self._width,
            )

            self._current_y += widget.compute_height(self._width)

        return self._current_y

    def _add_block(self, block):
        self._blocks.append(block)

    def _init_block(self, widget, block_type):
        self._widgets.append(widget)
        return ReportBlock(
            id=ReportBlock.generate_random_id(),
            type=block_type,
            data={'widgetId': widget.widget_id}
        )
