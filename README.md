# Service X, Firestore, and Google Sheets data pipeline

## Overview
 The project is a data pipeline based on the integration of Service X, Google Cloud Functions, Google Cloud Scheduler and Google Sheets API. It seamlessly synchronizes data between Service X, Firestore and Google Sheets.

### webhook-to-firestore-pipeline
The first function webhook-to-firestore-pipeline receives data from batches of POST webhooks with JSON, determines which of the POST requests fits validation and extracts certain keys with values (3 types in total: date, name and hyperlink, all three are string). In this case, the POST request is the HTTP trigger for the function execution. 
 
 In the same function, the extracted data is saved to the Google Firestore database, going through a couple more minor processes. This completes the first part of the data pipeline.

 ### firestore-to-google-sheets-pipeline
 The second part of the data pipeline is a function to extract and reconcile data between Firestore and Google Sheets. Using Cloud Scheduler (the cloud analog of `cron`), the function is called by HTTP trigger at specified intervals, reconciling data by unique identifier between the database and the spreadsheet, and adding new data to the spreadsheet. The process includes authentication by Google service account, date normalization for easy reading by meatbags :)) and... And that's it! It's not that big of a deal. Saves at least 4 hours a week of dumb mechanical work.

 If we talk about the ultimate goal of the process, the data exported to Sheets are further processed, which gives the data a qualitative assessment measured in quantitative values (yes, it is possible!), visualized, and used for iterative optimization of workflow and business processes.  
 
****************************************************************************************************************

P.S. Some other things, like setting up alerting by log events, creating a service account and Cloud Scheduler job, I didn't include in the description, but I'll leave the references below.
- [Service account overview](https://cloud.google.com/iam/docs/service-account-overview) 
- [Logging and Monitoring in Google Cloud](https://www.cloudskillsboost.google/paths/11/course_templates/99) 
- [Configure Service Accounts and IAM Roles for Google Cloud Course Lab](https://www.cloudskillsboost.google/course_templates/702)
- [Configure Service Accounts and IAM for Google Cloud: Challenge Lab](https://www.cloudskillsboost.google/focuses/67219?catalog_rank=%7B%22rank%22%3A1%2C%22num_filters%22%3A0%2C%22has_search%22%3Atrue%7D&parent=catalog&search_id=29556384) 

- [Cloud Scheduler: Qwik Start](https://www.cloudskillsboost.google/focuses/3556?catalog_rank=%7B%22rank%22%3A1%2C%22num_filters%22%3A0%2C%22has_search%22%3Atrue%7D&parent=catalog&search_id=29556428)

P.P.S. Many kudos to Keria for his advice on error handling and the error-first approach in code writing! :)

 
## Features
- **Automatic Data Synchronization**: Automatically updates Google Sheets with new data from service X via Firestore in a short time.
- **Data Validation**: Ensures only complete and valid data is processed and stored.
- **Timestamp Localization**: Converts UTC timestamps to a specified local timezone for ease of understanding and analysis.
- **Deduplication**: Prevents duplicate entries in the Google Sheet, maintaining clean and accurate data records.
