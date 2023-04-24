#!/bin/bash

set -ex

if [ "${CI_COMMIT_BRANCH}" == "main" ]; then
  echo "ensuring local clone does not exist"
  test -e gitlab && rm -rfv gitlab
  echo "cloning from gitlab"
  git clone git@gitlab.botthouse.net:botthouse/vault2secretsmanager.git gitlab
  cd gitlab
  echo "adding github repo"
  git remote add git@github.com:tmb28054/vault2secretsmanager.git github
  echo "pushing to github"
  git push -u github main
fi

