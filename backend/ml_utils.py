
from langchain_huggingface import HuggingFaceEmbeddings
import pandas as pd
from sklearn.model_selection import train_test_split



#*********Functions for dealing with Model related tasks...************

#Read dataset for model creation
def read_data(data):
    df = pd.read_csv(data,delimiter=',', header=None)
    return df

#Create embeddings instance
def get_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return embeddings

#Generating embeddings for our input dataset
def create_embeddings(df,embeddings):
    df[2] = df[0].apply(lambda x: embeddings.embed_query(x))
    return df

#Splitting the data into train & test
def split_train_test__data(df_sample):
    # Split into training and testing sets
    sentences_train, sentences_test, labels_train, labels_test = train_test_split(
    list(df_sample[2]), list(df_sample[1]), test_size=0.25, random_state=0)
    print(len(sentences_train))
    return sentences_train, sentences_test, labels_train, labels_test

#Get the accuracy score on test data
def get_score(svm_classifier,sentences_test,labels_test):
    score = svm_classifier.score(sentences_test, labels_test)
    return score
