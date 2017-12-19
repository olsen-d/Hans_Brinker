#email: derek.olsen@colorado.edu
#file: hans_brinker.py
#purpose: Identify a leaky bucket
#version: 1.0.3

#!/usr/bin/python3

import argparse
import bs4
import re
import requests

parser = argparse.ArgumentParser(description = 'A small leak can sink a great ship')
parser.add_argument("fileName",  help="Please provide file to write to" , action = "store", default = False)
parser.add_argument("-t", "--ticker", help="Ticker for target company" ,action = "store", default = False)
parser.add_argument("-a", "--analysis_flag",choices=['S', 'C'] , help="Analyze target company suppliers 'S' or customers 'C'" ,action = "store", default = False)
parser.add_argument("-f", "--folderNames_flag",choices=['Y'] , help="Include top folder names" ,action = "store", default = False)
parser.add_argument("-d", "--delimiter", default="", help="Indicates how to seperate strings (Default = '-')." , action = "store")
parser.add_argument("-n", "--limit",type=int, default=1000, help="Limits bucket requests" , action = "store")
parser.add_argument("-v","--version", action="version", version='%(prog)s 1.0')
args = parser.parse_args()
fileName = args.fileName
ticker = args.ticker
analysis_flag = args.analysis_flag
folderNames_flag= args.folderNames_flag
delimiter = args.delimiter
limit = args.limit


def info_gather(ticker, analysis_flag):
  tickers = []
  if analysis_flag == 'S':
    url = "https://csimarket.com/stocks/competition2.php?supply&code=%s" % (ticker)
  else:
    url = "https://csimarket.com/stocks/competitionNO2.php?markets&code=%s" % (ticker)
  r = requests.get(url)
  html = r.text
  soup = bs4.BeautifulSoup(html, "lxml")
  js_test = soup.find_all("a")
  for line in js_test:
    tix_link = (line.get('href'))
    if analysis_flag == 'S':
      if "Profitability.php?code=" in tix_link:
        tix = tix_link.strip("Profitability.php?code=")
        tickers.append(tix)
    else:
      if "technicals_ohlc.php?code=" in tix_link:
        tix = tix_link.strip("technicals_ohlc.php?code=")
        tickers.append(tix)
  return(tickers)
info_gather(ticker, analysis_flag)


def bucketName_gen(folderNames_flag, delimiter):
  folderNames = ['production', 'prod', 'user', 'staff', 'test', 'Q1', 'Q2', 'Q3', 'Q4','media','imag', 'image', '2010', '2011', '2012', '2013', '2014', '2015', 'corp','corporate', 'public', 'private', 'client', 'patient', 'clients', 'patients','home', 'root', 'admin', 'administrator', 'admins', 'administrators','credentials', 'dev', 'backup', 'back_up', 'sys32', 'pics', 'pix', 'pictures','files', 'conf_files', 'confidential', 'confidential_files', 'do_not_share','team', 'reports', 'index', 'www', 'com', 'delete', 'finance', 'hr','human_resources', 'resources', 'private', 'public', 'data', 'info', 'information','lists', 'exec', 'executive', 'team', 'project', 'proposal']
  n_folders = len(folderNames)
  tickers = info_gather(ticker, analysis_flag)
  n_tickers = len(tickers)
  bucketNames = []
  for i in range(0, n_tickers):
    prefix = tickers[i] + delimiter
    for i in range(0, n_folders):
      bucketName = prefix + folderNames[i]
      bucketNames.append(bucketName)
  return(bucketNames)
bucketName_gen(folderNames_flag, delimiter)

def url_builder(folderNames_flag, limit):
  l = int(limit)
  bucket_keys = []
  public_buckets = []
  private_buckets = []
  redirect_buckets = []
  tickers = info_gather(ticker, analysis_flag)
  bucketNames = bucketName_gen(folderNames_flag, delimiter)

  if folderNames_flag == 'Y':
    bucket_keys = bucketNames
  else:
    bucket_keys = tickers

  n_buckets = len(bucket_keys)
  if l < n_buckets:
    bucket_keys = bucket_keys[0:l]

  for bucket in bucket_keys:
    bucket = str(bucket).lower()
    base1_url = "https://%s.s3.amazonaws.com" % (bucket)
    r = requests.get(base1_url)
    r_code = str(r.status_code)
    print(r_code +" : "+base1_url)

    if r_code == '200':
      result = "200-PUBLIC: "+base1_url
      public_buckets.append(result)
    if r_code == '403':
      result = "<403-PRIVATE: "+base1_url
      private_buckets.append(result)
    if r_code == '301':
      reg_redirs = re.compile(r'<Endpoint>.+</Endpoint>')
      r_html = r.text
      endpoint = (re.findall(reg_redirs, r_html))
      new_url = endpoint[0].strip("<Endpoint>" "</Endpoint>")
      result = "<301-REDIRECT: "+base1_url+" --> "+new_url
      redirect_buckets.append(result)
  bucket_results =  public_buckets + private_buckets + redirect_buckets
  return(bucket_results)
url_builder(folderNames_flag, limit)

def write_out_pub(fileName):
  bucket_results = url_builder(folderNames_flag, limit)
  with open(fileName, "w") as out:
    for line in bucket_results:
      out.write(line + "\n")
  out.close()
write_out_pub(fileName)

