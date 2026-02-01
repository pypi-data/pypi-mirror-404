import pytest
from pykali.modules.genome import Genome
from pykali.modules.genomeset import GenomeSet

class TestGenomeSet:

    def test_init(self):
        genome = Genome("EU490707")
        assert GenomeSet(genome)

    def test_init_with_duplicate(self):
        genome1 = Genome("EU490707")
        genome2 = Genome("EU490707")

        assert len(GenomeSet(genome1,genome2)) == 1

    def test_init_with_distinct(self):
        genome1 = Genome("EU490707")
        genome2 = Genome("NZ_HG937516")

        assert len(GenomeSet(genome1,genome2)) == 2

    def test_names(self):
        genomes = GenomeSet(
            Genome("EU490707"),
            Genome("NZ_HG937516")
        )

        assert genomes.names() == ('NZ_HG937516', 'EU490707')

    def test_electrophorese(self):
        genomes = GenomeSet(
            Genome("EU490707"),
            Genome("NZ_HG937516")
        )

        assert genomes.electrophorese('AAAAA', 30)