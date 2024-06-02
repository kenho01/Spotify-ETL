# Spotify ETL Process with Airflow Scheduler

## Overview
This repository contains a simple Extract, Transform, Load (ETL) process implemented in Python using Flask for data extraction from the Spotify API, transformation of the data and loading it into a SQL table. The ETl process retrieves the songs that a user listened to the previous day and appeneds them to a SQL table. Moreover, the ETL process is scheduled to run daily without intervention using Apache Airflow.

