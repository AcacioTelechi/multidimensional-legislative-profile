import cProfile
import pstats
import os  # Add this line
import io  # Add this line

import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from dotenv import load_dotenv

from utils import api, endpoints, utils

import logging

load_dotenv()


logging.basicConfig(
    filename="extraction.log",  # Log to a file
    level=logging.INFO,                 # Log info level and above
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DATE_FORMAT = os.getenv("DATE_FORMAT")
PROPS_FOLDER = os.getenv("PROPS_FOLDER")
PROPS_AUTHORS_FOLDER = os.getenv("PROPS_AUTHORS_FOLDER")
PROPS_TOPICS_FOLDER = os.getenv("PROPS_TOPICS_FOLDER")
TIMEDELTA = int(os.getenv("TIMEDELTA"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS"))

def main():
    def process_proposition(prop, date_init, date_end):
        """Fetches and saves proposition details, authors, and topics."""
        id_prop = str(prop.get("id"))
        uri = prop.get("uri")


        if os.path.exists(os.path.join(PROPS_FOLDER, id_prop + ".json")):
            return  # Skip if already processed

        try:
            prop_det = api.request(uri)
            authors = api.request(uri + "/autores")
            topics = api.request(uri + "/temas")

            utils.save_json(PROPS_AUTHORS_FOLDER, id_prop, authors)
            utils.save_json(PROPS_TOPICS_FOLDER, id_prop, topics)
            utils.save_json(PROPS_FOLDER, id_prop, prop_det)

            # logging.info(f"Processed proposition {id_prop} for date range {date_init} - {date_end}")
        except Exception as e:
            logging.error(f"Error processing proposition {id_prop}: {e}")

    date_init = datetime.date(2019, 1, 1)
    date_end = date_init + datetime.timedelta(int(TIMEDELTA))
    today = datetime.date.today()
    days = (today - date_init).days

    pbar_days = tqdm(range(0, days), desc="Days", position=0)
    pbar_props = tqdm(desc="Downloading Propositions", position=1)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            params = {
                "dataApresentacaoInicio": date_init.strftime(DATE_FORMAT),
                "dataApresentacaoFim": date_end.strftime(DATE_FORMAT),
                "itens":999
            }

            url = api.construct_url(api.HOST, endpoints.PROPOSICAO, params)
            # print(url)
            props = api.request(url)
            logging.info(f"Fetched {len(props)} propositions for date range {date_init} - {date_end}")

            pbar_props.total = len(props)  # Update the propositions progress bar total

            futures = [executor.submit(process_proposition, prop, date_init, date_end) for prop in props]

            for future in as_completed(futures):
                future.result()
                pbar_props.update(1)
                
            date_init = date_end + datetime.timedelta(1)
            date_end = min(date_init + datetime.timedelta(int(TIMEDELTA)), today)  # Cap the end date at today

            pbar_days.update(TIMEDELTA)
            pbar_props.reset()

            if date_init >= today:
                break

    logging.info("Extraction complete!")

if __name__ == "__main__":
    # Create a profiler object
    profiler = cProfile.Profile()

    # Start the profiler
    profiler.enable()

    # Run your main function (where your extraction logic resides)
    main()

    # Stop the profiler
    profiler.disable()

    # Stream profiler stats to a string buffer
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats()

    # Print the profiler stats to the console
    print(s.getvalue())

    # Save profiler stats to a file (optional)
    with open("profiling_results.txt", "w+") as f:
        ps = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
        ps.print_stats()
