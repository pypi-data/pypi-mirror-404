import pytest
from pykali.modules.genome import Genome
from pykali.modules.genomeset import GenomeSet
from pykali.modules.bands import Bands

class TestBands:

    def test_calculate_distance(self):
        bands = GenomeSet(
            Genome("EU490707"),
            Genome("NZ_HG937516")
        ).electrophorese('AAAAA', 30)
        
        assert bands.distance() == []