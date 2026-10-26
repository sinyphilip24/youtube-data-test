Creates category, video engagement, and regional reporting Delta tables using aggregations and window functions.
from pyspark.sql import functions as F

from pyspark.sql.window import Window

 

silver = spark.table("silver_youtube_videos")

 

# 1. CATEGORY: one maximum observed view count per video/category.

category_per_video = (silver

    .groupBy("video_id", "category_name")

    .agg(F.max("view_count").alias("video_views")))

gold_category = (category_per_video

    .groupBy("category_name")

    .agg(F.countDistinct("video_id").alias("unique_videos"),

         F.sum("video_views").alias("total_views")))

gold_category.write.format("delta").mode("overwrite").saveAsTable("gold_youtube_category")

 

# 2. ENGAGEMENT: latest collected observation per unique video.

video_window = Window.partitionBy("video_id").orderBy(

    F.col("collected_at").desc(), F.col("view_count").desc())

latest_video = (silver.withColumn("rn", F.row_number().over(video_window))

    .filter(F.col("rn") == 1).drop("rn"))

gold_engagement = latest_video.withColumn(

    "engagement_rate",

    F.when(F.col("view_count") > 0,

           F.round((F.coalesce(F.col("like_count"), F.lit(0)) +

                    F.coalesce(F.col("comment_count"), F.lit(0))) /

                   F.col("view_count") * 100, 2))

     .otherwise(F.lit(0.0)))

gold_engagement.write.format("delta").mode("overwrite").saveAsTable("gold_youtube_engagement")

 

# 3. REGION: latest observation for each video in each region.

region_window = Window.partitionBy("video_id", "trending_region").orderBy(

    F.col("collected_at").desc(), F.col("view_count").desc())

latest_region = (silver.withColumn("rn", F.row_number().over(region_window))

    .filter(F.col("rn") == 1).drop("rn"))

gold_region = (latest_region.groupBy("trending_region")

    .agg(F.countDistinct("video_id").alias("unique_videos"),

         F.round(F.avg("view_count"), 2).alias("avg_views"),

         F.max("view_count").alias("max_views")))

gold_region.write.format("delta").mode("overwrite").saveAsTable("gold_youtube_region")

 

print("Category rows:", gold_category.count())

print("Unique video rows:", gold_engagement.count())

print("Region rows:", gold_region.count())
