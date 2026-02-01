import Bio
print(Bio.__version__)

from Bio import SeqIO
from Bio import Entrez

import numpy as np

import re
Entrez.email = "narapol.p@chula.ac.th"

stream = stream = Entrez.efetch(db="nucleotide", id="EU490707", rettype="gb", retmode="text")
record = SeqIO.read(stream, "genbank")

def restrict(seq, motif):
  import re
  begin = 0
  pattern = re.compile(motif)
  matches = pattern.finditer(seq if isinstance(seq, str) else str(seq))
  fragment = []
  for match in matches:
    fragment.append(match.start() - begin)
    begin = match.end()
  return fragment

def electrophorese(resolution, *fragments):
  min = np.min(fragments)
  max = np.max(fragments)
  gel = []
  for fragment in fragments:
    gel.append(np.histogram(fragment, bins= resolution, range=(min,max))[0])
  return gel

def distance_matrix(gel):
  import itertools
  from scipy.spatial import distance

  for lanes in list(itertools.combinations(gel, 2)):
    distance.jaccard(lanes[0], lanes[1])