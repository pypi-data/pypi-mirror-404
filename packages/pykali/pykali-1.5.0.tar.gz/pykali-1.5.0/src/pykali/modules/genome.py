import re
import os

from urllib.error import HTTPError

from Bio import SeqIO
from Bio import Entrez



class Genome:
    """Represents a genome, either loaded from a file or fetched from the NCBI nucleotide database.
    
    This class allows loading genome sequences in FASTA format and provides functionality to:
    - Compare genome objects based on their hash values (derived from their names).
    - Calculate the total length of the genome sequence(s).
    - Simulate restriction enzyme digestion by identifying DNA motifs and returning fragment lengths.
    """

    def __init__(self, filepath_or_ncbiid, name = "", format = "fasta", email="info@pharm.chula.ac.th") -> None:
        """Initializes a Genome object by either loading from a local file or fetching from NCBI.
        
        Args:
            filepath_or_ncbiid (str): Path to a local genome file or NCBI ID of the genome.
            name (str, optional): A name for the genome. Defaults to the sequence ID or NCBI ID.
            format (str, optional): The format of the genome file. Default is "fasta".
            email (str, optional): Email address required by NCBI's Entrez system. Default is "info@pharm.chula.ac.th".
        
        Raises:
            Exception: If the file path or NCBI ID is not valid, raises an exception with a descriptive message.
        """

        if os.path.isfile(filepath_or_ncbiid):
            self.records = tuple(record for record in SeqIO.parse(filepath_or_ncbiid,format))
            self.name = name if name else self.records[0].id
        else:
            Entrez.email = email
            try:
                stream = Entrez.efetch(db="nucleotide", id=filepath_or_ncbiid, rettype="fasta", retmode="text")
                self.records = tuple(record for record in SeqIO.parse(stream, "fasta"))
                self.name = name if name else filepath_or_ncbiid
            except HTTPError as err:
                raise Exception(f"DataNotFound: The file or id {filepath_or_ncbiid} is not exist! ")

    def __hash__(self) -> int:
        """Returns the hash of the genome object based on its name.
        
        Returns:
            int: The hash value for the genome, computed from the `name` attribute.
        """

        return hash(self.name)
    
    def __eq__(self, other):
        """Compares two Genome objects for equality based on their hash values.
        
        Args:
            other (Genome): The other Genome object to compare.
        
        Returns:
            bool: True if both genome objects have the same hash value (i.e., they are equal), False otherwise.
        """

        return hash(self) == hash(other)
    
    def __ne__(self, other):
        """Compares two Genome objects for inequality based on their hash values.
        
        Args:
            other (Genome): The other Genome object to compare.
        
        Returns:
            bool: True if the genome objects have different hash values (i.e., they are not equal), False otherwise.
        """

        return hash(self) != hash(other)
    
    # def __gt__(self, other):
    #     return hash(self) > hash(other)
    
    # def __ge__(self, other):
    #     return hash(self) >= hash(other)
    
    # def __lt__(self, other):
    #     return hash(self) < hash(other)
    
    # def __le__(self, other):
    #     return hash(self) <= hash(other)

    def __len__(self):
        """Calculates the total length of the genome.
        
        This is the sum of the lengths of all sequence records in the genome.
        
        Returns:
            int: The total length of the genome in base pairs.
        """

        return sum(len(r) for r in self.records)

    def restrict(self, motif):
        """Simulates restriction enzyme digestion by identifying and splitting the genome at occurrences of a DNA motif.
        
        Args:
            motif (str): A DNA sequence motif (e.g., the recognition site of a restriction enzyme) to search for.
        
        Returns:
            list: A list of fragment lengths, representing the pieces of the genome after "cutting" at each motif occurrence.
        """
        
        pattern = re.compile(motif, re.I)
        fragment = []
        for record in self.records:
            begin = 0
            matches = pattern.finditer(str(record.seq))
            for match in matches:
                fragment.append(match.start() - begin)
                begin = match.end()

            fragment.append(len(record.seq) - begin)


        return fragment
