#!/bin/bash

users=$(curl -s -H "application/vnd.github.hellcat-preview+json" -H "Authorization: token [GITHUB_TOKEN]" https://api.github.com/orgs/"$1"/members | jq -r .[].login);

while read -r hehe; do
  python `pwd`/main.py "$hehe" 1 2>/dev/null;
  python `pwd`/main.py "$hehe" 2 2>/dev/null;
  python `pwd`/main.py "$hehe" 3 2>/dev/null;
done <<< "$users"
