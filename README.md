# Erase-Hate-Versioning
Erase Hate repo for versions. Contains complete architecture.

* Will not include LSTM.h5 files-too large.

## Structure & Folder Heirarchy

- Version_M_DD_YYYY
  - Main <--folder
      - contains all files for front end, twiiter handling, & LogRegress Model predictions
      - app.py for for front end is in Main.
  - ModelServer <---folder
      - contains the files necessary for serving ONLY the LSTM model.
      - model serving application.py resides in ModelServer.
           -application.py filename required for AWS ---> route will then require @application.route,
           * Also requires.
           application = Flask('__name__')
           if __name__ == '__main__':
            application.run()

            * file will run locally with the change to' application' decorator instead of 'app'.

# Running 2 servers/Flask apps locally.

  For each flask file ( application.py & app.py) declare the port it will run on. Can not be same port.

  ## Example:

  * Front-End: Folder -> Main: File --> App.py:  app.run(port=5000)

  * Model Server: Folder -> ModelServer: File --> Application.py: app.run(port=5001)

# Important notes for running locallly.

  ## Config Vars & Security

Folder -> Main: File --> App.py
   * For twitter API
    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')
    access_token = os.environ.get('ACCESS_TOKEN')
    access_token_secret = os.environ.get('ACCESS_SECRET')
        * Replace --> os.environ.get('CONSUMER_KEY') with your key ---> consumer_key = 'cdjsiojfe94334ivdso'


    * modelserv_url variable
        Replace --> os.environ.get('MODELSERV_URL') with your url.
             -- If you are running locally this will be "http://127.0.0.1:chosenport/receiver"
                -- Ex: modelserv_url = 'http://127.0.0.1:5000/receiver'
                * dont use 'https' if runing the model server locally.
