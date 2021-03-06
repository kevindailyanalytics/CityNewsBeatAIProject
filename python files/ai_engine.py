import pandas as pd
import psycopg2
import numpy as np
from sqlalchemy import create_engine
import random
import warnings
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn import metrics


def aimodel(uid, settings, featureSettings, data):
    # dependencies: psycopg2, scikitlearn, pandas, numpy, sqlalchemy, xgboost

    # function to be used on columns to strip whitespace
    def rstrip(string):
        if string is None:
            return(None)
        else:
            return(string.rstrip())

    # function used to change day format to integer number of days
    # based on data format returned from sql query
    def stripdays(string):
        string = str(string)
        index = string.find('day')
        if index == -1:
            index2 = string.find(':')
            return(int(string[:index2])/24)
        else:
            return(int(string[:index]))

    # used for multilogistic regression
    def partitionClasses(index):
        amt_time_watched = user_time_watched_ratio.loc[index]['amount_of_time_watched']
        vid_length = user_time_watched_ratio.loc[index]['length']
        ratio = amt_time_watched/vid_length
        if (ratio < .25):
            return 0
        elif (ratio < .5):
            return 1
        elif (ratio < .75):
            return 2
        else:
            return 3

    # return list of probabilities that this user will want to watch that corresponding video
    def runLogisticRegression(ttuserint, vidfeatures, settings=settings):
        # ttuserint = ttuserint.drop('if_watched_multi',axis=1)
        y = ttuserint['if_watched']
        features = list(set(ttuserint.columns) - set(['if_watched']))
        X = ttuserint[features]

        if settings['nUserF1Scores'] is True:
            return(checkAccuracy(X, y, settings['numKFolds'], 'logreg'))
        else:
            if settings['checkF1Scores'] is True:
                checkAccuracy(X, y, settings['numKFolds'], 'logreg')

            model = LogisticRegression(solver='liblinear').fit(X, y)
            vids = np.array(vidfeatures['vid'])
            if settings['showVidTitles'] is True:
                titles = np.array(vidfeatures['title'])
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids, titles), reverse=True))
            else:
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids), reverse=True))

    def runKNN(ttuserint, vidfeatures, settings=settings):

        # ttuserint = ttuserint.drop('if_watched_multi',axis=1)
        y = ttuserint['if_watched']
        features = list(set(ttuserint.columns) - set(['if_watched']))
        X = ttuserint[features]

        if settings['nUserF1Scores'] is True:
            return(checkAccuracy(X, y, settings['numKFolds'], 'knn'))
        else:
            if settings['checkF1Scores'] is True:
                checkAccuracy(X, y, settings['numKFolds'], 'knn')

            model = KNeighborsClassifier(
                n_neighbors=3, weights='uniform', metric='minkowski').fit(X, y)
            vids = np.array(vidfeatures['vid'])
            if settings['showVidTitles'] is True:
                titles = np.array(vidfeatures['title'])
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids, titles), reverse=True))
            else:
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids), reverse=True))

    # likely not the algorithm to use due to binary nature of initial question
    def runMultiLogisticRegression(ttuserint, vidfeatures, settings=settings):

        ttuserint = ttuserint.drop('if_watched', axis=1)
        y = ttuserint['if_watched_multi']
        features = list(set(ttuserint.columns) - set(['if_watched_multi']))
        X = ttuserint[features]

        if settings['nUserF1Scores'] is True:
            return(checkAccuracy(X, y, settings['numKFolds'], 'multilogreg'))
        else:
            if settings['checkF1Scores'] is True:
                checkAccuracy(X, y, settings['numKFolds'], 'multilogreg')

            model = LogisticRegression(
                solver='liblinear', multi_class='auto').fit(X, y)
            vids = np.array(vidfeatures['vid'])
            if settings['showVidTitles'] is True:
                titles = np.array(vidfeatures['title'])
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids, titles), reverse=True))
            else:
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids), reverse=True))

    def runMLP(ttuserint, vidfeatures, settings=settings):

        y = ttuserint['if_watched']
        features = list(set(ttuserint.columns) - set(['if_watched']))
        X = ttuserint[features]

        if settings['nUserF1Scores'] is True:
            return(checkAccuracy(X, y, settings['numKFolds'], 'mlp'))
        else:
            if settings['checkF1Scores'] is True:
                checkAccuracy(X, y, settings['numKFolds'], 'mlp')

            model = MLPClassifier(
                solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1).fit(X, y)
            vids = np.array(vidfeatures['vid'])
            if settings['showVidTitles'] is True:
                titles = np.array(vidfeatures['title'])
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids, titles), reverse=True))
            else:
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1))[:, 1]
                return(sorted(zip(vids_prob, vids), reverse=True))

    def runXGBoost(ttuserint, vidfeatures, settings=settings):

        # ttuserint = ttuserint.drop('if_watched_multi',axis=1)
        y = ttuserint['if_watched']
        features = list(set(ttuserint.columns) - set(['if_watched']))
        X = ttuserint[features]
        data

        if settings['nUserF1Scores'] is True:
            return(checkAccuracy(X, y, settings['numKFolds'], 'mlp'))
        else:
            ca = 0
            if settings['checkF1Scores'] is True:
                checkAccuracy(X, y, settings['numKFolds'], 'xgboost')

            model = xgb.XGBClassifier(
                learning_rate=0.1,
                n_estimators=1000,
                max_depth=5,
                min_child_weight=1,
                gamma=0,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary:logistic',
                nthread=4,
                scale_pos_weight=1)

            model.fit(X.values, y.values, eval_metric='error')
            vids = np.array(vidfeatures['vid'])
            if settings['showVidTitles'] is True:
                titles = np.array(vidfeatures['title'])
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1).values)[:, 1]
                return(sorted(zip(vids_prob, vids, titles), reverse=True))
            else:
                vids_prob = model.predict_proba(
                    vidfeatures.drop(['vid', 'title'], axis=1).values)[:, 1]
                return(sorted(zip(vids_prob, vids), reverse=True))

    # returns the F1 score and results from confusion matrix.
    # The F1 score is define as follows: F1 = 2 * (precision * recall) / (precision + recall)
    def checkAccuracy(X, y, numsplits, modelSelection, settings=settings):

        # global userDefinedFeatures

        kf = KFold(n_splits=numsplits)
        f1_scores = []
        conf_matrices = []
        sample_size = 0
        final_conf_matrix = [[0, 0], [0, 0]]
        for train_index, test_index in kf.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            if modelSelection == 'logreg':
                model = LogisticRegression(
                    solver='liblinear').fit(X_train, y_train)
                y_pred = model.predict(X_test)
                f1_scores.append(metrics.f1_score(
                    y_test, y_pred, average='weighted'))
                conf_matrices.append(metrics.confusion_matrix(y_test, y_pred))
            elif modelSelection == 'knn':
                model = KNeighborsClassifier(
                    n_neighbors=3, weights='uniform', metric='minkowski').fit(X, y)
                y_pred = model.predict(X_test)
                f1_scores.append(metrics.f1_score(
                    y_test, y_pred, average='weighted'))
                conf_matrices.append(metrics.confusion_matrix(y_test, y_pred))
            elif modelSelection == 'multilogreg':
                model = LogisticRegression(
                    solver='liblinear', multi_class='auto').fit(X_train, y_train)
                y_pred = model.predict(X_test)
                f1_scores.append(metrics.f1_score(
                    y_test, y_pred, average='weighted'))
                conf_matrices.append(metrics.confusion_matrix(y_test, y_pred))
            elif modelSelection == 'mlp':
                model = LogisticRegression(
                    solver='liblinear', multi_class='auto').fit(X_train, y_train)
                y_pred = model.predict(X_test)
                f1_scores.append(metrics.f1_score(
                    y_test, y_pred, average='weighted'))
                conf_matrices.append(metrics.confusion_matrix(y_test, y_pred))
        if modelSelection == 'xgboost':

            model = xgb.XGBClassifier(
                learning_rate=0.1,
                n_estimators=1000,
                max_depth=5,
                min_child_weight=1,
                gamma=0,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary:logistic',
                nthread=4,
                scale_pos_weight=1)

            xgtrain = xgb.DMatrix(X.values, label=y.values)
            model.fit(X.values, y.values, eval_metric='error')
            cvresult = xgb.cv(model.get_xgb_params(), xgtrain, num_boost_round=model.get_params()[
                              'n_estimators'], nfold=numsplits, metrics='logloss', early_stopping_rounds=50)
            vid_predictions = model.predict(X.values)
            vid_predprob = model.predict_proba(X.values)[:, 1]
            if settings['nUserF1Scores'] is True:
                f1score = metrics.f1_score(
                    y.values, vid_predictions, average='weighted')
                final_conf_matrix = metrics.confusion_matrix(
                    y.values, vid_predictions)
                sample_size = sum([sum(i) for i in final_conf_matrix])
                tp = final_conf_matrix[0][0]/sample_size
                fp = final_conf_matrix[0][1]/sample_size
                tn = final_conf_matrix[1][1]/sample_size
                fn = final_conf_matrix[1][0]/sample_size
                return (f1score, tp, fp, tn, fn)
            else:
                final_conf_matrix = metrics.confusion_matrix(
                    y.values, vid_predictions)
                sample_size = sum([sum(i) for i in final_conf_matrix])
                # print(
                #     '_______________________________________________________________________________')
                # print('Model: {model}'.format(model=settings['modelType']))
                # print(
                #     'The F1 score is a value between 0 and 1. The closer to 1, the better the score.')
                # print(
                #     'The F1 score represents a balanced view between model precision and recall.')
                # print('F1 score: '+str(round(metrics.f1_score(y.values,
                #                                               vid_predictions, average='weighted'), 4)))
                # print()
                # print(
                #     'Normalized confusion matrix results below. Values are between 0 and 1.\n')
                # print('True Positive: '+str(round(
                #     final_conf_matrix[0][0]/sample_size, 2))+' (model is correct when it says you like video)')
                # print('False Positive (model error): '+str(round(
                #     final_conf_matrix[0][1]/sample_size, 2))+' (model says you like a video when you don\'t)')
                # print('True Negative: '+str(round(
                #     final_conf_matrix[1][1]/sample_size, 2))+' (model is correct when it says you don\'t like video)')
                # print('False Negative (model error): '+str(round(
                #     final_conf_matrix[1][0]/sample_size, 2))+' (model says you don\'t like video when you do)')
                # print(
                #     '_______________________________________________________________________________')
                f1score = round(metrics.f1_score(
                    y.values, vid_predictions, average='weighted'), 4)
                tp = round(final_conf_matrix[0][0]/sample_size, 2)
                fp = round(final_conf_matrix[0][1]/sample_size, 2)
                tn = round(final_conf_matrix[1][1]/sample_size, 2)
                fn = round(final_conf_matrix[1][0]/sample_size, 2)
                return({'f1score': f1score, 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn})

        else:
            avg_f1_scores = sum(f1_scores)/len(f1_scores)
            for m in conf_matrices:
                if len(m) == 1:
                    sample_size = sample_size + m[0][0]
                    final_conf_matrix[0][0] += m[0][0]
                else:
                    sample_size = sample_size + \
                        m[0][0] + m[0][1] + m[1][0] + m[1][1]
                    final_conf_matrix[0][0] += m[0][0]
                    final_conf_matrix[0][1] += m[0][1]
                    final_conf_matrix[1][0] += m[1][0]
                    final_conf_matrix[1][1] += m[1][1]
            if settings['nUserF1Scores'] is True:
                return(avg_f1_scores, final_conf_matrix[0][0]/sample_size, final_conf_matrix[0][1]/sample_size, final_conf_matrix[1][1]/sample_size, final_conf_matrix[1][0]/sample_size)
            else:
                # print(
                #     '_______________________________________________________________________________')
                # print('Model: {model}'.format(model=settings['modelType']))
                # print(
                #     'The F1 score is a value between 0 and 1. The closer to 1, the better the score.')
                # print(
                #     'The F1 score represents a balanced view between model precision and recall.')
                # print('Average F1 score: '+str(round(avg_f1_scores, 4)))
                # print()
                # print(
                #     'Normalized confusion matrix results below. Values are between 0 and 1.\n')
                # print('True Positive: '+str(round(
                #     final_conf_matrix[0][0]/sample_size, 2))+' (model is correct when it says you like video)')
                # print('False Positive (model error): '+str(round(
                #     final_conf_matrix[0][1]/sample_size, 2))+' (model says you like a video when you don\'t)')
                # print('True Negative: '+str(round(
                #     final_conf_matrix[1][1]/sample_size, 2))+' (model is correct when it says you don\'t like video)')
                # print('False Negative (model error): '+str(round(
                #     final_conf_matrix[1][0]/sample_size, 2))+' (model says you don\'t like video when you do)')
                # print(
                #     '_______________________________________________________________________________')
                f1score = round(avg_f1_scores, 4)
                tp = round(final_conf_matrix[0][0]/sample_size, 2)
                fp = round(final_conf_matrix[0][1]/sample_size, 2)
                tn = round(final_conf_matrix[1][1]/sample_size, 2)
                fn = round(final_conf_matrix[1][0]/sample_size, 2)
                return({'f1score': f1score, 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn})

    if settings['nUserF1Scores'] is True:
        userIDs = pd.DataFrame(data[0], columns=['uid'])
        n_Users = int(userIDs.shape[0]*settings['nUserFraction'])

        if n_Users == 0:
            n_Users = 1

        randNums = np.random.choice(userIDs.shape[0], n_Users, replace=False)
        userIDStrings = list(userIDs['uid'])
        userIDStrings = [uid for ind, uid in enumerate(
            userIDStrings) if ind in randNums]
        f1score, tp, fp, tn, fn = 0, 0, 0, 0, 0

        for user in userIDStrings:

            # integer value of number of users. used in later calculations
            num_users = len(userIDs)

            # table of the video ids that the specified user has watched/skipped
            user_time_watched_ratio = pd.DataFrame.from_dict(data[6])

            user_time_watched_ratio['if_watched'] = np.where(
                user_time_watched_ratio['amount_of_time_watched']/user_time_watched_ratio['length'] > .75, 1, 0)

            # used for multilogistic regression
            if settings['modelType'] == 'multilogreg':
                user_time_watched_ratio.index.name = 'index'
                user_time_watched_ratio.reset_index(inplace=True)
                user_time_watched_ratio['if_watched_multi'] = user_time_watched_ratio['index'].apply(
                    partitionClasses)
                user_time_watched_ratio.drop('index', axis=1)

            # table of the categories for all videos in the videolibrary
            categories = pd.DataFrame.from_dict(data[1])
            categories['primary_category'] = categories['primary_category'].apply(
                rstrip)
            categories['sub_category'] = categories['sub_category'].apply(
                rstrip)
            categories['sub_sub_category'] = categories['sub_sub_category'].apply(
                rstrip)

            # table of videos with the ratio of number of unique views to total number of users

            vid_num_views = pd.DataFrame.from_dict(data[2])
            vid_num_views['vid_user_watched_ratio'] = vid_num_views['num_distinct_views']/num_users

            # table of videos with the count of how many times it has been selected, used later for other table calculations
            vid_num_selected = pd.DataFrame.from_dict(data[3])
            # table of videos with the ratio of number of times video has been selected to number of unique views,
            # merged with the vid_num_views table from above
            vid_view_info = pd.merge(
                vid_num_views, vid_num_selected, how='outer', on='vid')

            vid_view_info = vid_view_info.fillna(value=0)
            vid_view_info['vid_user_selected_watch_ratio'] = np.where(
                vid_view_info['num_distinct_views'] > 0, vid_view_info['num_selected']/vid_view_info['num_distinct_views'], 0)

            # table of the average amount of time in seconds that the video has been watched
            vid_avg_time_watched = pd.DataFrame.from_dict(data[4])
            vid_avg_time_watched['vid_avg_time_watched_ratio'] = vid_avg_time_watched['vid_avg_time_watched'] / \
                vid_avg_time_watched['length']

            # table of the average length of time that has passed since users watched the video and since the video was released
            vid_avg_interaction_span = pd.DataFrame.from_dict(data[5])
            # vid_avg_interaction_span['vid_avg_interaction_span_days'] = vid_avg_interaction_span['vid_avg_interaction_span_days'].apply(
            #    stripdays)

            # merges the tables together by vid to form one large table, vidfeatures
            # vidfeatures is a table of the entire videolibrary with the previously calculated columns
            vidfeatures = pd.merge(
                categories, vid_view_info, how='outer', on='vid')
            vidfeatures = pd.merge(
                vidfeatures, vid_avg_time_watched, how='outer', on='vid')
            vidfeatures = pd.merge(
                vidfeatures, vid_avg_interaction_span, how='outer', on='vid')
            vidfeatures = vidfeatures.fillna(value=0)

            # drops features set to False by user in featureSettings + other unused table columns
            # global userDefinedFeatures
            # userDefinedFeatures = [f[0] for f in featureSettings.items() if f[1] is True]
            dropfeatures = [f[0]
                            for f in featureSettings.items() if f[1] is False]
            vidfeatures = vidfeatures.drop(
                ['num_distinct_views', 'num_selected', 'length', 'vid_avg_time_watched'], axis=1)
            vidfeatures = vidfeatures.drop(dropfeatures, axis=1)

            print("after drop features")

            if (featureSettings['primary_category'] is False or featureSettings['sub_category'] is False or featureSettings['sub_sub_category'] is False):
                cats = ['primary_category', 'sub_category', 'sub_sub_category']
                subsetfeats = [f[0] for f in featureSettings.items() if (
                    (f[1] is True) and (f[0] in cats))]
                vidfeatures = pd.get_dummies(vidfeatures, columns=subsetfeats)
            else:
                vidfeatures = pd.get_dummies(
                    vidfeatures, columns=['primary_category', 'sub_category', 'sub_sub_category'])

            # subsection of the vidfeatures table of the videos that ONLY the specified user has watched/skipped
            # also contains the dependent variable, time_watched
            ttuserint = pd.merge(vidfeatures, user_time_watched_ratio, how='inner', on='vid').drop(
                ['amount_of_time_watched', 'length'], axis=1)

            # this is the subset of the vidfeatures table of the videos that we want to run through the trained model
            # to get our list of probabilities that the selected user will watch each video
            keys = list(ttuserint.vid.values)
            # final table. use this to push through the already trained model
            vidfeatures = vidfeatures[~vidfeatures.vid.isin(keys)]

            # final table. use this to test/train the model
            ttuserint = ttuserint.drop(['vid', 'title'], axis=1)

            if settings['modelType'] == 'logreg':
                tmpf1score, tmptp, tmpfp, tmptn, tmpfn = runLogisticRegression(
                    ttuserint, vidfeatures)
                f1score += tmpf1score
                tp += tmptp
                fp += tmpfp
                tn += tmptn
                fn += tmpfn
            elif settings['modelType'] == 'multilogreg':
                tmpf1score, tmptp, tmpfp, tmptn, tmpfn = runMultiLogisticRegression(
                    ttuserint, vidfeatures)
                f1score += tmpf1score
                tp += tmptp
                fp += tmpfp
                tn += tmptn
                fn += tmpfn
            elif settings['modelType'] == 'knn':
                tmpf1score, tmptp, tmpfp, tmptn, tmpfn = runKNN(
                    ttuserint, vidfeatures)
                f1score += tmpf1score
                tp += tmptp
                fp += tmpfp
                tn += tmptn
                fn += tmpfn
            elif settings['modelType'] == 'xgboost':
                tmpf1score, tmptp, tmpfp, tmptn, tmpfn = runXGBoost(
                    ttuserint, vidfeatures)
                f1score += tmpf1score
                tp += tmptp
                fp += tmpfp
                tn += tmptn
                fn += tmpfn
            elif settings['modelType'] == 'mlp':
                tmpf1score, tmptp, tmpfp, tmptn, tmpfn = runMLP(
                    ttuserint, vidfeatures)
                f1score += tmpf1score
                tp += tmptp
                fp += tmpfp
                tn += tmptn
                fn += tmpfn
            else:
                print('Invalid model type selection.')
        # print('Running model {model} on {n_Users} users:'.format(
        #     model=settings['modelType'], n_Users=n_Users))
        # print('F1 Score: {f1score}'.format(f1score=round(f1score/n_Users, 2)))
        # print('True Positive: {tp} (model is correct when it says user likes video)'.format(
        #     tp=round(tp/n_Users, 2)))
        # print('False Positive: {fp} (model says user likes video when they don\'t)'.format(
        #     fp=round(fp/n_Users, 2)))
        # print('True Negative: {tn} (model is correct when it says user doesn\'t like video)'.format(
        #     tn=round(tn/n_Users, 2)))
        # print('False Negative: {fn} (model says user doesn\'t like video when they do)'.format(
        #     fn=round(fn/n_Users, 2)))
        f1score = round(f1score/n_Users, 2)
        tp = round(tp/n_Users, 2)
        fp = round(fp/n_Users, 2)
        tn = round(tn/n_Users, 2)
        fn = round(fn/n_Users, 2)
        return({'f1score': f1score, 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn})

    else:
        userIDs = pd.DataFrame(data[0], columns=['uid'])
        # integer value of number of users. used in later calculations
        num_users = len(userIDs)

        # table of the video ids that the specified user has watched/skipped
        user_time_watched_ratio = pd.DataFrame.from_dict(data[6])
        user_time_watched_ratio['if_watched'] = np.where(
            user_time_watched_ratio['amount_of_time_watched']/user_time_watched_ratio['length'] > .75, 1, 0)

        # used for multilogistic regression
        if settings['modelType'] == 'multilogreg':
            user_time_watched_ratio.index.name = 'index'
            user_time_watched_ratio.reset_index(inplace=True)
            user_time_watched_ratio['if_watched_multi'] = user_time_watched_ratio['index'].apply(
                partitionClasses)
            user_time_watched_ratio.drop('index', axis=1)

        # table of the categories for all videos in the videolibrary
        categories = pd.DataFrame.from_dict(data[1])
        categories['primary_category'] = categories['primary_category'].apply(
            rstrip)
        categories['sub_category'] = categories['sub_category'].apply(rstrip)
        categories['sub_sub_category'] = categories['sub_sub_category'].apply(
            rstrip)

        # table of videos with the ratio of number of unique views to total number of users
        vid_num_views = pd.DataFrame.from_dict(data[2])
        vid_num_views['vid_user_watched_ratio'] = vid_num_views['num_distinct_views']/num_users

        # table of videos with the count of how many times it has been selected, used later for other table calculations
        vid_num_selected = pd.DataFrame.from_dict(data[3])

        # table of videos with the ratio of number of times video has been selected to number of unique views,
        # merged with the vid_num_views table from above
        vid_view_info = pd.merge(
            vid_num_views, vid_num_selected, how='outer', on='vid')
        vid_view_info = vid_view_info.fillna(value=0)
        vid_view_info['vid_user_selected_watch_ratio'] = np.where(
            vid_view_info['num_distinct_views'] > 0, vid_view_info['num_selected']/vid_view_info['num_distinct_views'], 0)

        # table of the average amount of time in seconds that the video has been watched
        vid_avg_time_watched = pd.DataFrame.from_dict(data[4])
        vid_avg_time_watched['vid_avg_time_watched_ratio'] = vid_avg_time_watched['vid_avg_time_watched'] / \
            vid_avg_time_watched['length']

        # table of the average length of time that has passed since users watched the video and since the video was released
        vid_avg_interaction_span = pd.DataFrame.from_dict(data[5])

        # merges the tables together by vid to form one large table, vidfeatures
        # vidfeatures is a table of the entire videolibrary with the previously calculated columns
        vidfeatures = pd.merge(
            categories, vid_view_info, how='outer', on='vid')
        vidfeatures = pd.merge(
            vidfeatures, vid_avg_time_watched, how='outer', on='vid')
        vidfeatures = pd.merge(
            vidfeatures, vid_avg_interaction_span, how='outer', on='vid')
        vidfeatures = vidfeatures.fillna(value=0)

        # drops features set to False by user in featureSettings + other unused table columns
        # global userDefinedFeatures
        # userDefinedFeatures = [f[0] for f in featureSettings.items() if f[1] is True]
        dropfeatures = [f[0] for f in featureSettings.items() if f[1] is False]
        vidfeatures = vidfeatures.drop(
            ['num_distinct_views', 'num_selected', 'length', 'vid_avg_time_watched'], axis=1)
        vidfeatures = vidfeatures.drop(dropfeatures, axis=1)

        if (featureSettings['primary_category'] is False or featureSettings['sub_category'] is False or featureSettings['sub_sub_category'] is False):
            cats = ['primary_category', 'sub_category', 'sub_sub_category']
            subsetfeats = [f[0] for f in featureSettings.items() if (
                (f[1] is True) and (f[0] in cats))]
            vidfeatures = pd.get_dummies(vidfeatures, columns=subsetfeats)
        else:
            vidfeatures = pd.get_dummies(
                vidfeatures, columns=['primary_category', 'sub_category', 'sub_sub_category'])

        # subsection of the vidfeatures table of the videos that ONLY the specified user has watched/skipped
        # also contains the dependent variable, time_watched
        ttuserint = pd.merge(vidfeatures, user_time_watched_ratio, how='inner', on='vid').drop(
            ['amount_of_time_watched', 'length'], axis=1)

        # this is the subset of the vidfeatures table of the videos that we want to run through the trained model
        # to get our list of probabilities that the selected user will watch each video
        keys = list(ttuserint.vid.values)
        # final table. use this to push through the already trained model
        vidfeatures = vidfeatures[~vidfeatures.vid.isin(keys)]

        # final table. use this to test/train the model
        ttuserint = ttuserint.drop(['vid', 'title'], axis=1)

        if settings['modelType'] == 'logreg':
            return(runLogisticRegression(ttuserint, vidfeatures))
        elif settings['modelType'] == 'multilogreg':
            return(runMultiLogisticRegression(ttuserint, vidfeatures))
        elif settings['modelType'] == 'knn':
            return(runKNN(ttuserint, vidfeatures))
        elif settings['modelType'] == 'xgboost':
            return(runXGBoost(ttuserint, vidfeatures))
        elif settings['modelType'] == 'mlp':
            return(runMLP(ttuserint, vidfeatures))
        else:
            print('Invalid model type selection.')
