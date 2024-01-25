# 3rd parties service, Firestore, and Google Sheets data pipeline

## Overview
This project seamlessly synchronizes data between service X, Firestore and Google Sheets in near real-time, facilitated by webhook triggers. 
It is designed to automate the capture and analysis of proposal data, making it easier to manage submissions and updates directly within 
a familiar spreadsheet interface. The main goal is to get cleansed data for further analysis and iterative business process improvement.

## Features
- **Near Real-Time Synchronization**: Automatically updates Google Sheets with new proposal data from service X via Firestore as it arrives.
- **Data Validation**: Ensures only complete and valid proposal data is processed and stored.
- **Timestamp Localization**: Converts UTC timestamps to a specified local timezone for ease of understanding and analysis.
- **Deduplication**: Prevents duplicate entries in the Google Sheet, maintaining clean and accurate data records.
- **Easy Configuration**: Simple setup process with clear instructions for connecting Firestore and Google Sheets.
