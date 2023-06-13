import pandas as pd
from sqlalchemy import *
from fuzzywuzzy import fuzz
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import numpy as np
import matplotlib.pyplot as plt
import time
from fastapi.responses import JSONResponse



def fuzzy_matching(mapper, fav_item, verbose=True):
    """
    return the closest match via fuzzy ratio. 
    
    Parameters
    ----------    
    mapper: dict, map item title name to index of the item in data

    fav_item: str, name of user input item
    
    verbose: bool, print log if True

    Return
    ------
    index of the closest match
    """
    match_tuple = []
    # get match
    for title, idx in mapper.items():
        ratio = fuzz.ratio(title.lower(), fav_item.lower())
        if ratio >= 60:
            match_tuple.append((title, idx, ratio))
    # sort
    match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
    if not match_tuple:
        print('Oops! No match is found')
        return
    if verbose:
        print('Found possible matches in our database: {0}\n'.format([x[0] for x in match_tuple]))
    return match_tuple[0][1]



def make_recommendation(model_knn, data, mapper, fav_item, n_recommendations,engine):
    """
    return top n similar item recommendations based on user's input item


    Parameters
    ----------
    model_knn: sklearn model, knn model

    data: item-user matrix

    mapper: dict, map item title name to index of the item in data

    fav_item: str, name of user input item

    n_recommendations: int, top n recommendations

    Return
    ------
    list of top n similar item recommendations
    """
    model_knn.fit(data)
    idx = fuzzy_matching(mapper, fav_item, verbose=True)
    print(" "+ str(idx) +" ")
    print('Recommendation system start to make inference')
    print('......\n')
    distances, indices = model_knn.kneighbors(data[idx], n_neighbors=n_recommendations+1)
    raw_recommends = sorted(list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())), key=lambda x: x[1])[:0:-1]
    reverse_mapper = {v: k for k, v in mapper.items()}

    print('Recommendations for {}:'.format(fav_item))
    recommendations = []
    for i, (idx, dist) in enumerate(raw_recommends):
        with engine.begin() as conn: # Fetch item info from the database
            query = text(f"SELECT * FROM items WHERE title='{reverse_mapper[idx]}'")
            item_info = pd.read_sql_query(query, conn)
        item_info_dict = item_info.to_dict(orient='records')[0] # Convert to dictionary
        item_info_dict['rank'] = i+1
        item_info_dict['distance'] = dist
        recommendations.append(item_info_dict)
        print('{0}: {1}, with distance of {2}'.format(i+1, reverse_mapper[idx], dist))
    return recommendations


def start(nrec,sel_item):
    start = time.perf_counter()


    dataprocessstart = time.perf_counter()
    engine = create_engine('sqlite:///db'+str('0')+'.db?check_same_thread=False')

    


    # read data

    with engine.begin() as conn:
        query = text("SELECT * FROM items")
        df_items = pd.read_sql_query(query, conn)
    with engine.begin() as conn:
        query = text("SELECT * FROM users")
        df_ratings = pd.read_sql_query(query, conn)


    df_items.head()
    df_items.shape


    df_ratings.head()


    # df_ratings.shape
    df_ratings=df_ratings[:2000000]



    df_ratings.shape


    # pivot ratings into item features
    df_item_features = df_ratings.pivot(
        index='itemId',
        columns='userId',
        values='rating'
    ).fillna(0)

    dataprocessend = time.perf_counter() - dataprocessstart
    recstart = time.perf_counter()
    mat_item_features = csr_matrix(df_item_features.values)



    df_item_features.head()

    model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)


    num_users = len(df_ratings.userId.unique())
    num_items = len(df_ratings.itemId.unique())
    print('There are {} unique users and {} unique items in this data set'.format(num_users, num_items))


    # get count
    df_ratings_cnt_tmp = pd.DataFrame(df_ratings.groupby('rating').size(), columns=['count'])


    # there are a lot more counts in rating of zero
    total_cnt = num_users * num_items
    rating_zero_cnt = total_cnt - df_ratings.shape[0]

    df_ratings_cnt = df_ratings_cnt_tmp.append(
        pd.DataFrame({'count': rating_zero_cnt}, index=[0.0]),
        verify_integrity=True,
    ).sort_index()




    #log normalise to make it easier to interpret on a graph

    df_ratings_cnt['log_count'] = np.log(df_ratings_cnt['count'])
    df_ratings_cnt

    plt.style.use('ggplot')

    ax = df_ratings_cnt[['count']].reset_index().rename(columns={'index': 'rating score'}).plot(
        x='rating score',
        y='count',
        kind='bar',
        figsize=(12, 8),
        title='Count for Each Rating Score (in Log Scale)',
        logy=True,
        fontsize=12,
    )
    ax.set_xlabel("item rating score")
    ax.set_ylabel("number of ratings")



    # get rating frequency
    #number of ratings each item got.
    df_items_cnt = pd.DataFrame(df_ratings.groupby('itemId').size(), columns=['count'])
    df_items_cnt.head()



    #now we need to take only items that have been rated atleast 50 times to get some idea of the reactions of users towards it

    #Popularity threshold. Used later to exclude items that have not been rated X times.
    popularity_thres = 1
    popular_items = list(set(df_items_cnt.query('count >= @popularity_thres').index))
    df_ratings_drop_items = df_ratings[df_ratings.itemId.isin(popular_items)]
    print('shape of original ratings data: ', df_ratings.shape)
    print('shape of ratings data after dropping unpopular items: ', df_ratings_drop_items.shape)


    # get number of ratings given by every user
    df_users_cnt = pd.DataFrame(df_ratings_drop_items.groupby('userId').size(), columns=['count'])
    df_users_cnt.head()



    # filter data to come to an approximation of user likings. May be used to detect inactive users.
    ratings_thres = 1
    active_users = list(set(df_users_cnt.query('count >= @ratings_thres').index))
    df_ratings_drop_users = df_ratings_drop_items[df_ratings_drop_items.userId.isin(active_users)]
    print('shape of original ratings data: ', df_ratings.shape)
    print('shape of ratings data after dropping both unpopular items and inactive users: ', df_ratings_drop_users.shape)



    # pivot and create item-user matrix
    item_user_mat = df_ratings_drop_users.pivot(index='itemId', columns='userId', values='rating').fillna(0)
    # set 'itemId' as index
    df_items = df_items.set_index('itemId')

    # create the boolean index
    indexer = df_items.index.isin(item_user_mat.index)

    # apply the boolean index and get the titles
    item_to_idx = {item: i for i, item in enumerate(list(df_items.loc[indexer, 'title']))}
    # transform matrix to scipy sparse matrix
    item_user_mat_sparse = csr_matrix(item_user_mat.values)


    item_user_mat_sparse




    # define model
    model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
    # fit
    model_knn.fit(item_user_mat_sparse)


    my_favorite = sel_item


    output = make_recommendation(
    model_knn=model_knn,
    data=item_user_mat_sparse,
    fav_item=my_favorite,
    mapper=item_to_idx,
    n_recommendations=nrec,
    engine=engine
)

    recend = time.perf_counter() - recstart
    end = time.perf_counter() - start

    result = {
        "execution_time": {
            "total": end,
            "data_processing": dataprocessend,
            "recommendation": recend
        },
        "recommendations": output
    }

    return JSONResponse(content=result)



