import os
import concurrent.futures

import pandas as pd
from tqdm import tqdm

from utils import utils
from dotenv import load_dotenv

load_dotenv()

DATE_FORMAT = os.getenv("DATE_FORMAT")
PROPS_FOLDER = os.getenv("PROPS_FOLDER")
PROPS_AUTHORS_FOLDER = os.getenv("PROPS_AUTHORS_FOLDER")
PROPS_TOPICS_FOLDER = os.getenv("PROPS_TOPICS_FOLDER")


def main():
    props_files = os.listdir(PROPS_FOLDER)

    props_data = []
    props_authors = []
    props_topics = []

    def process_props_file(props_file):
        data = utils.open_json(PROPS_FOLDER, props_file)
        authors_data = utils.open_json(PROPS_AUTHORS_FOLDER, props_file)
        topic_data = utils.open_json(PROPS_TOPICS_FOLDER, props_file)

        prop_id = props_file.split(".")[0]
        for pad in authors_data:
            pad["id_prop"] = prop_id
        for td in topic_data:
            td["id_prop"] = prop_id

        return data, authors_data, topic_data

    # load
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            tqdm(executor.map(process_props_file, props_files), total=len(props_files))
        )

    for data, authors_data, topic_data in results:
        props_data += data
        props_authors += authors_data
        props_topics += topic_data

    # save
    pd.DataFrame(props_data).to_csv("./output/df_props.csv", index=False)
    pd.DataFrame(props_authors).to_csv("./output/df_authors.csv", index=False)
    pd.DataFrame(props_topics).to_csv("./output/df_topics.csv", index=False)


if __name__ == "__main__":
    main()
