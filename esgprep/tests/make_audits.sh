#!/usr/bin/env bash

esgfetchini
md5deep -r ini > audits/fetch_all_projects
rm -fr ini

esgfetchini -p cmip5
md5deep -r ini > audits/fetch_one_projects
rm -fr ini

esgfetchini -p cmip5 cordex cmip6
md5deep -r ini > audits/fetch_list_of_projects
rm -fr ini
