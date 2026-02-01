from pykali.modules.genome import Genome
from pykali.modules.genomeset import GenomeSet
from pykali.modules.bands import Bands


bands = GenomeSet(
        Genome("EU490707", email="info@pharm.chula.ac.th"),
        Genome("NZ_HG937516", email="info@pharm.chula.ac.th")
    ).electrophorese('AAAAA', 30)
    
print(bands.labels)
print(bands.lanes)
print(bands.bin_edges)
print(bands.to_dataframe())

bands.plot()
