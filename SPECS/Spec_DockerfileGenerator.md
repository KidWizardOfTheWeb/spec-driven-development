# Feature Spec: Dockerfile Generation from Python files

## Goal
- Generate a Dockerfile for a python script or a python project.
- This application is meant to ease passing around containerized applications for testing purposes without needing to write your own Dockerfile. The full version of this project is meant to create a Docker Image. However, there are some security concerns/caveats for being able to build an image without the user already having Docker installed and setup (see "Possible areas for expansion").

## Scope
- In: A Python script. This can either include one python file or include other modules with a flag for the cli input.
- Out: A dockerfile, created in the same directory as the original python file is from. This allows users th generate a docker image afterwards.

## Requirements
- Generator must be able to detect the minimum python version necessary for a given python script.
- Generator must be able to detect any extra imports needed for the particular Python script, on request of the user.

## Acceptance Criteria
- [ ] Dockerfile output for one Python script, no imports.
- [ ] Dockerfile output for one Python script, including imports.
- [ ] Dockerfile output for a specialized framework (Django, Flask, etc).

## Possible areas for expansion
- The dockerfile generator currently works with python scripts, as we are able to detect what we need in a given script using the AST module. In the future, we may be able to implement other types of projects as well.
- Dockerfiles are normally used to generate a Docker Image, which is what is normally used to run containerized applications. Ensuring Docker is installed by a user requires them to have WSL (requires admin permissions to install in powershell), so for this demonstration, we use Dockerfiles instead. In the future, our goal is to build Docker Images from this generator as well, automating the entire process rather than just the file.
- When Docker Images are able to be built from this generator, the Dockerfile Database should be expanded to support Docker Image uploads and time records. 