import pandas as pd

from ...client.kawa_client import KawaClient
from ...client.kawa_decorators import kawa_tool

from datetime import datetime, date, timedelta
import numpy as np
from faker import Faker


def kawa():
    k = KawaClient(kawa_api_url='http://localhost:4200')
    k.set_api_key(api_key_file='/Users/emmanuel/doc/local-pristine/.key')
    k.set_active_workspace_id(workspace_id='79')
    return k


report = kawa().report('Sample report III')
main = report.create_section(num_columns=1)

main.header1('Main Title here')

main.code('''
@staticmethod
def _content(content_type, content_name, content):
    return ReportBlock(
        id=self._generate_random_id(),
        type=content_type,
        data={
            content_name: content
        }
    )
''')

main.header2('Subtitle now')

main.header3('Smaller title')
main.paragraph('Some text for the first paragraph. This is very interesting 😁.')
main.paragraph('Some text for the second paragraph. Not so good this time 🍔.')

main.header3('Smaller title')
main.paragraph('Some text for the third paragraph. This is very interesting 💎.')
main.paragraph('Some text for the fourth paragraph. Not so good this time 🏓.')

main.paragraph('''
Lorem ipsum dolor sit amet, consectetur adipiscing elit, 
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
''')

widget1 = main.line_chart(
    title='Evolution of Profit and Sales ($)',
    x='Order Date',
    y=('Profit', 'Sales'),
    aggregation=('SUM', 'SUM'),
    time_sampling='YEAR_AND_MONTH',
    show_values=False,
    area=True,
    fill_in_temporal_gaps=True,
    sheet_id='3571',
)

main.widget_description(
    widgets=[widget1]
)

widget2 = main.bar_chart(
    title='Evolution of Quantity',
    x='Order Date',
    y='Quantity',
    aggregation='SUM',
    time_sampling='YEAR_AND_MONTH',
    show_values=False,
    sheet_id='3571',
)

widget3 = main.scatter_chart(
    title='Profit vs. Quantity per City ⛱️',
    granularity='City',
    x='Profit',
    y='Quantity',
    color='Order ID',
    aggregation_color='COUNT',
    sheet_id='3571',
)

main.widget_description(
    widgets=[widget2, widget3]
)

main.pie_chart(
    title='Quantity per Category',
    labels='Category',
    values='Quantity',
    show_values=True,
    show_labels=True,
    doughnut=True,
    sheet_id='3571',
)

main.boxplot(
    title='Profit per Year ($)',
    x='Order Date',
    y='Profit',
    time_sampling='YEAR',
    sheet_id='3571',
)
main.boxplot(
    title='Profit per Sub-Category ($)',
    x='Sub-Category',
    y='Profit',
    sheet_id='3571',
)

main.scatter_chart(
    title='Sales vs. Profit per City',
    granularity='City',
    x='Sales',
    y='Profit',
    aggregation_x='SUM',
    aggregation_y='SUM',
    color='City',
    sheet_id='3571',
)

main.table(
    title='Data',
    sheet_id='3571',
)

report.create_text_filter(
    name='filter1',
    filtered_column='State',
    sheet_id='3571',
)

meta = report.publish()
print(meta)
