import os
from flask import Flask, render_template,request,jsonify,redirect,url_for
import tweepy
from model import logregress_linsvc
import requests
import json
import datetime
import time


# import sqlite3
# from sqlite3 import Error



app= Flask(__name__)

###############################
#Configure Tweepy'''
#############################
consumer_key = os.environ.get('CONSUMER_KEY')
consumer_secret = os.environ.get('CONSUMER_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get('ACCESS_SECRET')



global api
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)


########################################################################

#Setup tweepy api call functions
############### CHANGE ITEM COUNT IN FINAL VERSION

#######################################################################
#Query for pulling tweets containing a keyword'''
def api_topic(api,topic):
    tweet_dict = {'dates':[],'text':[]}
    for tweet in tweepy.Cursor(api.search,q=topic, tweet_mode='extended',lang="en").items(10):
        tweet_dict['dates'].append((tweet.created_at).strftime('%m-%d-%Y'))
        tweet_dict['text'].append(tweet.full_text)

    return tweet_dict
#######################################################################
#Query for pulling tweets only from a single useer timelime specified as the input, when form choice is 'user' '''
def api_user(api,user):
    user_posts = {'dates':[],'text':[]}
    for post in tweepy.Cursor(api.user_timeline, screen_name=user, tweet_mode='extended',lang="en").items(10):
        user_posts['dates'].append((post.created_at).strftime('%m-%d-%Y'))
        user_posts['text'].append(post.full_text)
    return user_posts

##########################################################################
#Transform user input into a array for use in prediction function '''
def text_transform(textinput):
    #sentence_array = textinput.split('.')
    dict_to_df = {'text':[textinput]}
    return dict_to_df


# define model_server url
modelserv_url = os.environ.get('MODELSERV_URL')

#####################################
# Create routes
#####################################


###### Handles 404 errors. Filters for Get requests on the post route.
###### 405:method not allowed returns browser default method not allowed page.
@app.errorhandler(404)
def route_error(error):
    print(request.path)
    if request.path[:8] == '/predict':
        return ('404 GET method attempted, POST method only')
    else:
        return ("Page Not Found")

@app.errorhandler(503)
def heroku_error(error):
    print(request.path)
    return render_template('support.html', error = 'Model Serving Error')



@app.route('/')
def index():
    '''Return the homepage'''
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    '''Return about us'''
    return render_template('aboutus.html')

@app.route('/models')
def models():
    '''Return tech_section on models'''
    return render_template('models.html')

@app.route('/contact')
def contact():
    '''Return contact page'''
    return render_template('contact.html')
@app.route('/support')
def support():
    return render_template('support.html', error = 'If an error exists, it will appear here. Errors: None')

@app.route('/terms_privacy')
def terms_privacy():
    return render_template('terms_privacy.html')

###################################################################################
''' /predict route takes a form submission.
 makes predictions based on form imputs for query input, query type,model type.'''
##################################################################################

####################################################################################################################################
'''If the twitter server responds with any error besides the 404 error returned from a query with no results, lock the user outer
 of selecting any Twitter prediction method. On first load declare and unlocked state'''
#########################################################################################################

# Set inital lock state on first load
locks = {"time": datetime.datetime.now(), "state": 'unlocked'}

@app.route('/predict',methods = ['POST'])
def predict():

    if request.method == 'POST':
        form_input = request.form.to_dict()
        print(form_input)
        query = form_input['query_input']
        query_type =form_input['query_type']
        model_type = form_input['model_type']

        # Check if Twitter method selected in form input. If so apply locking scheme
        if (query_type == 'topic') or (query_type=='user'):
            print('new request')
            print(locks)

            # check lock time. if 15min since "locked" state set. Reset lock
            if (locks['state'] == 'locked') and ((datetime.datetime.now() - locks['time'])> datetime.timedelta(seconds=60)):
                print('im unlocking!!!!')
                locks['state'] = 'unlocked'
                # Continue with users request
                if query_type == 'topic':
                    ############################################ topic query
                    if model_type == 'LogRegress-Linsvc':
                        try:
                            topic_tweets_dict = api_topic(api,query)
                            # print('sample text from query: ')
                            # print(topic_tweets_dict['text'][0])
                            results= logregress_linsvc(topic_tweets_dict)
                            return render_template('results_tweets.html',
                            query_type=query_type,query_input=query,
                            count_items=results['total_count'],model_type=model_type,
                            hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                            hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                            neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in wteepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'{query_type}: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                print('!!!!This tweepy error occured: '+ str(e))
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked: Duration 15min")

                    elif model_type == 'LSTM':
                        try :
                            topic_tweets_dict = api_topic(api,query)
                            try:
                                resp_return= requests.post(url=modelserv_url, json=topic_tweets_dict )
                                results =resp_return.json()
                                print(results)
                                return render_template('results_tweets.html',
                                query_type=query_type,query_input=query,
                                count_items=results['total_count'],model_type=model_type,
                                hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                                hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                                neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                            except Exception as e:
                                print("!!!!Model Server Error: " + str(e))
                                return render_template('support.html', error = 'Model Serving Error')
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in wteepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'{query_type}: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                print('!!!!This tweepy error occured: '+ str(e))
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked: Duration 15min")



                ################### Query for user posts from single user's timeline
                elif query_type == 'user':
                    if model_type == 'LogRegress-Linsvc':
                        try:
                            user_tweets_dict = api_user(api,query)
                            results= logregress_linsvc(user_tweets_dict)
                            return render_template('results_tweets.html',
                            query_type=query_type,query_input=query,
                            count_items=results['total_count'],model_type=model_type,
                            hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                            hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                            neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in teepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'User: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")

                    elif model_type == 'LSTM':
                        try:
                            user_tweets_dict = api_user(api,query)
                            try:
                                resp_return= requests.post(url=modelserv_url, json=user_tweets_dict )
                                results =resp_return.json()
                                print(results)
                                return render_template('results_tweets.html',
                                query_type=query_type,query_input=query,
                                count_items=results['total_count'],model_type=model_type,
                                hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                                hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                                neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                            except Exception as e:
                                print("!!!!Model Server Error: " + str(e))
                                return render_template('support.html', error = 'Model Serving Error')
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in teepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'User: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")

                                # END LOCK --> UNLOCKED --> CONTINUE RUNNING
                                ####################################################################################################################

            #if lock state is 'unlocked' proceed with user request.
            elif locks['state'] is 'unlocked':

                ####################################################################
                '''Structure query and modeling process based on form inpuforts
                 Render results page based on form inputs
                Args for render template (html_reference)=(python_data_from_model)'''
                ####################################################################
                if query_type == 'topic':
                    ############################################ topic query
                    if model_type == 'LogRegress-Linsvc':
                        try:
                            topic_tweets_dict = api_topic(api,query)
                            # print('sample text from query: ')
                            # print(topic_tweets_dict['text'][0])
                            results= logregress_linsvc(topic_tweets_dict)
                            return render_template('results_tweets.html',
                            query_type=query_type,query_input=query,
                            count_items=results['total_count'],model_type=model_type,
                            hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                            hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                            neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404, tweepy error is not error in teepy,but error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'{query_type}: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")

                    elif model_type == 'LSTM':
                        try :
                            topic_tweets_dict = api_topic(api,query)
                            try:
                                resp_return= requests.post(url=modelserv_url, json=topic_tweets_dict )
                                results =resp_return.json()
                                print(results)
                                return render_template('results_tweets.html',
                                query_type=query_type,query_input=query,
                                count_items=results['total_count'],model_type=model_type,
                                hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                                hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                                neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                            except Exception as e:
                                print("!!!!Model Server Error: " + str(e))
                                return render_template('support.html', error = 'Model Serving Error')
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404, tweepy error is not error in teepy,but error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'{query_type}: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")



                ################### Query for user posts from single user's timeline
                elif query_type == 'user':
                    if model_type == 'LogRegress-Linsvc':
                        try:
                            user_tweets_dict = api_user(api,query)
                            results= logregress_linsvc(user_tweets_dict)
                            return render_template('results_tweets.html',
                            query_type=query_type,query_input=query,
                            count_items=results['total_count'],model_type=model_type,
                            hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                            hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                            neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in teepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'User: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")


                    elif model_type == 'LSTM':
                        try:
                            user_tweets_dict = api_user(api,query)
                            try:
                                resp_return= requests.post(url=modelserv_url, json=user_tweets_dict )
                                results =resp_return.json()
                                print(results)
                                return render_template('results_tweets.html',
                                query_type=query_type,query_input=query,
                                count_items=results['total_count'],model_type=model_type,
                                hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                                hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                                neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                            except Exception as e:
                                print("!!!!Model Server Error: " + str(e))
                                return render_template('support.html', error = 'Model Serving Error')
                        except tweepy.TweepError as e:
                            print(e)
                            if str(e)[-3:]== '404':
                                # Search inputs that dont return a user will throw a TWITTER 404,
                                # tweepy error is not error in teepy,but an error in twitter
                                # Tweepy will pass along twitters error message
                                print('!!!!This twitter error occured: '+ str(e))
                                print(f'User: {query} -does not exist')
                                return render_template('support.html', error = f"Twitter Error - Type: {query_type} - Input: {query}")
                            else:
                                print('!!!!This tweepy error occured: '+ str(e))
                                locks['state'] = 'locked'
                                locks['time']=datetime.datetime.now()
                                print(' Error:locking now')
                                print(locks)
                                return render_template("support.html", error ="Twitter Server Error - Twitter search locked:15min")
                                #End state 'UNLOCKED' process, init main process if no errors thrown
                                ##############################################################################################################

            # If state is locked, return/render the lockout page
            elif locks['state'] is 'locked':
                print('im still locked :/')
                ## if twitter server error occured not to due to input error, possibly ratelimit,
                ## lock the ability to Twitt search. If user tries twit searched while locked, keep user at index.html
                # Only text option allows prediction when state = 'LOCKED'
                return render_template('index.html')

                # End locking function.
                ##################################################3

        ################################################### text input query
        elif query_type == "text":
            # Hide user input and reduce text lenght when displayed in results.
            # If text < 500 characters, show half of text inputs.
            # if text input  > 500 characters, truncate it and show max 500 characters.
            char_count = len(query)
            if char_count > 500:
                text_snip = query[:500]
            else:
                text_snip = query[:int(len(query)/2)]

            ####################################
            if model_type == 'LogRegress-Linsvc':
                textinput_dict = text_transform(query)
                results = logregress_linsvc(textinput_dict)
                return render_template('results_text.html',
                query_type=query_type,text_snip=text_snip,
                count_items=results['total_count'],model_type=model_type,
                hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])

            elif model_type == 'LSTM':
                textinput_dict = text_transform(query)
                try:
                    resp_return= requests.post(url=modelserv_url, json=textinput_dict )
                    results =resp_return.json()
                    print(results)
                    return render_template('results_text.html',
                    query_type=query_type,text_snip=text_snip,
                    count_items=results['total_count'],model_type=model_type,
                    hate_count=results['hate_data']['count'],hate_percent=results['hate_data']['percentTotal'],
                    hurt_count=results['hurt_data']['count'],hurt_percent=results['hurt_data']['percentTotal'],
                    neither_count=results['neither_data']['count'],neither_percent=results['neither_data']['percentTotal'])
                except Exception as e:
                    print("!!!!!Model Server Error: " + str(e))
                    return render_template('support.html', error = 'Model Serving Error')













if __name__ == "__main__":
    app.run()
