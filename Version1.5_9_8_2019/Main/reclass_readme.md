# Reclass feauture operation
### Affected - application.py, results_text.html,results_tweets.html

* User makes a query. If the search result returns any items marked as hate. The user can select the up to 5 items to reclassify. The 5 items are the first five in the array of hate results. To determine which texts are the ones labeled hate, the prediction array of both models was added to the result/return of the prediction function.

 * Determine if that item was classed as hateful. Then limit reclass items to five items.
  * **LogRegress**
  ~~~~
  to_reclass =[(tweets_dict['text'][i],results['prediction_array'][i],f'ITEM {str(i)}') for i in range(len(tweets_dict['text'])) if (int(results['prediction_array'][i]) == 0)]
  if len(to_reclass)> 5:
      to_reclass = to_reclass[:5]
  ~~~~

  * **LSTM**
   > Here prediction_array is a list of probabilities. Use the indices of the max probability value by using np.argmax
  ~~~~
  to_reclass =[(tweets_dict['text'][i],np.argmax(results['prediction_array'][i]),f'ITEM {str(i)}') for i in range(len(tweets_dict['text'])) if int(np.argmax(results['prediction_array'][i]) == 0)]
  if len(to_reclass)> 5:
      to_reclass = to_reclass[:5]
  ~~~~

* variable `to_reclass` is now a list of only hate classed tweets. The list contains `[text,class(0,1,or2),Item Label]`.
* A form control/form selection is added for each hateful tweets. Each select option has 3 options/classes to choose from.
* Item label is the name of the select tag that acts as form control. Each select must have a unique name.

> Application.py render_template passes data to html using params.
~~~~
return render_template('results_tweets.html',
                  reclass_data = to_reclass,
~~~~
> HTML
~~~~
{% for item in reclass_data %}
  <div class="row">
    <p class='text-white'>{{ item[0] }}</p>
    <select class="form-control" name="{{ item[2] }}">
      <option value="0 delimiter {{ item[0] }}">No Change</option>
      <option value="1 delimiter {{ item[0] }}">Hurtful</option>
      <option value="2 delimiter {{ item[0] }}">Harmless</option>
    </select>
  </div>
  <hr style="color:lavender;width:100%;">
{% endfor %}
~~~~

* Note - the class and text is passed as one string, in the value for the form selet tags. `delimiter` has been added to allow repeatable parsing later.
~~~~
<option value="2 delimiter {{ item[0] }}">Harmless</option>
~~~~
