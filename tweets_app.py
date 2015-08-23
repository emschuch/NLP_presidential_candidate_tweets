from spyre import server

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import tweepy
import cnfg
import datetime
from datetime import date
from pytz import reference
from pattern.en import parse, tag, sentiment, modality, Sentence

plt.style.use('fivethirtyeight')
pd.set_option('display.max_colwidth', -1) #displays full tweet text

config = cnfg.load(".twitter_config")

auth = tweepy.OAuthHandler(config["consumer_key"],
                           config["consumer_secret"])
auth.set_access_token(config["access_token"],
                      config["access_token_secret"])

api = tweepy.API(auth)

candidates = [{'name': 'Jeb Bush', 'party': 'R', 'user': 'JebBush'},
              {'name': 'Hillary Clinton', 'party': 'D', 'user': 'HillaryClinton'},
              {'name': 'Ted Cruz', 'party': 'R', 'user': 'tedcruz'},
              {'name': 'Marco Rubio', 'party': 'R', 'user': 'marcorubio'},
              {'name': 'Scott Walker', 'party': 'R', 'user': 'ScottWalker'},
              {'name': 'Bernie Sanders', 'party': 'D', 'user': 'BernieSanders'},
              {'name': 'Rick Perry', 'party': 'R', 'user': 'TeamRickPerry'},
              {'name': 'Chris Christie', 'party': 'R', 'user': 'ChrisChristie'},
              {'name': 'Rand Paul', 'party': 'R', 'user': 'RandPaul'},
              {'name': 'John Kasich', 'party': 'R', 'user': 'JohnKasich'},
              {'name': 'Ben Carson', 'party': 'R', 'user': 'RealBenCarson'},
              {'name': 'Bobby Jindal', 'party': 'R', 'user': 'BobbyJindal'},
              {'name': 'Lindsey Graham', 'party': 'R', 'user': 'LindseyGrahamSC'},
              {'name': 'Mike Huckabee', 'party': 'R', 'user': 'GovMikeHuckabee'},
              {'name': 'Carly Fiorina', 'party': 'R', 'user': 'CarlyFiorina'},
              {'name': "Martin O'Malley", 'party': 'D', 'user': 'MartinOMalley'},
              {'name': 'Donald Trump', 'party': 'R', 'user': 'realDonaldTrump'},
              {'name': 'George Pataki', 'party': 'R', 'user': 'GovernorPataki'},
              {'name': 'Rick Santorum', 'party': 'R', 'user': 'RickSantorum'},
              {'name': 'Lincoln Chafee', 'party': 'D', 'user': 'LincolnChafee'},
              {'name': 'Jim Webb', 'party': 'D', 'user': 'JimWebbUSA'},
              {'name': 'Jill Stein', 'party': 'G', 'user': 'DrJillStein'}
             ]

class TweetApp(server.App):

    def __init__(self):
        # caches the data to avoid multiple calls to the twitter API
        self.data_cache = None
        self.today = date.strftime(datetime.datetime.now(), format='%m/%d/%Y, %H:%M')


    title = 'Tweets of Presidential Candidates'

    inputs =[{ "type":'radiobuttons',
                "options": [{"label": "Average Favorites", "value": "Favorites"},
                            {"label": "Average Retweets", "value": "Retweets"},
                            {"label": "Average Polarity", "value": "Polarity"},
                            {"label": "Average Subjectivity", "value": "Subjectivity"},
                            {"label": "Average Certainty", "value": "Certainty"}
                            ],
                "value": 'Favorites',
                "key": 'barchart', 
                "action_id": 'update_data'}]

    controls = [{ 'type': "hidden", 
                    'id': 'update_data'}]

    tabs = ['Chart', 'Table']

    outputs = [{ "type" : "plot",
                    "id" : "plot_id",
                    'control_id': 'update_data',
                    'tab': 'Chart'},
                { 'type': 'table',
                    'id': 'table_id',
                    'control_id': 'update_data',
                    'tab': 'Table', 
                    'sortable': True}]


    def getData(self, params):
        if self.data_cache is None:
            tweets = []
            for cand in candidates:
                tweets.append({'tweets': api.user_timeline(cand['user'], count=20), 
                                'name': cand['name'], 
                                'party': cand['party']})
            all_tweets = []
            for tweet_data in tweets:
                name = tweet_data['name']
                party = tweet_data['party']
                for tweet in tweet_data['tweets']:
                    all_tweets.append( {'Name': name,
                                        'Tweet': tweet.text, 
                                        'Favorites': tweet.favorite_count, 
                                        'Retweets': tweet.retweet_count} )
            dfs = pd.DataFrame(all_tweets)
            sentiments = [sentiment(tweet) for tweet in dfs['Tweet']]
            dfs['Polarity'] = [sent[0] for sent in sentiments]
            dfs['Subjectivity'] = [sent[1] for sent in sentiments]
            modal = [modality(Sentence(parse(tweet, lemmata=True))) for tweet in dfs['Tweet']]
            dfs['Certainty'] = modal
            self.data_cache = dfs
        return self.data_cache


    def getPlot(self, params):
        df = self.getData(params)
        col = params['barchart']
        df = pd.DataFrame(df.groupby(['Name'])[col].mean())
        df = df.sort(columns=col)
        localtime = reference.LocalTimezone()
        tz = localtime.tzname(datetime.datetime.now())
        plt_obj = df.plot(kind='barh', legend=False)
        plt_obj.set_ylabel('')
        plt_obj.set_xlabel('Average ' + col)
        plt_obj.set_title('20 Most Recent Tweets (' + self.today + ' ' + tz + ')')
        # set xlims for specific columns
        if col == 'Polarity' or col == 'Certainty':
            x1, x2, y1, y2 = plt_obj.axis()
            plt_obj.axis((x1, 1.0, y1, y2))
        elif col == 'Subjectivity':
            plt_obj.set_xlim([0, 1.0])
        fig = plt_obj.get_figure()
        return fig


if __name__ == '__main__':
    app = TweetApp()
    app.launch(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
