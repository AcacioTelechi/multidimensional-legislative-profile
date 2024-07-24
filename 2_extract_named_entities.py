import os
from span_marker import SpanMarkerModel
from tqdm import tqdm
from dotenv import load_dotenv
from utils import utils
import concurrent.futures
import pandas as pd
import torch
import json


load_dotenv()

PROPS_FOLDER = os.getenv("PROPS_FOLDER")
NER_FOLDER = os.getenv("NER_FOLDER")
DF_FOLDER = "./output/df_props.csv"


def main():
    model = SpanMarkerModel.from_pretrained(
        "lxyuan/span-marker-bert-base-multilingual-uncased-multinerd",
        language="pt",
        show_progress_bar=False,
    )

    if torch.cuda.is_available():
        model.to("cuda")
        print(f"Using CUDA for processing on device {torch.cuda.get_device_name()}")
    else:
        print("CUDA not available, using CPU")

    df_props = pd.read_csv(DF_FOLDER)
    df_props_ementa_not_null = df_props[~df_props["ementa"].isnull()].copy()

    def process_row(row):
        ementa = row["ementa"]

        try:
            ner = model.predict(ementa)
            return {"id_prop": row["id"], "ner": ner}
        except Exception as e:
            print(f"Error during prediction for row {row['id']}: {e}")
            return

    # Parallel processing with detailed error handling
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            tqdm(
                executor.map(
                    process_row, [row for _, row in df_props_ementa_not_null.iterrows()]
                ),
                total=len(df_props_ementa_not_null),
            )
        )

    utils.save_json(NER_FOLDER, "NER", results)


if __name__ == "__main__":
    main()
