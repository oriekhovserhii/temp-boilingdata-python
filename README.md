# BoilingData Python SDK

## IMPORTANT
This is a WIP and may not work correctly

## TODO
- Refactor 
- Finish process to release to PyPi https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56 -> "Upload your package to PyPi"

## Installation

INTERIM UNTIL SUBMITTED TO PyPi: Install dependencies with pip install -r requirements.txt

```shell
pip install boilingdata
```

## Basic Examples

`query()` method can be used to await for the results directly.

```python
import asyncio
from boilingdata.boilingdata import BoilingData
import os

async def main():
    username = os.environ.get('BD_USERNAME')
    password = os.environ.get('BD_PASSWORD')
    region = "eu-west-1"

    bdInstance = BoilingData(username, password, region)

    # Connect to the BoilingData WebSocket
    await bdInstance.connect()

    # Run a query and process the results
    sql_query = "SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;"
    keys = ["s3://boilingdata-demo/demo.parquet", "s3://boilingdata-demo/demo2.parquet"]
    rows = await bdInstance.query(sql_query, keys)

    await bdInstance.close()
```

`exec_query()` uses callbacks.

```python
import asyncio
from boilingdata.boilingdata import BoilingData
import os

async def main():
    username = os.environ.get('BD_USERNAME')
    password = os.environ.get('BD_PASSWORD')
    region = "eu-west-1"

    bdInstance = BoilingData(username, password, region)

    # Connect to the BoilingData WebSocket
    await bdInstance.connect()

    # Run a query and process the results
    sql_query = "SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;"
    keys = ["s3://boilingdata-demo/demo.parquet", "s3://boilingdata-demo/demo2.parquet"]
    callbacks = {
        "onLogInfo": lambda msg: print("Info:", msg),
        "onLogError": lambda msg: print("Error:", msg),
        "onData": lambda msg: print("Data received:", msg),
        "onQueryFinished": lambda msg: print("Query finished:", msg),
    }
    query = await bdInstance.exec_query(sql_query, keys, callbacks)
    await query.wait()

    await bdInstance.close()
```

### Callbacks

The SDK uses the BoilingData Websocket API in the background, meaning that events can arrive at any time. We use a range of global and query-specific callbacks to allow you to hook into the events that you care about.

All callbacks work in both the global scope and the query scope; i.e. global callbacks will always be executed when a message arrives, query callbacks will only be executed when messages relating to that query arrive.

- onRequest - This event happens when your application sends a request to BoilingData
- onData - Query data response. A single query may have many onData events as processing is parallelised in the background.
- onQueryFinished - The processing of data has completed, and you should not expect any further onData events (although more info messages may arrive)
- onLambdaEvent - the status of your datasets, i.e. warm, warmingUp, shutdown
- onSocketOpen - executed when the socket API successfully opens (so it is safe to start sending SQL queries)
- onSocketClose - executed when the socket API has closed (intentionally or not)
- onInfo - information about a query - connection time, query time, execution time, etc.
- onLogError - Log Errors, such as SQL syntax errors.
- onLogWarn - Log warning messages
- onLogInfo - Log info messages
- onLogDebug - Log debug messsages

#### Setting Global Callbacks

Global callbacks can be set when creating the BoilingData instance.

```python
BoilingData(
    username=username,
    password=password,
    region=region,
    global_callbacks={
        "onRequest": lambda req: (print("A new request has been made with ID", req["requestId"]), print("something else"))[0],
        "onQueryFinished": lambda req: print("Request complete!", req["requestId"]),
        "onLogError": lambda message: print("LogError", message),
        "onSocketOpen": lambda: print("The socket has opened!"),
        "onLambdaEvent": lambda message: print("Change in status of dataset: ", message),
    },
)
```

#### Setting Query-level Callbacks

Query callbacks are set when creating the query

```python
bdInstance.exec_query(
    sql="SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;",
    callbacks={
        "onRequest": lambda req: (print("A new request has been made with ID", req["requestId"]), print("something else"))[0],
        "onQueryFinished": lambda req: print("Request complete!", req["requestId"]),
        "onLogError": lambda message: print("LogError", message),
    }
)
```

## Using `keys`

BoilingData works best for running the same query against many files (for example, creating a historical trend from a dataset that is partitioned by date). To achieve this, you can use the `keys` array to specify a list of files to query, and the string `s3://KEY` in place of the file location in the SQL query:

```python
bdInstance.exec_query(
    sql="SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;",
    keys=[
    "s3://bucket/data/2022-01-01.parquet",
    "s3://bucket/data/2022-01-02.parquet",
    "s3://bucket/data/2022-01-03.parquet",
])
```

Results are streamed as soon as they are ready, so it is unlikely that you will recieve results in the same order that you specified the files.

If you do not need to query multiple files, then you do not need to specify the keys, for instance `SELECT COUNT(*) as rowCount FROM parquet_scan('s3://bucket/data/2022-01-01.parquet');`.

You can also now query Glue (Hive) Tables:

```python
bdInstance.exec_query(
    sql="SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;",
    keys=["glue.default.nyctaxis"]
)
```
