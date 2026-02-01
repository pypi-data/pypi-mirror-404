import numpy as np

from pykali.modules.genome import Genome
from pykali.modules.bands import Bands

class GenomeSet(set):
    """
    A class representing a set of Genome objects.

    Inherits from the built-in set class and adds functionality specific to genomic analysis,
    such as fetching the names of genomes in the set and simulating gel electrophoresis to
    visualize DNA fragment patterns from restriction digestion.

    Methods:
    - `__init__(self, *genomes: Genome)`: Initializes the GenomeSet with a variable number of Genome objects.
    - `names(self)`: Returns a tuple of genome names in the set.
    - `electrophorese(self, motif: str, bins: int)`: Simulates gel electrophoresis for each genome in the set based on a given DNA motif and returns the result as a Bands object.
    """

    def __init__(self, *genomes: Genome) -> None:
        """
        Initializes the GenomeSet object with one or more Genome objects.
        
        Args:
            *genomes (Genome): A variable number of Genome objects to add to the GenomeSet.
        """

        super().__init__(genomes)

    def names(self) -> tuple:
        """
        Returns the names of all the genomes in the GenomeSet.

        This is useful for labeling or identifying the genomes when performing operations like gel electrophoresis.

        Returns:
            tuple: A tuple of strings representing the names of each genome in the set.
        """

        return tuple(genome.name for genome in self)
    
    def electrophorese(self, motif: str, bins: int) -> Bands:
        """
        Simulates gel electrophoresis for each genome in the set, based on a given restriction motif.

        For each genome, the restriction enzyme recognition motif is used to "cut" the genome into fragments.
        These fragments are then visualized as histograms (lanes), simulating how fragments would appear on
        a gel in a lab experiment. The number of bins represents how the fragment sizes are grouped.

        Args:
            motif (str): A DNA sequence motif (e.g., a restriction enzyme site) to use for cutting the genomes.
            bins (int): The number of bins (size ranges) to divide the fragments into for the electrophoresis simulation.

        Returns:
            Bands: A Bands object containing the names of the genomes and their respective fragment distribution histograms.
        """
        
        fragments = []
        mins = []
        maxes = []

        for genome in self:
            fragment = genome.restrict(motif)
            fragments.append(fragment)
            mins.append(np.min(fragment))
            maxes.append(np.max(fragment))

        min = np.min(mins)
        max = np.max(maxes)

        lanes = []

        for fragment in fragments:
            lanes.append(np.histogram(fragment, bins= bins, range=(min,max)))

        return Bands(self.names(), lanes)
    