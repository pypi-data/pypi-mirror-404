import pytest
from pykali.modules.genome import Genome

class TestGenome:
    
    def test_fetch(self):
        assert Genome("EU490707")
        assert Genome("NZ_HG937516")

    def test_len(self):
        genome = Genome("EU490707")
        assert len(genome) == 1302

    def test_restrict(self):
        genome = Genome("EU490707")
        assert genome.restrict("AAAAA") == [124, 118, 248, 139, 508]
    
    def test_hash(self):
        assert hash(Genome("EU490707")) == hash("EU490707")
        assert hash(Genome("NZ_HG937516")) == hash("NZ_HG937516")

    def test_eq(self):
        genome1 = Genome("EU490707")
        genome2 = Genome("EU490707")
        genome3 = Genome("NZ_HG937516")

        assert (genome1 == genome2) == True
        assert (genome1 == genome3) == False

    def test_nq(self):
        genome1 = Genome("EU490707")
        genome2 = Genome("EU490707")
        genome3 = Genome("NZ_HG937516")

        assert (genome1 != genome2) == False
        assert (genome1 != genome3) == True

    # def test_gt(self):
    #     genome1 = Genome("EU490707")
    #     genome2 = Genome("EU490707")
    #     genome3 = Genome("NZ_HG937516")

    #     assert (genome1 > genome2) == False
    #     assert (genome3 > genome1) == True
