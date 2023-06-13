import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sqlalchemy import *
import time
import json


def itemDesc(id,ds):
    return ds.loc[ds['itemId'] == id]['description'].tolist()[0]

def itemTags(id,ds):
    return ds.loc[ds['itemId'] == id]['tag'].tolist()[0]

def itemName(id,ds):
    return ds.loc[ds['itemId'] == id]['title'].tolist()[0]

# Just reads the results out of the dictionary.
def recommend(ds,results,item_id, num):
    target = {}
    target["Target_name"] = itemName(item_id,ds)
    target["Target_ID"] = item_id
    target["Target_RecN"] = str(num)
    recs = results[item_id][:num]
    lis = []
    listarget = {"Target":target}
    lis.append(listarget)
    position = 0
    for rec in recs:
        dict = {}
        position+=1
        dict["Position"] = position
        dict["Name"] = itemName(rec[1],ds)
        dict["Desc"] = itemDesc(rec[1],ds)
        dict["Tags"] = itemTags(rec[1],ds)
        dict["Score"] = str(rec[0]) 
        lis.append(dict)
    return lis


def start(dbn, itid, nitems):
    start = time.perf_counter()
    dataprocessstart = time.perf_counter()
    print('sqlite:///./db'+str(dbn)+'.db?check_same_thread=False')
    engine = create_engine('sqlite:///db'+str(dbn)+'.db?check_same_thread=False')

    with engine.begin() as conn:
        query = text("SELECT * FROM items")
        ds = pd.read_sql_query(query, conn)
    dataprocessend = time.perf_counter() - dataprocessstart
    recstart = time.perf_counter()

    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(ds['description']+"|"+ds['tag'])

    cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)

    results = {}

    for idx, row in ds.iterrows():
        similar_indices = cosine_similarities[idx].argsort()[:-100:-1]
        similar_items = [(cosine_similarities[idx][i], ds['itemId'][i]) for i in similar_indices]

        results[row['itemId']] = similar_items[1:]

    print('done!')
    lis = recommend(ds,results,item_id=itid, num=nitems)
    recend = time.perf_counter() - recstart
    end = time.perf_counter() - start
    dict = {}
    dict["endpoint_execution_time"] = str(end)
    dict["data_processing_time"] = str(dataprocessend)
    dict["rec_exec_time"] = str(recend)
    lis.append(dict)
    return lis
