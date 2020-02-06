import config
import hashlib
import urllib.request as urllib2
from github import Github,GithubException
from pathlib import Path

g = Github(config.key)

def download_file(url, filename):
    urllib2.urlretrieve(url, filename + '.yml')
    
def print_output(version_range, version_range_sha):
    print(version_range + " docker-compose.yml sha: " + version_range_sha)
    
def get_remote_hash(url,algorithm):
	remote = urllib2.urlopen(url)
	return hash(remote, algorithm)

def hash(remote, algorithm="md5"):
	max_file_size=100*1024*1024
	if algorithm=="md5":
		hash = hashlib.md5()
	elif algorithm=="sha1":
		hash = hashlib.sha1()
	elif algorithm=="sha256":
		hash = hashlib.sha256()
	elif algorithm=="sha384":
		hash = hashlib.sha384()
	elif algorithm=="sha512":
		hash = hashlib.sha512()

	total_read = 0
	while True:
		data = remote.read(4096)
		total_read += 4096

		if not data or total_read > max_file_size:
			break

		hash.update(data)

	return hash.hexdigest()

if __name__ == '__main__':
    target_file = 'docker-compose.yml'
    
    with open('project-list.txt') as f:
        projects = f.read().splitlines()
    
    for project in projects:
        output_path = "output/" + project + "/"
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        repo = g.get_repo(project)
        
        release_count = repo.get_tags().totalCount
        print(repo.name + ": " + str(release_count) + " releases")
        
        file_sha = ''
        start_version = ''
        
        if release_count > 0:
            print("using tags")
            
            for tag in repo.get_tags():
                file = repo.get_contents(target_file, tag.name)

                if start_version == '':
                    start_version = tag.name
                    file_sha = file.sha
                    continue
                    
                if file_sha == file.sha:
                    continue
                
                # file_hash = get_remote_hash(file.download_url, "sha1")
                output_version_range = tag.name + "-" + start_version
                print_output(output_version_range, file_sha)
                download_file(file.download_url, output_path + output_version_range)
                
                start_version = tag.name
                file_sha = file.sha
                
            output_version_range = tag.name + "-" + start_version
            output_version_range = output_version_range.strip('-')
            print_output(output_version_range, file_sha)
            download_file(file.download_url, output_path + output_version_range)
            
        else:
            # work from commits instead of tags
            print("using commits")
            
            for commit in repo.get_commits():
                try:
                    file = repo.get_contents(target_file, commit.sha)
                except GithubException as exception:
                    if exception.status == 404:
                        continue
                
                if start_version == '':
                    start_version = commit.sha
                    file_sha = file.sha
                    continue
                    
                if file_sha == file.sha:
                    continue

                # file_hash = get_remote_hash(file.download_url, "sha1")
                output_version_range = commit.sha + "-" + str(start_version)
                print_output(output_version_range, file_sha)
                download_file(file.download_url, output_path + output_version_range)

                start_version = commit.sha
                file_sha = file.sha

            output_version_range = commit.sha + "-" + start_version
            output_version_range = output_version_range.strip('-')
            print_output(output_version_range, file_sha)
            download_file(file.download_url, output_path + output_version_range)
