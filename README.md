

## Running the Sunny Boy Data Collection Script

Below is an example using the -t flag. Passing the -t flag will result in the script using
some dummy test data rather than using real sunny boy data.

```
$ python save-sunny-boy-power-data.py --sunnyboyhost sma3013980643 --invid sunnyboy1 --redishost localhost --redispassword nimda1234 --influxdbhost http://localhost:8086 --influxdbtoken 3Nj5jtGSROxcuJg_r-4CJKVIqql_5NLSYjPEuMCzNKpdTqKAna57JdkW0c_UldrEvRepVvWKM0J_Mx567972vQ== --influxdborg pv_data --influxdbbucket pv_data --lat 36.17 --lon -82.86 -t
```


## Flux Data Query examples

### Get Sunny Boy PV AC output

```
from(bucket:"pv_data")
|>range(start:-1h)
|>filter(fn: (r) => r._measurement == "pv_ac_measurements" and r._field == "grid_total_watts" and r.inv_id == "sunnyboy1" )
```