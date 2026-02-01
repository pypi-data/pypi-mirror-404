import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import core.randomizer as rnd

isimler = list(rnd.names())


def generate_turkish_name():
    isimler = random.choice(isimler)

    return isimler
