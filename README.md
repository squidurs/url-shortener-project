# URL Shortener Project

## Introduction

Welcome to the URL Shortener Project. This project will guide you through building a URL shortener application in multiple stages.

## Project Parts

- Part 0: Understanding Design Principles
- Part 1: Building a Simple URL Shortener
- Part 2: Deploying and Hosting
- Part 3: Users and Permissions
- Part 4: Building a URL Shortener CLI
- Part 5: Performance Testing

Double click on the html files for these instructions under ```docs/``` to open them up on your browser and follow along. 

Organizing Your Coachable Repository
------------------------------------

Have a Coachable repository where you also store your Leetcode solutions and any other code related to the program. This will help maintain a clear and structured portfolio of your work throughout the program.

## Getting Started

Follow the instructions in each part to complete the project. Make sure to set up your environment and install the necessary dependencies. We will provide you with some basic setup and file structure, but it is ultimately up to you how to organize the project, these are just suggestions.

## Forking and Cloning the Repository

To showcase the project on your own GitHub profile and start working on it, follow these steps:

### Fork the Repository

1. Go to the [original repository](https://github.com/coachadelson/url-shortener-project).
2. Click the "Fork" button at the top right of the page to create a copy under your GitHub account.

### Clone Your Fork

1. Navigate to your GitHub profile and find the forked repository.
2. Click the "Code" button and copy the URL.
3. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/url-shortener-project.git
   cd url-shortener-project

## Set Up the Project

Install the necessary dependencies:

```bash
pip install -r requirements.txt
```

Project Workflow
----------------

### Setting Up a Branch

Create a new branch for your work:

`git checkout -b your-branch-name`

### Making Changes

Make your code changes and add them to the staging area:

`git add .`

Commit your changes with a meaningful message:

`git commit -m "Your commit message"`

### Pushing Changes

Push your branch to your forked repository:

`git push origin your-branch-name`

### Submitting a Pull Request

1.  Go to your forked repository on GitHub.
2.  Click the "Compare & pull request" button.
3.  Provide a clear title and description for your pull request and submit it.

Send it to us on Slack, your coach will review your pull request and provide feedback.

Keeping Your Fork Updated
-------------------------
NOTE: This is for if any updates or changes are made to the project. We will let you know if you need to do this! 

Add the original repository as a remote:

`git remote add upstream https://github.com/coachadelson/url-shortener-project.git`

Fetch the latest changes from the original repository:

`git fetch upstream`

Merge the changes into your local main branch:

`git checkout main
git merge upstream/main`
