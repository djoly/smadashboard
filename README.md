

## Running the Sunny Boy Data Collection Script

Below is an example using the -t flag. Passing the -t flag will result in the script using
some dummy test data rather than using real sunny boy data.

```
$ python save-sunny-boy-power-data.py --sunnyboyhost invhostname --invid sunnyboy1 --redishost localhost --redispassword nimda1234 --influxdbhost http://localhost:8086 --influxdbtoken 3Nj5jtGSROxcuJg_r-4CJKVIqql_5NLSYjPEuMCzNKpdTqKAna57JdkW0c_UldrEvRepVvWKM0J_Mx567972vQ== --influxdborg pv_data --influxdbbucket pv_data --lat 36.17 --lon -82.86 -t
```

## Running the Sunny Island Data Collection Script

```
$ python save-sunny-island-data.py --mqtthost localhost --mqtttopic "sunnyisland/1260000000" --redishost localhost --redispassword nimda1234 --influxdbhost http://localhost:8086 --influxdbtoken H-FM6r88G_9AQjHYBZFX0Ipg4knIpr2Kw7rZK24HRUMw0DaefTuuCnZerXXjgjMP3CGqsZ95xEEz28WsC8BAjA== --influxdborg pv_data --influxdbbucket pv_data
```

## Running the Mock Sunny Island Data Publisher

To test the sunny island data collection script without yasdi2mqtt and a connection to the real inverter, run the mock data script. This script will publish Sunny Island data to mqtt. Make sure the host and topic match those passed to the colletion script.

```
$ python mock_sunny_island_data_publisher.py --mqtthost localhost --mqtttopic "sunnyisland/1260000000"
```

## Flux Data Query examples

### Get Sunny Boy PV AC output

```
from(bucket:"pv_data")
|>range(start:-1h)
|>filter(fn: (r) => r._measurement == "pv_ac_measurements" and r._field == "grid_total_watts" and r.inv_id == "sunnyboy1" )
```
