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


dashboard = kawa().dashboard('Sample dashboard I')

column = dashboard.create_section(num_columns=1)

chart1 = column.line_chart(
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

column.widget_description(
    widgets=[chart1]
)

(column1, column2) = dashboard.create_section(num_columns=2)

chart2 = column1.bar_chart(
    title='Evolution of Quantity',
    x='Order Date',
    y='Quantity',
    aggregation='SUM',
    time_sampling='YEAR_AND_MONTH',
    show_values=False,
    sheet_id='3571',
)

chart3 = column1.pie_chart(
    title='Quantity per Category',
    labels='Category',
    values='Quantity',
    show_values=True,
    show_labels=True,
    doughnut=True,
    sheet_id='3571',
)

chart4 = column1.scatter_chart(
    title='Sales vs. Profit per City',
    granularity='City',
    x='Sales',
    y='Profit',
    aggregation_x='SUM',
    aggregation_y='SUM',
    color='City',
    sheet_id='3571',
)

column1.widget_description(
    widgets=[chart2, chart3, chart4]
)

chart5 = column2.scatter_chart(
    title='Profit vs. Quantity per City ⛱️',
    granularity='City',
    x='Profit',
    y='Quantity',
    color='Order ID',
    aggregation_color='COUNT',
    sheet_id='3571',
)

chart6 = column2.boxplot(
    title='Profit per Year ($)',
    x='Order Date',
    y='Profit',
    time_sampling='YEAR',
    sheet_id='3571',
)
chart7 = column2.boxplot(
    title='Profit per Sub-Category ($)',
    x='Sub-Category',
    y='Profit',
    sheet_id='3571',
)

column2.widget_description(
    widgets=[chart5, chart6, chart7]
)

dashboard.create_text_filter(
    name='filter1',
    filtered_column='State',
    sheet_id='3571',
)

meta = dashboard.publish()
print(meta)
