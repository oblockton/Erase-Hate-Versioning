# Reclass feauture operation
application.py

* User makes a query. If the search result returns any items marked as hate. The user can select the up to 5 items to reclassify. The 5 items are the first five in the array of hate results. To determine which texts are the ones labeled hate, the prediction array of both models was added to the result/return of the prediction function.

 > * Determine if that item was classed as hateful. Then limit reclass items to five items.
  ~~~~
  to_reclass =[(tweets_dict['text'][i],results['prediction_array'][i],f'ITEM {str(i)}') for i in range(len(tweets_dict['text'])) if (int(results['prediction_array'][i]) == 0)]
  if len(to_reclass)> 5:
      to_reclass = to_reclass[:5]
  ~~~~
