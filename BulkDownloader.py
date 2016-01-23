# Akademik HME Bulk Downloader
# Written by Rosmianto Aji Saputro
# First written 18/01/2016
# Last updated 23/01/2016

# HME Bulk Downloader is written to specifically download a folder at once at akademikhme.ee.itb.ac.id:8080
# This tool is intended to solve "file too big" problem when downloading
# the folder as a zip file.

# Import required libraries.
from urllib.parse import quote
from clint.textui import progress
import urllib.request
import collections
import requests
import html
import sys
import re
import os

# ---------------------------------------------
# fetch_list(url)
# Retrieve list of current folder content.
# return:		hierarchy	= Hierarchy object.
# parameter:	_url		= URL to be parsed.
# ---------------------------------------------
def fetch_list(_url):
	_hierarchy = {};
	_content = urllib.request.urlopen(_url).read();
	
	# Fetch URL's folder name
	_m = re.search(r'(?<=\<h2 id\=\"view\-hd\"\>)(?P<folder>.*)(?=</h2>)', str(_content), re.I | re.S);
	yield Hierarchy(_m.group('folder'), 'Current dir', _url, '');
	if _m:
		for _m in re.finditer(r'(\.png\" alt\=\")(?P<type>.*?)(\" \/\>\<\/td\>)(.*?)href\=\"(?P<link>.*?)(\"\>)(?P<title>.*?)(\<\/a\>)(.*?)href\=\"(?P<download>.*?)(\"\>)', str(_content), re.S | re.I | re.S):
			yield Hierarchy(html.unescape(_m.group('title')), _m.group('type'), _m.group('link'), quote(html.unescape(_m.group('download')), safe='?=&/'));
	return

# ---------------------------------------------
# fetch_size(url)
# Retrieve size of current url.
# return:		size			= Size object.
# parameter:	Hierarchy		= Hierarchy object.
# ---------------------------------------------
def fetch_size(_hierarchy):
	totalSize = 0;
	totalFile = 0;
	for list in _hierarchy:
		print('wait...');
		if(list.type == 'Directory icon'):
			dirList = fetch_list(host + list.link);
			dirSize = fetch_size(dirList);
			totalSize += dirSize.total_size;
			totalFile += dirSize.file_count;
		elif(list.type == 'File'):
			resp = requests.head(host + list.download);
			resp = requests.head(resp.headers['Location']);
			totalSize += int(resp.headers['Content-Length']);
			totalFile += 1;
	return Size(totalFile, totalSize);

# ---------------------------------------------
# download_dir(_hierarchy)
# Download the entire content of hierarchy.
# return:		Size			= Size object.
# parameter:	Hierarchy		= Hierarchy object.
# ---------------------------------------------
def download_dir(_hierarchy):
	DownloadedSize = 0;
	DownloadedFile = 0;
	print('Downloading contents...');
	for list in _hierarchy:
		# sys.stdout.write('.');
		print(list.type, list.title);
		if(list.type == 'Current dir'):
			if not os.path.exists(list.title):
				os.makedirs(list.title);
			os.chdir(list.title);
		elif(list.type == 'Directory icon'):
			if not os.path.exists(list.title):
				getDir = download_dir(fetch_list(host + list.link));
				DownloadedFile += getDir.file_count;
				os.chdir('..');
		elif(list.type == 'File'):
			DownloadedFile += 1;
			print(DownloadedFile, '.');
			resp = requests.head(host + list.download);
			r = requests.get(resp.headers['location'], stream=True)
			with open(list.title, 'wb') as f:
				total_length = int(r.headers.get('content-length'));
				for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
					if chunk:
						f.write(chunk);
						f.flush();
	return Size(DownloadedFile, DownloadedSize);
	

# Namedtuple declaration.
Hierarchy = collections.namedtuple('Hierarchy',['title','type','link','download']);
Size = collections.namedtuple('Size',['file_count','total_size']);
host = r'http://akademikhme.ee.itb.ac.id:8000';

url = input("Please input an URL:\n");
print("Loading...");

folderFileList = fetch_list(url);
print('Retrieving directory size...');
folderSize = fetch_size(folderFileList);
print(folderSize.file_count, 'file(s) (', folderSize.total_size / 1024, 'KB)');

answer = input('Do you want to download its content? (y/n) ');
if(answer == 'y'):
	result = download_dir(fetch_list(url));
	print(result.file_count, 'files have been downloaded.');
else:
	exit();
# for list in folderFileList:
	# print(list.type, '\t', list.title);
