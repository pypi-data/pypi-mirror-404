import pandas as pd

from ...client.kawa_client import KawaClient as K
from datetime import datetime, date, timedelta
import numpy as np
from faker import Faker
import json


def kawa():
    k = K(kawa_api_url='http://localhost:8080')
    k.login_with_credential(login='setup-admin@kawa.io', password='changeme')
    k.set_active_workspace_id(workspace_id='107')
    k.set_session_id(session_id='123')
    return k


research = kawa().research('Some research')
orders_model = research.register_model('4727')
events_model = research.register_model('4728')
main_model = orders_model

orders_model.create_metric(
    name='TwiceTheProfit',
    formula='"Profit" + "Profit"'
)

main_model.create_fixed_level_metric(
    name='SumOfProfitPerState',
    per='State',
    formula='SUM("Profit" + "Profit" + "Profit")',
)

main_model.create_fixed_level_metric(
    name='SumOfProfitPerStateAndSegment',
    per=['State','Segment'],
    formula='SUM("Profit" + "Profit" + "Profit")',
)

main_model.create_fixed_level_metric(
    name='SumOfProfitOverall',
    per='entire_dataset', # KEY WORD FOR NO JOINS
    formula='SUM("Profit")',
)

join1 = main_model.join(
    right_model=main_model,
    name='TransactionsWithUsers',
    on={'State': 'State'}
)

join1.add_join_column(
    column_from_right_model='Profit',
    aggregation='SUM',
    new_column_in_left_model='TotalProfitPerState'
)

rel1 = main_model.create_relationship(
    name='Rel1',
    origin_model=main_model,  # Self link
    link={'State': 'State'}
)

rel1.add_column(
    origin_column='Profit',
    aggregation='SUM',
    new_column_name='TotalProfitPerState',
    filters=[
        K.col('State').eq('California')
    ],
)

rel1.add_column(
    origin_column='Profit',
    aggregation='ARG_MAX',
    aggregation_argument='Order Date',
    new_column_name='LatestProfitPerState',
)

orders_model.create_every_level_metric(
    name='ONE !',
    formula='"Profit" / "Quantity"'
)

orders_model.create_metric(
    name='TWICE ONE',
    formula='"ONE" + "ONE"'
)

orders_model.create_metric(
    name='Foooo',
    formula='2 * "LatestProfitPerState"'
)

research.bar_chart(
    title='Profit per State',
    x='State',
    y='Profit',
    color='Segment',
    show_values=True,
    show_totals=True,
    model=orders_model,
    filters=[
        # K.col("State").in_list("California", "Ohio"),
        K.col("Profit").gt(1)
    ],
    order_by='Profit',
    order_direction='DESCENDING',
    limit=5,
)


print(research.publish_main_model(main_model=main_model))


#
# research.scatter_chart(
#     title='Order Count vs. Profit by Month',
#     granularity='Order Date',
#     x='Order ID',
#     aggregation_x='COUNT',
#     y='Profit',
#     aggregation_y='SUM',
#     color='Profit',
#     aggregation_color='SUM',
#     model=orders_model,
#     time_sampling='YEAR_AND_MONTH',
# )
#
# df = (orders_model
#       .select(
#     K.col('State'),
#     K.col('Unit Profit III').avg().alias('Average profit'),
#     K.col('Cost per State').sum().alias('Total per state'),
#     K.col('Profit per State').median().alias('Median profit per state'),
# )
#       .group_by('State')
#       .query_description('This is the description')
#       .collect())
#
# research.register_result(
#     description='Dataframe containing data about cost and profit',
#     df=df
# )
print(research.publish_results())
