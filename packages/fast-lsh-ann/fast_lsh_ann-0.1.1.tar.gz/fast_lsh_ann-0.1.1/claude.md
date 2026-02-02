# Fast LSH and ANN implementation
## Back ground 
    - I was working on implementing vector seach and finding Approaximate nearest neighbour for millions of embeddings in databricks vector search
    - problem was this does not have a batch api and scaling it was impossible 
    - I turned to LSH , where I fitted a MinHashLSH from spark (https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.ml.feature.BucketedRandomProjectionLSH.html) and fitted the embedding dataframe ( 100m records)
        - then transformed the dataframe of the vectors which I wanted to get nearest neighbours and then run approaximateSimilarity join and example is like this 
        ```
        from pyspark.ml.linalg import Vectors
        from pyspark.sql.functions import col
        data = [(0, Vectors.dense([-1.0, -1.0 ]),),
                (1, Vectors.dense([-1.0, 1.0 ]),),
                (2, Vectors.dense([1.0, -1.0 ]),),
                (3, Vectors.dense([1.0, 1.0]),)]
        df = spark.createDataFrame(data, ["id", "features"])
        brp = BucketedRandomProjectionLSH()
        brp.setInputCol("features")
        BucketedRandomProjectionLSH...
        brp.setOutputCol("hashes")
        BucketedRandomProjectionLSH...
        brp.setSeed(12345)
        BucketedRandomProjectionLSH...
        brp.setBucketLength(1.0)
        BucketedRandomProjectionLSH...
        model = brp.fit(df)
        model.getBucketLength()
        1.0
        model.setOutputCol("hashes")
        BucketedRandomProjectionLSHModel...
        model.transform(df).head()
        Row(id=0, features=DenseVector([-1.0, -1.0]), hashes=[DenseVector([-1.0])])
        data2 = [(4, Vectors.dense([2.0, 2.0 ]),),
                 (5, Vectors.dense([2.0, 3.0 ]),),
                 (6, Vectors.dense([3.0, 2.0 ]),),
                 (7, Vectors.dense([3.0, 3.0]),)]
        df2 = spark.createDataFrame(data2, ["id", "features"])
        model.approxNearestNeighbors(df2, Vectors.dense([1.0, 2.0]), 1).collect()
        [Row(id=4, features=DenseVector([2.0, 2.0]), hashes=[DenseVector([1.0])], distCol=1.0)]
        model.approxSimilarityJoin(df, df2, 3.0, distCol="EuclideanDistance").select(
            col("datasetA.id").alias("idA"),
            col("datasetB.id").alias("idB"),
            col("EuclideanDistance")).show()
        +---+---+-----------------+
        |idA|idB|EuclideanDistance|
        +---+---+-----------------+
        |  3|  6| 2.23606797749979|
        +---+---+-----------------+
        ```
    - However this is also not very fast 
    - I want to build something that can do this realiably in cpu ( rapids ml does it in gpu)but I am thinking something in rust that does it fast and have apython api that I can use 
    

## Goal 
    - build a rust backend python package that does Bucketed Random Projection LSH (idea is here as well https://www.pinecone.io/learn/series/faiss/locality-sensitive-hashing-random-projection/)
    - have similar api like the spark api 
    - should be scalable enough to do it millions of embedding search in reasonable time 
    - create benchmark with similar system 
    - installable via pip 
