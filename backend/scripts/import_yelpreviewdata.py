"""
    Process to Import yelp data from kaggle dataset file. 
    Plan to migrate this process to a live API feed once we get an end-to-end MVP

"""

import os
import json
import ast
import time
import random
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI


## Configure final version of functions used to clean/normalize import data
## import that file into this file once done
## generate test script to test effectiveness of process and load top 100 ( we can adapt our current process)
