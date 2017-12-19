#!/bin/bash
set -e

if [[ $TRAVIS != "true" ]]
then
    docker build -t teabot_endpoints .
    exit 0
fi

if [[ $TRAVIS_PULL_REQUEST == "false" && $TRAVIS_BRANCH == "master" ]]
then
    echo "Building images for master"
    docker build -t teabot_endpoints .
    # push to Docker hub
    docker login -u "$DOCKER_USER" -p "$DOCKER_PASS"
    docker tag teabot_endpoints akalair/teabot_endpoints
    docker push akalair/teabot_endpoints
    exit 0
fi

echo "Not building images as its not a master run"
