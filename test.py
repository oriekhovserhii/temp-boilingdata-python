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
    sql_query = "SELECT 's3://KEY' AS key, COUNT(*) AS count FROM parquet_scan('s3://KEY') GROUP BY key;"
    keys = ["s3://boilingdata-demo/demo.parquet", "s3://boilingdata-demo/demo2.parquet"]
    # Run a query and process the results
    callbacks = {
        "onLogInfo": lambda msg: print("Info:", msg),
        "onLogError": lambda msg: print("Error:", msg),
        "onData": lambda msg: print("Data received:", msg),
        "onQueryFinished": lambda msg: print("Query finished:", msg),
    }
    query_finished_event = await bdInstance.exec_query(sql_query, keys, callbacks)
    await query_finished_event.wait()

    await bdInstance.close()
    # bd = BoilingData(username, password, region)

    # # Connect to the BoilingData WebSocket
    # await bd.connect()

    # # Run a query and process the results
    # sql_query = "SELECT count(*) FROM parquet_scan('s3://boilingdata-demo/demo.parquet') LIMIT 2;"
    # out = await bd.query(sql_query)
    # print("MYOUT", out)
    # callbacks = {
    #     "onLogInfo": lambda msg: print("Info:", msg),
    #     "onLogError": lambda msg: print("Error:", msg),
    #     "onData": lambda msg: print("Data received:", msg),
    #     "onQueryFinished": lambda msg: print("Query finished:", msg),
    # }
    # await bd.exec_query(sql_query, callbacks=callbacks)
    # query_finished_event = await bd.exec_query(sql_query, callbacks=callbacks)
    # await query_finished_event.wait()
    
    # await bdInstance.close()

if __name__ == "__main__":
    asyncio.run(main())