# vertex-forecast-poc
assets needed to successfully pilot Vertex Forecast for enterprise demand forecasting use cases


## Getting Started


1. edit [env_config.py](env_config.py)

2. Enable APIs (if needed)
 
```bash
gcloud services enable artifactregistry.googleapis.com \
    bigquery.googleapis.com \
    cloudbuild.googleapis.com \
    logging.googleapis.com \
    run.googleapis.com \
    storage-component.googleapis.com  \
    eventarc.googleapis.com \
    aiplatform.googleapis.com
```

<details>
    <summary> <strong>environment setup with Poetry</strong></summary>

1. Create new conda environment
    
```bash
export ENV_NAME=py310_vf_v1
export ENV_DISPLAY=py310_vf_v1

conda create -n $ENV_NAME -y python=3.10.16
conda activate $ENV_NAME

conda install pip
pip install -U poetry ipykernel packaging
```

2. Install the required Python packages using Poetry:
    
```bash
export DIR_NAME=poetry_dir
cd $DIR_NAME

poetry install
```

3. Add conda kernel for Wokbench Instance notebook
    
```bash
DL_ANACONDA_ENV_HOME="${DL_ANACONDA_HOME}/envs/$ENV_NAME"
echo $DL_ANACONDA_ENV_HOME

python -m ipykernel install --prefix "${DL_ANACONDA_ENV_HOME}" --name $ENV_NAME --display-name $ENV_DISPLAY
```

4. After reloading the Workbench instance (`ctrl + r`), you should see `$ENV_DISPLAY` available as a notebook kernel

</details>


<details>
    <summary> <strong>Vertex Forecast parameters</strong></summary>

> see [Training parameters for forecast models](https://cloud.google.com/vertex-ai/docs/tabular-data/forecasting-parameters)

* `TARGET_COLUMN`: The demand measurment. In our case it is the number of trips taken per day from a particular bike station - the sum of trips for a day.
* `TIME_COLUMN`: The time of demand. Expressed in the time or date units related to the granularity of the forecast exercise. In our case, demand is measured daily so the time column is prepared as a date.
* `SERIES_COLUMN` groups rows associated with the same time series
* `SPLITS_COLUMN` groups sequential rows within each time series for their purpose during the forecasting exercise
* `COVARIATE_COLUMNS` is a list of columns that measure additional features over time. Some forcasting methods can use these to imporove the understanding of trends and make better forecasts.To use a covariate for forecasting then its value needs to be know in advance to be used when making predictions, or the forecast method will need to have special handling for unknown covariates. The three types of covariate information are:
  * **Attributes**
    * Values that do not change over time but describe what the time series represents. In our case a bike station might be identified by latitude and longitude, color, number of bike slots.
  * **Covariates that are available (known) at forecast time (in advance)**
     * These are measurements that can be known ahead of time like when holidays occur, promotions, events, changes in capacity.
  * **Covariates that are unavailable (unknown) at forecast time (in advance)**
     * Measurements that change over time but are not known until the time of measurment like rain, other weather, foot traffic, and queue length. 

`FORECAST_GRANULARITY` is the frequency of measurment like `MINUTE`, `HOUR`, `DAY`, `WEEK`, `MONTH`, `YEAR`
* The data was summarized at the DAY level in the data preparation notebook
* This is the amount of time between measurments - rows
* For a different granularity, you may need to summarize the demand signal as a `SUM`, `MIN`, `MAX`, or `AVERAGE` for different time components.

`FORECAST_TEST_LENGTH`  is the number of rows allocated to the test region
* This is in the units of `FORECAST_GRANULARITY`
* The data preparation included setting this for specifying the `SPLITS_COLUMN = 'TEST'` values for each time series in `SERIES_COLUMMN`

`FORCAST_VALIDATE_LENGTH` is the number of rows allocated to the validation region
* This is in the units of `FORECAST_GRANULARITY`.
* The data preparation included setting this for specifying the `SPLITS_COLUMN = 'VALIDATE'` values for each time series in `SERIES_COLUMN`

`FORECAST_HORIZON_LENGTH` is the number of rows to forecast into the future beyond the test region
* This is in the units of `FORECAST_GRANULARITY`
* This needs to be set as an input to the forecast method

</details>


<details>
    <summary> <strong>Vertex Forecast capabilities</strong></summary>

`probabilisitic forecast`
   * traditional forecasting: single point prediction for each future timestamp
   * **probabilistic forecasting**: instead assigns the probability to every possible outcome, enabling us to quantify the uncertainty of the prediction
   * In many important domains (e.g., supply chains) probabilistic forecasts are critical for making decisions in the face of uncertainty
    
`hierarchical aggregation`
   * see docs for more: [Reduce forecasting bias with hierarchical aggregation](https://cloud.google.com/vertex-ai/docs/tabular-data/forecasting/hierarchical)
    
`Holiday regions`
   * forecasting data can exhibit irregular behaviour on days that correspond to regional holidays. If you want your model to take this effect into account, select the geographical region or regions that correspond to your input data

</details>


## Vertex Pipeline: Multicontender vs Champion 

> see [02_vf_pipelines.ipynb](notebooks/02_vf_pipelines.ipynb) to create pipeline

<img src='imgs/vf_champ_pipe_dag.png'>


## Custom metrics

*Some common metrics for evaluating forecasting effectiveness are...*

- MAPE, or Mean Absolute Percentage Error
    - $\textrm{MAPE} = \frac{1}{n}\sum{\frac{\mid(actual - forecast)\mid}{actual}}$
- MAE, or Mean Absolute Error
     - $\textrm{MAE} = \frac{1}{n}\sum{\mid(actual - forecast)\mid}$
- MAE divided by average demand so it yields a % like MAPE
    - $\textrm{pMAE} = \frac{\sum{\mid(actual - forecast)\mid}}{\sum{actual}}$
- MSE, or Mean Squared Error
    - $\textrm{MSE} = \frac{1}{n}\sum{(actual-forecast)^2}$
- RMSE, or Root Mean Squared Error
    - $\textrm{RMSE} = \sqrt{\frac{1}{n}\sum{(actual-forecast)^2}}$
- RMSE divided by average demand so it yeilds a % like MAPE
    - $\textrm{pRMSE} = \frac{\sqrt{\frac{1}{n}\sum{(actual-forecast)^2}}}{\frac{1}{n}\sum{actual}}$
    

*It can be helpful to explicity calculate these to make comparison between datasets and models fair. See below for SQL syntax...*

>```sql
>(actual_value - forecast_value) as diff
>
>
>AVG(SAFE_DIVIDE(ABS(diff), actual_value)) as MAPE,
>AVG(ABS(diff)) as MAE,
>SAFE_DIVIDE(SUM(ABS(diff)), SUM(actual_value)) as pMAE,
>AVG(POW(diff, 2)) as MSE,
>SQRT(AVG(POW(diff, 2))) as RMSE,
>SAFE_DIVIDE(SQRT(AVG(POW(diff, 2))), AVG(actual_value)) as pRMSE
>```


## Business Friendly and Interpretable Metrics for Demand Forecasting


Choosing appropriate evaluation metrics is one of the most important yet error-prone tasks for time series forecasting...

  * check the distribution of the prediction target by plotting a histogram at the intended spatial and temporal granularity
  * check whether the distribution of the target is sparse or asymmetric
  * When the distribution of prediction targets is sparse or asymmetric, it is inappropriate to use `wMAPE`, `MAE`, or `MASE` as a primary optimization criteria. 
  * `RMSE` and `WRMSSE` can be used as a primary optimization criteria despite the distribution of the prediction targets  


Characteristics of high quality evaluation metrics...

* **Interpretability**: Results should be easily interpreted by humans (i.e. `RMSE` and `MAE` are less ideal)
* **Calculation safety**: The metric should handle zero actuals properly (i.e. `MAPE` in its original form is less ideal)
* **Fair aggregation**: The metric should aggregate low-volume and high-volume demands *fairly*  
  * sometimes difficult to define *fairly* 
  * e.g., unweighted vs weighted MAPE may be meaningful in different scenarios: do we care about each product equally, or do we are about high-volume items much more than low-volume ones?
* **Stability with forecast horizon**: Changes in the length of forecasting horizon shouldn’t lead to drastically different results
* **Business Friendly**: The metric can be connected with crucial business KPIs such as revenue and profit
* **Comparability**: Optionally, the scores from different projects can be roughly compared


Common evaluation metrics in forecasting can be roughly organized into three groups...

  * scale-dependent metrics
  * percentage metrics
  * scale-free metrics
 

#### Scale-Dependent Metrics

* Mean Absolute Error (`MAE`) and Rooted Mean Square Error (`RMSE`), are two most widely used scale-dependent metrics for both forecasting and regression tasks
* Two major limitations of scale-dependent metrics are that a) the values are not human-interpretable; and that b) values from different time series or projects are not directly comparable

#### Percentage Metrics

The family of *percentage metrics*, such as **Mean Absolute Percentage Error** (`MAPE`), **Symmetric Mean Absolute Percentage Error** (`sMAPE`), and **Weighted Mean Absolute Percentage Error** (`wMAPE`) are widely used to compare forecasting performance due to advantages such as scale independence and interpretability

`MAPE` is one of the most widely used metrics for forecasting tasks. Despite its popularity, MAPE has at least the following limitations:

* **Undefined value when the measured value is 0**... techniques to apply include (a) cropping undefined values to 100% (i.e. `cropped MAPE`) and (b) excluding data values of 0 from metric calculation
* **Asymmetric error**. `MAPE` values will be different once forecast and actual values are swapped
* **Inconsistency when evaluating high and low volume demand**

> *Note: these "limitations" can be advantages depending on the application. What is appropriate for the business? Are absolute errors important or are relative errors important?*


#### Scale-free Metrics

Because of the known limitations in scale-dependent metrics and percentage metrics, Hyndman et al [1] proposed a scale-free metric named Mean Absolute Scaled Error (MASE)
* `MASE` is the precursor that inspired `WRMSSE` used in the [M5 forecasting competition](https://www.kaggle.com/c/m5-forecasting-accuracy)
* Since the numerator of `MASE` is also `MAE`, `MASE` shares similar advantages as `MAE` and `wMAPE`
* Furthermore, since the denominator of `MASE` is the performance of a naive model, `MASE` has an extra advantage of being roughly comparable across different projects
* At the same time, since `MASE` is a ratio rather than a percentage, it can not be roughly treated as an “error rate” when compared with other percentage metrics such as `wMAPE` and `sMAPE`


## References

[1] Rob J. Hyndman, and Ane B. Koehler (2006). Another look at measures of forecast accuracy. International Journal of Forecasting 22(4), pp 679-688. 


## Misc.

1. remove `__pycache__` and checkpoint files

```bash
rm -rf `find . -name "*.ipynb_checkpoints" -o -name "*.cpython-310.pyc" -o -name "__pycache__"`

find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
```

2. get status of long running operation (LRO)

```
curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://{LOCATION}-documentai.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/operations/{OPERATION_ID}"
```