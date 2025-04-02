from prophet import Prophet
from google.cloud import bigquery
import pandas as pd
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import argparse

# import parameters
parser = argparse.ArgumentParser()
parser.add_argument('--project', dest = 'project', type = str)
parser.add_argument('--bq_input', dest = 'bq_input', type = str)
parser.add_argument('--bq_output', dest = 'bq_output', type = str)
parser.add_argument('--horizon', type=int)
parser.add_argument('--target_column', type = str)
parser.add_argument('--series_column', type = str)
parser.add_argument('--time_column', type = str)
parser.add_argument('--cov_unavailable', nargs='*')
parser.add_argument('--cov_available', nargs='*')
parser.add_argument('--cov_attribute', nargs='*')

parser.add_argument('--yearly', action='store_true')
parser.add_argument('--no-yearly', action='store_false')
parser.set_defaults(yearly=False)

args = parser.parse_args()
project = args.project
bq_input = args.bq_input
bq_output = args.bq_output

# client for BQ
bq = bigquery.Client(project = project)

# input data - from BQ
query = f"SELECT * FROM `{bq_input}` ORDER by {args.series_column}, {args.time_column}"
source = bq.query(query = query).to_dataframe()

# preprocess data - as a list of dataframes for each series
seriesNames = source[args.series_column].unique().tolist()
seriesFrames = []
for s in seriesNames:
    frame = source[
        (source[args.series_column] == s) & (source['splits']!='TEST')
    ][[
        args.time_column, args.target_column
    ]].rename(columns = {args.time_column:'ds', args.target_column:'y'})
    seriesFrames.append(frame)

# function to run a prophet fit & forecast
def run_prophet(series):
    if args.yearly:
        p = Prophet(weekly_seasonality=True, yearly_seasonality=True)
    else:
        p = Prophet(weekly_seasonality=True)
    p.add_country_holidays(country_name='US')
    p.fit(series)
    f = p.make_future_dataframe(periods = args.horizon, include_history = False)
    f = p.predict(f)
    return f[['ds','yhat','yhat_lower','yhat_upper']]

# run the series in a thread pool for multiprocessing
pool = Pool(cpu_count())
predictions = list(tqdm(pool.imap(run_prophet, seriesFrames), total = len(seriesFrames)))
pool.close()
pool.join()

# postprocess data - add series name back to dataframe and concatenate all into one dataframe
for i, p in enumerate(predictions):
    p[args.series_column] = seriesNames[i]
output = pd.concat(predictions)

# output data - to BQ
output.to_gbq(f"{bq_output}", f"{bq_input.split('.')[0]}", if_exists = 'replace')

# Transform final data in BQ - merge with original input
query = f"""
CREATE OR REPLACE TABLE `{bq_output}` AS
WITH
    SOURCE AS (
        SELECT *
        FROM `{bq_input}`
        WHERE splits='TEST'
    ),
    PROPHET AS (
        SELECT {args.series_column}, DATE(ds) as {args.time_column}, yhat, yhat_lower, yhat_upper
        FROM `{bq_output}`
    )
SELECT *
FROM PROPHET
LEFT OUTER JOIN SOURCE
USING ({args.series_column}, {args.time_column})
ORDER by {args.series_column}, {args.time_column}
"""
Tjob = bq.query(query = query)
Tjob.result()
(Tjob.ended-Tjob.started).total_seconds()
