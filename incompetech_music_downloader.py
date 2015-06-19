
import urllib.request as urlreq
import os
import yaml

url = 'http://incompetech.com/music/royalty-free/index.html?isrc=USUAN1500038&Search=Search'

def mm_ss_to_s(duration):
    """
    Duration in shape "[m]m:ss"
    Examples:
    0:12
    1:00
    12:21

    converts it to seconds.
    """
    d = list(map(int, duration.split(':')))
    s = d[0] * 60 + d[1]
    return s

def size_to_units(size):
    '''
    Copied from PlaylistDuration/upload.py on 7th June 2015.
    '''
    units = list(' kMGTP')
    for i in range(len(units)):
        if size < 1024:
            return '%s' % float('%.4g' % size) + ' ' + units[i] + 'B'
        size /= 1024
    return '%s' % float('%.4g' % size) + ' units_overload'

def units_to_size(units):
    stevilka, units = units.split()
    stevilka = float(stevilka)
    if 'k' in units: stevilka *= 1024
    if 'M' in units: stevilka *= 1024**2
    if 'G' in units: stevilka *= 1024**3
    if 'T' in units: stevilka *= 1024**4
    return stevilka

def get_mp3_from_url(url, folder, converse=True):
    """
    Results are saved in folder folder.
    folder must end with / or \\.
    Relative and absolute paths accepted
    """
    prefix = 'http://incompetech.com'
    split_by = '/music/royalty-free/mp3-royaltyfree/'
    middle = split_by
    try: webpage = urlreq.urlopen(prefix + url).read().decode('utf-8')
    except Exception as e:
        print(e, 'while doing', url)
        return -1
    splitted = webpage.split(split_by)[1]
    extracted = splitted.split('>')[0].strip('"')
    prettier_name = urlreq.unquote(extracted)
    mp3 = prefix + \
          middle + \
          extracted
    f = open(folder + prettier_name, 'wb')
    mp3 = urlreq.urlopen(mp3).read()
    f.write(mp3)
    f.close()
    size = os.stat(folder + prettier_name).st_size
    if converse: print('Downloaded', prettier_name, '\twith size of', size_to_units(size), '.')
    return size

def get_all_songs():
    list_url = "http://incompetech.com/music/royalty-free/isrc_to_name.php"
    parsed = urlreq.urlopen(list_url).read().decode('utf-8')
    parsed = parsed.split('Inactive Pieces')[0]
    parsed = parsed.split('ISRC Code to Track Name Lookup')[2]
    parsed = parsed.split('ISRC')[1:]
    print(len(parsed))
    IDs = []
    names = []
    urls = []
    for i in parsed:
        tmp = i
        tmp = tmp.split('HREF=')[1].split('>')
        url = tmp[0].strip('"')
        ID = tmp[1].split('<')[0].strip()
        name = tmp[2].split('<')[0].strip().strip('-').strip()
        IDs += [ID]
        urls += [url]
        names += [name]
    return urls, IDs, names

def download_all_songs(folder):
    already_have_data = 'what_I_have.yaml'
    urls, IDs, names = get_all_songs()
    f = open(already_have_data, 'r')
    already_have = yaml.load(f.read())
    f.close()
    if already_have is None: 
        already_have = dict()
    IDset = set()
    for url, ID, name in zip(urls, IDs, names):
        if ID in IDset:
            print(ID, 'already in IDset')
        IDset.add(ID)
        if ID in already_have:
            # This (next) if adds additional data
            # to previously downloaded songs.
            if 'Instruments' not in already_have[ID]:
                additional = get_additional_details(url)
                for i, j in additional.items():
                    already_have[ID][i] = j
                f = open(already_have_data, 'w')
                f.write(yaml.dump(already_have, default_flow_style=False))
                f.close()
                print('Added data to', already_have[ID]['name'])
            
            continue
        
        size = get_mp3_from_url(url, folder)
        if size < 0:
            print("Couldn't download", url, ID, name, '.')
            print('Probably because non utf-8 characters.')
            continue
        size = size_to_units(size)
        already_have[ID] = dict(
            size= size,
            URL= url,
            name= name)
        additional = get_additional_details(url)
        for i, j in additional.items():
            already_have[ID][i] = j        
        f = open(already_have_data, 'w')
        f.write(yaml.dump(already_have, default_flow_style=False))
        f.close()

def sum_of_size():
    already_have_data = 'what_I_have.yaml'
    f = open(already_have_data, 'r')
    a = yaml.load(f.read())
    f.close()
    s = 0
    for i, j in a.items():
        if 'kB' in j['size']: continue
        s += units_to_size(j['size'])
    return size_to_units(s), len(a)


def get_additional_details(url, converse=True):
    """
    """
    prefix = 'http://incompetech.com'
#    split_by = '/music/royalty-free/mp3-royaltyfree/'
#    middle = split_by
    try: webpage = urlreq.urlopen(prefix + url).read().decode('utf-8')
    except Exception as e:
        print(e, 'while doing', url)
        return -1
    splitted = webpage.split('musictitle')
    if len(splitted) != 2:
        print('When getting additional details, I encounterd a problem. len(splitted) =', len(splitted), 'but should be 2')
    splitted = splitted[1].split('btn btn-success btn-small')[0]
    #print(splitted)
    podatki = dict()
    try:
        podatki['Genre'] = splitted.split('Genre:')[1].split('<')[1].split('>')[1].strip()
        if 'Collection' in splitted:
            podatki['Collection'] = splitted.split('Collection:')[1].split('<')[1].split('>')[1].strip()
        podatki['Duration'] = splitted.split('Time:')[1].split('<')[1].split('>')[1].strip()
        podatki['Duration_seconds'] = mm_ss_to_s(podatki['Duration'])
        podatki['BPM'] = splitted.split('Time:')[1].split('BPM')[0].split('>')[2].strip()
        if 'Instruments' in splitted:
            podatki['Instruments'] = \
                splitted.split('Instruments:')[1].split('<')[0].strip().split(', ')
        else:
            podatki['Instruments'] = []
    except Exception as e:
        print(e)
        print(url)
        print(1/0)
    return podatki

def filter(pogoj):
    f = open('what_I_have.yaml', 'r')
    seznam = yaml.load(f.read())
    f.close()

    for i in seznam:
        if pogoj(seznam[i]):
            print(seznam[i]['name'])

def voice(item):
    return 'Voice' in item['Instruments']

filter(voice)

if 0:
    print(sum_of_size())
    print(get_additional_details("/music/royalty-free/index.html?isrc=USUAN1500039&Search=Search"))

if __name__ == '__main__' and 0:
    f = open('foldername.yaml')
    foldername = yaml.load(f.read())['foldername']
    f.close()
    download_all_songs(foldername)

if False:
    url = 'http://incompetech.com/music/royalty-free/index.html?isrc=USUAN1500013&Search=Search'
    a = urlreq.urlopen(url)
    a = a.read()
    print(a)
    print(len(a))
    prev = 'initial'
    for i in range(0, len(a), 10):
        try:
            tmp = a[i:i+10].decode('utf-16')
            print(tmp)
        except Exception as e:
            print(e)
            print(prev)
        prev = tmp

"""
When multiple musics have the same ID everything is fucked up.
Multple mp3s are on the same page.
Multiple song details are on the same page.
...
"""