###**Usage**
Execute **example.py** and you will have .csv and .json roster file in your directory.
```
$ python3 example.py
```

.csv file can be used to import into your google calender from browser
.jon file can be used for google calender API

Any comment is welsome and hope you enjoy it!


### Run in debug mode
```sh
cd src; FLASK_APP=server.py FLASK_DEBUG=1 python -m flask run
```


### Run in server mode
```sh
cd src; FLASK_APP=server.py python -m flask run
```