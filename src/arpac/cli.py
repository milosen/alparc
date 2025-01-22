import logging
import os

import click

from arpac.io import EXAMPLE_EXTERNAL_LEXICON_PATH


ARC_WORKSPACE = "arc_workspace"


logger = logging.getLogger(__name__)


def setup_logging(workspace_path: str):
    logging.basicConfig(filename=os.path.join(workspace_path, "debug.log"), 
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.addHandler(logging.StreamHandler())


@click.group(help="========== ARC: Artificial languages with Rhythmicity Controls ==========\n\n" 
                  "ARC generates streams of syllables from an artificial language based on a natural language corpus (default: German). "
                  "It will also generate syllables, pseudo-words, and lexicons as byproducts of the artificial language creation.")
def cli():
    pass


@cli.command(help="Generate new lexicons and syllable streams.")
def generate():
    with open(EXAMPLE_EXTERNAL_LEXICON_PATH, "r") as file:
        print(file.read())
