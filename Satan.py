from mastodon import Mastodon, StreamListener
from bs4 import  BeautifulSoup
from multiprocessing import Pool
import os, random, re, json, re, sys, html

mastodon = Mastodon(
    access_token = 'mybot_usercred.secret',
    api_base_url = 'https://musain.cafe',
)

def extract_toot(toot):
    toot = toot.replace("&apos;", "'") #convert HTML stuff to normal stuff
    toot = toot.replace("&quot;", '"') #ditto
    soup = BeautifulSoup(toot, "html.parser")
    for lb in soup.select("br"): #replace <br> with linebreak
        lb.insert_after("\n")
        lb.decompose()
    for p in soup.select("p"): #ditto for <p>
        p.insert_after("\n")
        p.unwrap()
    for ht in soup.select("a.hashtag"): #make hashtags no longer links, just text
        ht.unwrap()
    text = soup.get_text()
    text = text.rstrip("\n") #remove trailing newline
    return text

def process_mention(mastodon, notification):
    acct = "@" + notification['account']['acct'] #get the account's @
    print("mention detected")
    post = notification['status']
    mention_text = extract_toot(post['content'])
    print(mention_text)
    # two modes: Whisper & Wish
    pattern1 = re.compile(r'悄悄话|悄悄話') # Whisper
    pattern2 = re.compile(r'许愿|許願') # Wish
    if pattern1.search(mention_text):
        print("Whisper!")
        mention_text_temp = mention_text.split('\n')
        mention_text_len = len(mention_text_temp)
        mention_text = mention_text_temp[(mention_text_len-4):]
        to_account_id = '@' + mention_text[0].split('：')[1]
        whisper_text = mention_text[1].split('：')[1]
        anonymous_if = mention_text[2].split('：')[1].lower() == ('否' or 'no')
        to_visibility = mention_text[3].split('：')[1]
        if anonymous_if:
            content = to_account_id + ' \n' + whisper_text + '\n 来自' + acct + ' '
        else:
            content = to_account_id + ' \n' + whisper_text
        mastodon.status_post(
            status = content, # the toot you'd like to send
            visibility = to_visibility 
        )
    elif pattern2.search(mention_text):
        print("Wish!")
        mention_text_temp = mention_text.split('\n')
        mention_text_len = len(mention_text_temp)
        mention_text = mention_text_temp[(mention_text_len-3):]
        wish_text = mention_text[0].split('：')[1]
        anonymous_if = mention_text[1].split('：')[1].lower() == ('否' or 'no')
        to_visibility = mention_text[2].split('：')[1]
        if anonymous_if:
            content = wish_text + '\n 来自 ' + acct + ' '
        else:
            content = wish_text
        mastodon.status_post(
            status = content, 
            visibility=to_visibility 
        )

def autotoot(mastodon, since_id):
    notifications = mastodon.notifications(since_id = since_id)
    if len(notifications) == 0:
        fo.write(since_id)
        return
    new_since_id = str(notifications[0]['id'])
    fo.write(new_since_id)
    for noti in notifications:
        if noti['type'] != 'mention':
            continue
        if str(noti['id']) != since_id:
            process_mention(mastodon, noti)
        else:
            return

fo = open("sinceid.txt", "r")
since_id = fo.readline()
since_id = int(since_id)
fo.close()
fo = open("sinceid.txt", "w+")
print(since_id)
autotoot(mastodon, since_id)
fo.close()
