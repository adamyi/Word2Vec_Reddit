from __future__ import print_function
 
import logging
import os.path
import six
import sys
import re
import datetime
import io
import json
from math import log

# Build a cost dictionary, assuming Zipf's law and cost = -math.log(probability).
words = open("enwiki_vocab_min200.txt").read().split()
wordcost = dict((k, log((i+1)*log(len(words)))) for i,k in enumerate(words))
maxword = max(len(x) for x in words)

def import_comments_from_file(file_path, output, logger):
        f = io.open(file_path, 'r', encoding="utf8")
        logger.info("Begin scanning %s" % file_path)

        counter = 0
        while True:
                current_line = f.readline()
                if not current_line:
                    break
        
                current_json_obj = json.loads(current_line)
                body = current_json_obj["body"]

                try:
                    parse_message(body, output)

                except Exception as e:
                    logger.error(e)
                    raise e
                counter += 1
                if counter % 10000 == 0:
                    logger.info("scanned %d messages from %s" % (counter, file_path))
        logger.info("Finished scanning %d messages from %s" % (counter, file_path))

def parse_message(text, output):
    if (text == "[deleted]" or text == "[removed]"):
        return
    text = remove_urls(text)
    text = remove_tags(text)
    text = remove_none_english_characters(text)
    text = remove_extra_spaces(text)
    text = text.lower()
    output.write(text + "\n")


def infer_spaces(s):
    """Uses dynamic programming to infer the location of spaces in a string
    without spaces."""

    # Find the best match for the i first characters, assuming cost has
    # been built for the i-1 first characters.
    # Returns a pair (match_cost, match_length).
    def best_match(i):
        candidates = enumerate(reversed(cost[max(0, i-maxword):i]))
        return min((c + wordcost.get(s[i-k-1:i], 9e999), k+1) for k,c in candidates)

    # Build the cost array.
    cost = [0]
    for i in range(1,len(s)+1):
        c,k = best_match(i)
        cost.append(c)

    # Backtrack to recover the minimal-cost string.
    out = []
    i = len(s)
    while i>0:
        c,k = best_match(i)
        assert c == cost[i]
        out.append(s[i-k:i])
        i -= k

    return " ".join(reversed(out))

tag_href = re.compile('\[(.*)\]\(https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\)')
tag_url = re.compile('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
def remove_urls(string):
    removed = re.sub(tag_href, r'\1', string)
    removed = re.sub(tag_url, '', removed)
    return removed

tag_regex = re.compile('<.*?>')
def remove_tags(string):
    removed = re.sub(tag_regex, '', string)
    return removed

non_english_regex = re.compile('[^A-Za-z]')
def remove_none_english_characters(string):
    string = string.replace("&lt", "")
    string = string.replace("&gt", "")
    
    return " ".join(non_english_regex.split(string))

def remove_extra_spaces(string):
    return re.sub(' +',' ',string)

if __name__ == '__main__':
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))

    # check and process input arguments
    if len(sys.argv) != 2:
        print("Using: python process_reddit_corpus.py reddit_corpus.en")
        sys.exit(1)

    output = open(sys.argv[1], 'w')

    for i in range(1, 30):
        import_comments_from_file("../reddit_data/RC_2017-12-%s" % str(i).zfill(2), output, logger)

    output.close()
