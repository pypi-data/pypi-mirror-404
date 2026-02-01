import numpy as np
import pandas as pd
import seaborn as sns

from scipy.spatial import distance

class Bands:
    """
    A class representing the fragment distribution of genomes after electrophoresis simulation.

    The `Bands` class stores the fragment patterns (lanes) for different genomes and provides
    methods to calculate pairwise distances between these lanes using various distance metrics.
    
    Attributes:
        labels (tuple): A tuple of strings representing the names or labels of the genomes.
        lanes (numpy.ndarray): A 2D NumPy array where each row represents the fragment distribution
                               (or lane) of a genome.
    
    Methods:
        calculate_distance(metric='euclidean', **kwargs): Calculates the pairwise distance between
                                                          all lanes using a specified distance metric.
        squareform_distance(metric='euclidean', **kwargs): Returns the pairwise distances in square-form
                                                           as a pandas DataFrame, with labels for rows and columns.
    """

    def __init__(self, labels, lanes) -> None:
        """
        Initializes the Bands object with genome labels and their respective fragment distribution (lanes).
        
        Args:
            labels (list or tuple): A list or tuple of strings representing the names or labels of the genomes.
            lanes (list or numpy.ndarray): A 2D array-like object where each row represents a genome's fragment distribution (lane).
        """
        self.labels = tuple(labels)
        self.lanes = np.array([lane[0] for lane in lanes])
        self.bin_edges = np.round(lanes[0][1])

    def calculate_distance(self, metric='euclidean', **kwargs) -> float:
        """
        Calculates the pairwise distances between genome fragment patterns (lanes) using a specified distance metric.
        
        Args:
            metric (str, optional): The distance metric to use (default is 'euclidean'). Can be any valid metric
                                    supported by `scipy.spatial.distance.pdist`, such as 'euclidean', 'cityblock', 'cosine', etc.
            **kwargs: Additional keyword arguments passed to `scipy.spatial.distance.pdist` for specific metrics.

        Returns:
            numpy.ndarray: A condensed distance matrix containing the pairwise distances between all lanes.
                           The matrix is in the form returned by `scipy.spatial.distance.pdist`.
        
        Example:
            >>> bands.calculate_distance(metric='cosine')
            array([...])
        """
        
        return distance.pdist(self.lanes, metric, **kwargs)

    
    def squareform_distance(self, metric='euclidean', **kwargs) -> float:
        """
        Returns the pairwise distances between genome fragment patterns (lanes) in square-form as a pandas DataFrame.
        
        The distance between all lanes is calculated using a specified distance metric, and the result is converted into
        a DataFrame with genome labels as row and column indices for better readability.

        Args:
            metric (str, optional): The distance metric to use (default is 'euclidean'). Can be any valid metric
                                    supported by `scipy.spatial.distance.pdist`.
            **kwargs: Additional keyword arguments passed to `scipy.spatial.distance.pdist`.

        Returns:
            pandas.DataFrame: A square-form distance matrix, where the rows and columns are labeled with genome names.
        
        Example:
            >>> bands.squareform_distance(metric='cityblock')
            # Output will be a DataFrame:
                Genome1  Genome2  Genome3
            Genome1      0.0      1.2      2.3
            Genome2      1.2      0.0      1.4
            Genome3      2.3      1.4      0.0
        """
        
        return pd.DataFrame(
            distance.squareform(
                distance.pdist(self.lanes, metric, **kwargs)
            ), 
            columns=self.labels, index=self.labels
        )

    def to_dataframe(self):
        """
        Returns the fragment patterns (lanes) as a pandas DataFrame.
        
        Returns:
            pandas.DataFrame: A DataFrame where each row represents a genome's fragment distribution (lane).
        """
        return pd.DataFrame(self.lanes, columns=self.bin_edges[1:], index=self.labels)
    
    def plot(self, output: str = 'out.png'):
        """
        Plots the pairwise distances between genome fragment patterns (lanes) as a heatmap.
        
        The distance between all lanes is calculated using a specified distance metric, and the result is converted into
        a DataFrame with genome labels as row and column indices for better readability.

        Args:
            **kwargs: Additional keyword arguments passed to `seaborn.heatmap`.

        Returns:
            seaborn.axisgrid.FacetGrid: A FacetGrid object containing the heatmap plot.
        """

        fig = sns.heatmap(self.to_dataframe(), cmap='binary').get_figure()
        fig.savefig(output)