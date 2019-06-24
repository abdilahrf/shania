# -*- coding: utf-8 -*-
######################################################
##	        _         _ _ _       _           __ 	##
##	       | |       | (_) |     | |         / _|	##
##	   __ _| |__   __| |_| | __ _| |__  _ __| |_ 	##
##	  / _` | '_ \ / _` | | |/ _` | '_ \| '__|  _|	##
##	 | (_| | |_) | (_| | | | (_| | | | | |  | |  	##
##	  \__,_|_.__/ \__,_|_|_|\__,_|_| |_|_|  |_|  	##
##                                             		##
######################################################
# http://abdilahrf.github.io
# Date:  	2019/04/27 08:39
# Email: 	abdilah.pb@gmail.com
# Comment: 	Scan secrets from CI Build Logs

import requests
import json
import re
import urllib
import sys
import os

# travis = eure / gitlab = gitlab-org
travis_repos = "https://api.travis-ci.org/v3/owner/{}/repos?limit=100&offset=1"
travis_builds = "https://api.travis-ci.org/repos/{}/builds?limit=100&offset=1"
travis_log = "https://api.travis-ci.org/v3/job/{}/log.txt"
gitlab_repos = "https://gitlab.com/api/v4/groups/{}/projects"
gitlab_builds = "https://gitlab.com/api/v4/projects/{}/jobs"
gitlab_log = "https://gitlab.com/gitlab-org/gitlab-ce/-/jobs/{}/raw"

# ‘github’ or ‘bitbucket’.
circle_repos = "https://api.github.com/users/{}/repos"
circle_log = "https://circleci.com/api/v1.1/project/github/{}/{}"
CI_TOKEN = "[CI_TOKEN]"

def travis_hunt(target):
	slugs = []
	builds_id = []
	get_repos = requests.get(travis_repos.format(target)).json()
	for x in get_repos['repositories']:
		try:
			slugs.append(x['slug'])
		except Exception as e:
			pass
	print("[Travis CI] Found {} repo for {}!".format(len(slugs),target))
	if len(slugs) != 0:
		for slug in slugs:
			get_builds = requests.get(travis_builds.format(slug),headers={"Content-Type":"application/vnd.github.hellcat-preview+json"})
			if get_builds.status_code == 200:
				for a in get_builds.json():
					# its silly need to plus 1 ? weird
					builds_id.append(a["id"]+1)
		print("[Travis CI] Found {} builds for {}!".format(len(builds_id),target))
		if len(builds_id) != 0:
			result = open("{}-travis.txt".format(target),'a')
			for b in builds_id:
				get_logs = requests.get(travis_log.format(b)).text
				result.write(get_logs.encode('utf-8'))
			result.close()

def gitlab_hunt(target):
	headers={"PRIVATE-TOKEN":"[GITLAB_TOKEN]"}
	slugs = []
	builds_url = []
	get_repos = requests.get(gitlab_repos.format(target),headers=headers).json()
	if len(get_repos) != 0:
		for x in get_repos:
			try:
				slugs.append(x['path_with_namespace'])
			except Exception as e:
				pass

	print("[Gitlab CI] Found {} repo for {}!".format(len(slugs),target))
	if len(slugs) != 0:
		for slug in slugs:
			get_builds = requests.get(gitlab_builds.format(urllib.quote_plus(slug)),headers=headers).json()
			if len(get_builds) != 0:
				for builds in get_builds:
					try:
						builds_url.append(builds['web_url'])
					except Exception as e:
						pass
					# builds_url.append(str(builds['web_url']).encode("utf-8"))
		print("[Gitlab CI] Found {} builds for {}!".format(len(builds_url),target))

		if len(builds_url)!=0:
			result = open("{}-gitlab.txt".format(target),'a')
			for build in builds_url:
				get_logs = requests.get(build+"/raw",headers=headers).text
				result.write(build)
				result.write(get_logs.encode('utf-8'))
			result.close()

def circel_hunt(target):
	slugs = []
	out_url = []
	get_repos = requests.get(circle_repos.format(target)).json()
	for repo in get_repos:
		try:
			slugs.append(repo['full_name'].encode('utf-8'))
		except Exception as e:
			pass
	print("[Circle CI] Found {} repo for {}!".format(len(slugs),target))
	if len(slugs) != 0:
		for slug in slugs:
			for xx in range(1,1000):
				get_builds = requests.get(circle_log.format(slug,xx)).json()
				try:
					if get_builds["message"] == "Build not found" or get_builds["message"] == "Project not found":
						break
				except Exception as e:
					pass
				for build in get_builds['steps']:
					try:
						out_url.append(build["actions"][0]["output_url"])
					except Exception as e:
						pass
		print("[Circle CI] Found {} output for {}!".format(len(out_url),target))
		if len(out_url) != 0:
			result = open("{}-circle.txt".format(target),'a')
			for b in out_url:
				get_logs = requests.get(b).json()[0]["message"]
				result.write(get_logs.encode("utf-8"))
			result.close()

def find_secret(target,provider):
	if provider == 1:
		provider ="gitlab"
		try:
			data = open(target+'-gitlab.txt','r').read()
		except Exception as e:
			exit(1)
	elif provider == 2:
		provider ="travis"
		try:
			data = open(target+'-travis.txt','r').read()
		except Exception as e:
			exit(1)
	elif provider == 3:
		provider ="circle"
		try:
			data = open(target+'-circle.txt','r').read()
		except Exception as e:
			exit(1)	

	result = open('{}-{}-leaks.txt'.format(target,provider),'w')
	matching = open('./secrets-variable.txt','r').read()
	matching = matching.split("\n")
	for x in matching:
		cari = re.findall(x,data)
		if cari:
			result.write(x.split("[")[0]+":\n"+"\n".join(cari)+"\n")
			print("Found {}".format(x))
	os.system("awk '!x[$0]++' {}-{}-leaks.txt > {}-{}-leaks-clean.txt".format(target,provider,target,provider))

if __name__ == '__main__':

	if len(sys.argv) <= 2:
		print "Usage: python secret-ci.py TARGET [1 (gitlab)|2 (travis)|3 (circel)]"

	target = sys.argv[1]
	provider = sys.argv[2]

	if int(provider) == 1:
		gitlab_hunt(target)
		find_secret(target,1)
	elif int(provider) == 2:
		travis_hunt(target)
		find_secret(target,2)
	elif int(provider) == 3:
		circel_hunt(target)
		find_secret(target,3)

