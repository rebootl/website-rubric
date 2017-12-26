#!/bin/bash
#
git ls-files | grep '.py' | xargs wc -l
git ls-files | grep '.html' | xargs wc -l
git ls-files | grep '.css' | xargs wc -l
git ls-files | grep '.js' | xargs wc -l
