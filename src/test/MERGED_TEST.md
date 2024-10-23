#!/bin/bash

# Create a new repository
mkdir CCTV_Backend_V2
cd CCTV_Backend_V2
git init

# Set up the new remote
git remote add origin https://github.com/Naris167/CCTV_Backend_V2.git

create a test file and commit on master as initial commit

# Create and switch to bmatraffic branch
git checkout -b bmatraffic
git remote add bmatraffic https://github.com/Naris167/bmatraffic_cctv_scraping.git
git fetch bmatraffic
git merge remotes/bmatraffic/master --allow-unrelated-histories

# Move all content to a subdirectory
mkdir bmatraffic-content
git mv -k * bmatraffic-content/
git commit -m "Move bmatraffic content to subdirectory"

# Create and switch to cctv-backend branch
git checkout -b cctv-backend
git remote add cctv-backend https://github.com/Naris167/CCTV_Backend.git
git fetch cctv-backend
git merge remotes/cctv-backend/master --allow-unrelated-histories

# Move all content to a subdirectory
mkdir cctv-backend-content
git mv -k * cctv-backend-content/
git commit -m "Move CCTV_Backend content to subdirectory"

# Create master branch and merge both other branches
git checkout -b master
git merge bmatraffic --allow-unrelated-histories
git merge cctv-backend --allow-unrelated-histories

echo "Repositories merged. Please resolve any conflicts if they occurred."
echo "You now have three branches: master, bmatraffic, and cctv-backend"
echo "Each original repo's content is in a separate subdirectory in the master branch"
echo "Remember to push changes to the new remote with: git push -u origin master"