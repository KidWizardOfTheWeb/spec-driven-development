# Feature Spec: File Database for Dockerfiles, testing results, etc. 

## Goal
- This application provides the ability to store Dockerfiles (or any other kind of text-based file, such as JSONs, YAML, etc) into a database. The database is organized by time and date for easy record keeping.
- By having users able to upload files to the database, incremental steps in testing in a QA environment can be taken into account, seeing every individual iteration of a program being tested.
- E.g. If a new version of the project is created, a Dockerfile can be generated and stored for any other user to generate their own Docker Image from. Notes about a specific build can also be uploaded, making it easier for testers to take note of when bugs happen for what build, and it becomes timestamped.
- Results can be retrieved and viewed from the database as well, keeping a clean, sqlite3 based record of development and testing results/notes/data of any type.

## Scope
- In: A Dockerfile, or any text based file works. 
- Out: An entry of the file (organized by timestamp) in a locally created database named `dockerfiles.db`.

## Requirements
- Database must be able to store files given by a user.
- Database must be able to retrieve files given by a user.
- Database must be able to retrieve files by date.

## Acceptance Criteria
- [ ] Database stores a Dockerfile entry into `dockerfiles.db`
- [ ] Dockerfile entries must include a name for the file, date, time, and contents of the file.
- [ ] Database retrieves all Dockerfiles.
- [ ] Database can query for Dockerfiles given on a specific date and retrieve files.
- [ ] Database can query for Dockerfiles given on a specific date and by name.
- [ ] Database can view all dates Dockerfiles have been stored on.
- [ ] Database fails to add Dockerfiles with an empty name.

## Possible areas for expansion
- When Docker Images are able to be built from this generator, the Dockerfile Database should be expanded to support Docker Image uploads and time-based records. For this demonstration, it was requested to run locally. But ideally, the database would be able to send full Docker Images to a service like AWS Elastic Container Registry and be accessible by the entire QA team. The program can be ran multiple times, chaining a container upload, Dockerfile storage, and testing results/notes for a specific build. All of this being timestamped makes record keeping a snap.
- There should be a verbiage change to the given options to indicate that *any* type of file can be added to the database. The reason it is important we indicate this is, that users should be able to upload testing reports/details about a particular build. Like the example above, I'd like an expanded version of this application to be able to upload testing reports and important information to a database, while a Docker Image is pushed to AWS ECS or another registry, making it easier for the QA team to keep track of builds being tested.