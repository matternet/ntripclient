#!/bin/bash
current_dir=$(pwd)
docker run -v $current_dir:/home/matternet $(docker build -q -f Dockerfile-xcompile .)
