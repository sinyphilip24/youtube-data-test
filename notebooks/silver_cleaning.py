Silver Layer — Cleaning & Validation

Deduplicates exact observation keys, standardises timestamps and numerical types, handles missing descriptions, validates quality, and writes a Delta table.

bronze = spark.table("bronze_youtube_videos")

 

# Keep one row per video/region/collection-time observation.

# A video can legitimately appear in more than one region.

silver = (bronze

    .dropDuplicates(["video_id", "trending_region", "collected_at"])

    .withColumn("description", F.coalesce(F.col("description"), F.lit("")))

    .withColumn("published_at", F.to_timestamp("published_at"))

    .withColumn("collected_at", F.to_timestamp("collected_at"))

    .withColumn("view_count", F.col("view_count").cast("long"))

    .withColumn("like_count", F.col("like_count").cast("long"))

    .withColumn("comment_count", F.col("comment_count").cast("long"))

    .withColumn("duration_seconds", F.col("duration_seconds").cast("long"))

    .withColumn("processed_at", F.current_timestamp())

)

 

# Fail early if the source contains invalid essential records.

invalid = silver.filter(

    F.col("video_id").isNull() |

    F.col("trending_region").isNull() |

    F.col("collected_at").isNull() |

    F.col("published_at").isNull() |

    (F.col("view_count") < 0) |

    (F.col("like_count") < 0) |

    (F.col("comment_count") < 0) |

    (F.col("duration_seconds") < 0)

)

assert invalid.count() == 0, "Silver validation failed; inspect invalid records."

 

silver.write.format("delta").mode("overwrite").saveAsTable("silver_youtube_videos")

print("Silver observations:", silver.count())
