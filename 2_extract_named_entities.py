import os
from span_marker import SpanMarkerModel
from tqdm import tqdm
from dotenv import load_dotenv
from utils import utils
import concurrent.futures

load_dotenv()

PROPS_FOLDER = os.getenv("PROPS_FOLDER")
NER_FOLDER = os.getenv("NER_FOLDER")

def main():
    seen_props = set(os.listdir(NER_FOLDER))

    model = SpanMarkerModel.from_pretrained(
        "lxyuan/span-marker-bert-base-multilingual-uncased-multinerd",
        language="pt",
    )
    model.try_cuda()  # Assuming you have a GPU

    def process_prop(prop):  
        if prop in seen_props:
            return
        
        prop_data = utils.open_json(PROPS_FOLDER, prop)
        ementa = prop_data[0].get("ementa")

        if not ementa:
            return

        ner = model.predict(ementa)
        utils.save_json(NER_FOLDER, prop.split('.')[0], ner)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        props_to_process = [prop for prop in os.listdir(PROPS_FOLDER) if prop not in seen_props]
        with tqdm(total=len(props_to_process)) as pbar:  # Initialize the progress bar
            futures = {executor.submit(process_prop, prop): prop for prop in props_to_process}
            for future in concurrent.futures.as_completed(futures):
                # Catch any exceptions raised in the process_prop function
                try:
                    future.result()  
                except Exception as e:
                    print(f"Error processing {futures[future]}: {e}")
                pbar.update(1)  # Update the progress bar after each task completes


if __name__ == '__main__':
    main()