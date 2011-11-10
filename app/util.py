import cPickle as pickle
import gzip
import numpy as np
from sklearn.utils import safe_asanyarray
from sklearn.utils.extmath import safe_sparse_dot

def load_pickle(filename, encoding=None):
    opener = gzip.open if filename.endswith('.gz') else open
    f = opener(filename, 'rb')
    data = pickle.load(f)
    f.close()
    if encoding is not None:
        data = data.decode(encoding)
    return data

def save_pickle(filename, data, encoding=None):
    if encoding is not None:
        data = data.encode(encoding)
    opener = gzip.open if filename.endswith('.gz') else open
    f = opener(filename, 'wb')
    f.write(pickle.dumps(data))
    f.close()

def cosine_similarity(X, Y, copy=False):
    """Compute pairwise cosine similarities between rows in X and Y

    Cosine similarity is a normalized linear kernel with value ranging
      - -1: similar vectors with opposite signs
      - 0: completely dissimilar (orthogonal) vectors
      - 1: similar vectors (same sign)

    In practice, cosine similarity is often used to measure the
    relatedness of text documents represented by sparse vectors of word
    counts, frequencies or TF-IDF weights. In this cases all features
    are non negative and the similarities range from 0 to 1 instead.

    Cosine similarity can be used as an affinity matrix for spectral
    and power iteration clustering algorithms.

    Parameters
    ----------

    X: array or sparse matrix of shape (n_samples_1, n_features)

    Y: array or sparse matrix of shape (n_samples_2, n_features)

    copy: boolean, optional, True by default
        For memory efficiency, set to False to avoid copies of X and Y and
        accept them to be modified (inplace row normalization).

    Returns
    -------

    array or sparse matrix of shape (n_samples_1, n_samples_2)

    Examples
    --------

    >>> from scikits.learn.metrics.pairwise import cosine_similarity
    >>> X = np.asarray([[0, 1], [1, 1], [0, -1], [0, 0]], dtype=np.float64)
    >>> cosine_similarity(X, X).round(decimals=2)
    array([[ 1.  ,  0.71, -1.  ,  0.  ],
           [ 0.71,  1.  , -0.71,  0.  ],
           [-1.  , -0.71,  1.  ,  0.  ],
           [ 0.  ,  0.  ,  0.  ,  0.  ]])

    >>> from scipy.sparse import csr_matrix
    >>> X_sparse = csr_matrix(X)
    >>> cosine_similarity(X_sparse, X_sparse).toarray().round(decimals=2)
    array([[ 1.  ,  0.71, -1.  ,  0.  ],
           [ 0.71,  1.  , -0.71,  0.  ],
           [-1.  , -0.71,  1.  ,  0.  ],
           [ 0.  ,  0.  ,  0.  ,  0.  ]])

    It is possible to use the cosine similarity to perform similarity
    queries:

    >>> query = [[0.5, 0.9]]
    >>> cosine_similarity(X, query)
    array([[ 0.87415728],
           [ 0.96152395],
           [-0.87415728],
           [ 0.        ]])
    """
    # XXX: delayed import to avoid cyclic dependency between base, metrics
    # and preprocessing
    from sklearn.preprocessing import normalize
    X = safe_asanyarray(X)
    Y = safe_asanyarray(Y)

    X = normalize(X, norm='l2', copy=copy)
    Y = normalize(Y, norm='l2', copy=copy)
    return safe_sparse_dot(X, Y.T)
