# Changes to `application.py`

## Addition of dedicated API reclassification route. /api_reclass_submit, methods = ['POST']

  * A separate route has been added to ingest reclassified item. For the most part the route is the same as the route which serves the webpage, however the data parse, outputs and internal print statement have been adjusted to demark API usage, and better serve Erase Hate Python Library users. Return statements now return a response as opposed to render_template(as would happen for the web page.)

  * This new route accepts a list of lists as such.:
  `[['class label', 'text/tweet'], ['classlabel', 'text2/tweet2'], ['classlabel', 'text3/tweet3']]`
      - **Any reclassification form parsing must be completed by the user, using custom code or the Erase Hate Python Library prior to posting to this route.**

   - With the input being different from the route that serves the webpage, a new sql input helper function has been created. `enter_items_api`

  * API codes have been added as such:
   - 200 = Successful
   - 500 = Failed. Code error or uncaught SQL exceptions
   - 403 = ACCESS DENIED -SQL Err - authentication
   - 404 = BAD_DB_ERROR - SQL selected database nonexistent


  > Error handling with api_code in return statement
  ~~~~
  try:
      cnx = mysql.connector.connect(**config)
      c = cnx.cursor()
      enter_items_api(reclass_input,c,cnx)
      cnx.close()
      print( '**** Reclass submit successful -API SUBMIT REQUEST ****' )
      return jsonify({'api_code':200, 'message':'successful' })
  except mysql.connector.Error as err:
      if (err.errno == errorcode.ER_ACCESS_DENIED_ERROR):
           print("!!!! Something is wrong with your user name or password- API SUBMIT REQUEST !!!!")
           print(err)
           cnx.close()
           return jsonify({ 'api_code':403, 'message':'ACCESS DENIED: {}'.format(err) })
      elif (err.errno == errorcode.ER_BAD_DB_ERROR):
          print("!!! Database does not exist - API SUBMIT REQUEST !!!")
          cnx.close()
          return jsonify({ 'api_code':404, 'message':'BAD_DB_ERROR: {}'.format(err) })
      else:
          print('Some other SQL error occured - API SUBMIT REQUEST')
          print(err)
          cnx.close()
          return jsonify({ 'api_code':500, 'message':'DB insert Unsuccessful: {}'.format(err) })

  except Exception as e :
      print('!!!! Error in Reclass Submisson - Not a SQL error - API SUBMIT REQUEST !!!!')
      print('Error: {}'.format(e))
      cnx.close()
      return jsonify({'api_code':500, 'message':'DB insert Unsuccessful: {}'.format(err)})
  ~~~~

## TweepyMashup Updated to 1.0.7

  * No code changes made to `application.py`. However , note the update.


---
