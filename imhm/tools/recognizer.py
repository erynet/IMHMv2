# -*- coding:utf-8 -*-
import Queue

__author__ = 'ery'

from gcm import GCM
import sys
import os
import MySQLdb
import base64
import random, string
import numpy as np
from pydub import AudioSegment
from pydub.utils import audioop
# from .strcat import StrCat
from itertools import izip_longest

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (generate_binary_structure,
                                      iterate_structure, binary_erosion)
import hashlib
from operator import itemgetter

from MySQLdb.cursors import DictCursor


IDX_FREQ_I = 0
IDX_TIME_J = 1
DEFAULT_FS = 22050
DEFAULT_WINDOW_SIZE = 4096
DEFAULT_OVERLAP_RATIO = 0.015625 # 0.03125
DEFAULT_FAN_VALUE = 15
DEFAULT_AMP_MIN = 10
PEAK_NEIGHBORHOOD_SIZE = 20
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200
PEAK_SORT = True
FINGERPRINT_REDUCTION = 20


connection_string =\
    {
        "Common":
            {
                "unix_socket": "/var/run/mysqld/mysqld.sock",
                "user": "root",
                "passwd": "1423",
                "db": "IMHM",
                "use_unicode": True,
                "charset": "utf8"
            },
    }


def get_continued_pcm(session_idx):
    conn = MySQLdb.connect(**connection_string["Common"])
    cur = conn.cursor()

    s = StrCat()
    cur.execute("""SELECT `data` FROM `IMHM`.`search_packet` WHERE `session_idx` = %s ORDER BY `sequence` ASC""", (session_idx,))
    with s:
        for row in cur.fetchall():
            s.append(base64.b64decode(row[0]))
        return s.__str__()[5000:]


def fingerprint(channel_samples, Fs=DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO,
                fan_value=DEFAULT_FAN_VALUE,
                amp_min=DEFAULT_AMP_MIN):

    # print str(channel_samples)
    # print int(wsize * wratio)

    arr2D = mlab.specgram(
        channel_samples,
        NFFT=wsize,
        Fs=Fs,
        window=mlab.window_hanning,
        noverlap=int(wsize * wratio))[0]

    arr2D = 10 * np.log10(arr2D)
    arr2D[arr2D == -np.inf] = 0  # replace infs with zeros

    # find local maxima
    local_maxima = get_2D_peaks(arr2D, plot=False, amp_min=amp_min)

    # return hashes
    return generate_hashes(local_maxima, fan_value=fan_value)


def get_2D_peaks(arr2D, plot=False, amp_min=DEFAULT_AMP_MIN):
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)

    local_max = maximum_filter(arr2D, footprint=neighborhood) == arr2D
    background = (arr2D == 0)
    eroded_background = binary_erosion(background, structure=neighborhood,
                                       border_value=1)

    detected_peaks = local_max - eroded_background

    amps = arr2D[detected_peaks]
    j, i = np.where(detected_peaks)

    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > amp_min]  # freq, time, amp

    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    if plot:
        # scatter of the peaks
        fig, ax = plt.subplots()
        ax.imshow(arr2D)
        ax.scatter(time_idx, frequency_idx)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return zip(frequency_idx, time_idx)


def generate_hashes(peaks, fan_value=DEFAULT_FAN_VALUE):
    """
    Hash list structure:
       sha1_hash[0:20]    time_offset
    [(e05b341a9b77a51fd26, 32), ... ]
    """
    if PEAK_SORT:
        peaks.sort(key=itemgetter(1))

    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if (i + j) < len(peaks):

                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]
                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]
                t_delta = t2 - t1

                if t_delta >= MIN_HASH_TIME_DELTA and t_delta <= MAX_HASH_TIME_DELTA:
                    h = hashlib.sha1(
                        "%s|%s|%s" % (str(freq1), str(freq2), str(t_delta)))
                    yield (h.hexdigest()[0:FINGERPRINT_REDUCTION], t1)


def find_matches(samples, Fs=DEFAULT_FS):
    hashes = fingerprint(samples, Fs=Fs)
    return return_matches(hashes)


SELECT_MULTIPLE = """SELECT HEX(`hash`), `idx`, `offset` FROM `fingerprints` WHERE `hash` IN (%s);"""


def return_matches(hashes):
    """
    Return the (song_id, offset_diff) tuples associated with
    a list of (sha1, sample_offset) values.
    """
    # Create a dictionary of hash => offset pairs for later lookups
    mapper = {}
    for hash, offset in hashes:
        mapper[hash.upper()] = offset

    # Get an iteratable of all the hashes we need
    values = mapper.keys()

    conn = MySQLdb.connect(**connection_string["Common"])
    cur = conn.cursor()

    for split_values in grouper(values, 1000):
        # Create our IN part of the query
        query = SELECT_MULTIPLE
        query %= ', '.join(['UNHEX(%s)'] * len(split_values))

        cur.execute(query, split_values)

        for hash, sid, offset in cur:
            # (sid, db_offset - song_sampled_offset)
            yield (sid, offset - mapper[hash])


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return (filter(None, values) for values
            in izip_longest(fillvalue=fillvalue, *args))


def cursor_factory(**factory_options):
    def cursor(**options):
        options.update(factory_options)
        return Cursor(**options)
    return cursor


SELECT_SONG = """SELECT `music`.`idx`, `music`.`title`, COUNT(fingerprints.idx) AS `total_hash_count` FROM `music` INNER JOIN `fingerprints` ON (`music`.`idx` = `fingerprints`.`idx`) WHERE `music`.`idx` = %s;"""


def get_song_by_id(sid):
    conn = MySQLdb.connect(**connection_string["Common"])
    cur = conn.cursor()
    # cur = Cursor(cursor_type=DictCursor)
    cur.execute(SELECT_SONG, (sid,))
    return cur.fetchone()


def align_matches(matches):
    """
        Finds hash matches that align in time with other matches and finds
        consensus about which hashes are "true" signal from the audio.

        Returns a dictionary with match information.
    """
    # align by diffs
    diff_counter = {}
    largest = 0
    largest_count = 0
    song_id = -1
    for tup in matches:
        sid, diff = tup
        if diff not in diff_counter:
            diff_counter[diff] = {}
        if sid not in diff_counter[diff]:
            diff_counter[diff][sid] = 0
        diff_counter[diff][sid] += 1

        if diff_counter[diff][sid] > largest_count:
            largest = diff
            largest_count = diff_counter[diff][sid]
            song_id = sid

    # extract idenfication
    song = get_song_by_id(song_id)
    # if song:
    #     # TODO: Clarify what `get_song_by_id` should return.
    #     songname = song.get("title", None)
    # else:
    #     return None

    # return match info
    nseconds = round(float(largest) / DEFAULT_FS *
                     DEFAULT_WINDOW_SIZE *
                     DEFAULT_OVERLAP_RATIO, 5)
    song_info = {
        "idx": song[0],
        # "title": song[1],
        "confidence": largest_count,
        "total_hash_count": song[2],
        "offset": int(largest),
        "offset_seconds": nseconds,
        }
    return song_info


def recognize(pcm):
    # rand_filename = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    # full_path = "/imhm/imhm/tmp/" + rand_filename
    # fp = open(full_path, "wb")
    # fp.write(pcm)
    # fp.close()
    #
    # au = AudioSegment.from

    from struct import pack, unpack
    s2 = unpack(">{}h".format(pcm.__len__() / 2), pcm)
    s3 = pack("<{}h".format(s2.__len__()), *s2)

    nums = np.fromstring(s3, np.int16)

    # fp = open("/imhm/dejavu/pcm/input/in.pcm", "wb")
    # for d in nums:
    #     fp.write(d)
    # fp.close()

    matches = []
    #for d in nums:
    matches.extend(find_matches(nums))
    return align_matches(matches)


class Cursor(object):
    """
    Establishes a connection to the database and returns an open cursor.


    ```python
    # Use as context manager
    with Cursor() as cur:
        cur.execute(query)
    ```
    """
    _cache = Queue.Queue(maxsize=5)

    def __init__(self, cursor_type=MySQLdb.cursors.Cursor, **options):
        super(Cursor, self).__init__()

        try:
            conn = self._cache.get_nowait()
        except Queue.Empty:
            conn = MySQLdb.connect(**options)
        else:
            # Ping the connection before using it from the cache.
            conn.ping(True)

        self.conn = conn
        self.conn.autocommit(False)
        self.cursor_type = cursor_type

    @classmethod
    def clear_cache(cls):
        cls._cache = Queue.Queue(maxsize=5)

    def __enter__(self):
        self.cursor = self.conn.cursor(self.cursor_type)
        return self.cursor

    def __exit__(self, extype, exvalue, traceback):
        # if we had a MySQL related error we try to rollback the cursor.
        if extype is MySQLdb.MySQLError:
            self.cursor.rollback()

        self.cursor.close()
        self.conn.commit()

        # Put it back on the queue
        try:
            self._cache.put_nowait(self.conn)
        except Queue.Full:
            self.conn.close()


class StrCat(object):
    def __init__(self, seed = None):
        from cStringIO import StringIO
        self._str = StringIO()
        if seed:
            assert isinstance(seed, str)
            self._str.write(seed)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._str.close()

    def __str__(self):
        return self._str.getvalue()

    def __unicode__(self):
        return unicode(self._str.getvalue(), "utf8")

    def append(self, token):
        assert isinstance(token, str)
        self._str.write(token)


import urllib2
import json


def sendgcm(uuid, idx, status):
    url = "https://android.googleapis.com/gcm/send"
    apikey = "AIzaSyBJ8Nf5v1z6baoGrtg97b6O4JJZDGZEUI0"
    mykey = "key=" + apikey
    header = {'Content-Type': 'application/json', 'Authorization': mykey}
    data = {}
    data['registration_ids'] = uuid # ("ferbqpz45L8:APA91bG79mQTmR3NqNP18n3ZTzk9YSTDnsT8ouMr2zaqGBKHb5Fu1U0irUP437Pa-Gv-43MGhLH45PZTZuJewNoyryTS1VN_aCAiBEZfg-raiq7_xqkhvXXVswjZfQY7kJiOOLMd24ys",)
    data['data'] = {"status" : str(status), "idx" : str(idx)}
    json_dump = json.dumps(data)
    req = urllib2.Request(url, json_dump, header)
    result = urllib2.urlopen(req).read()
    return result


if __name__ == "__main__":
    if sys.argv.__len__() < 3:
        sys.exit()

    session_idx = int(sys.argv[1])
    pcm = get_continued_pcm(session_idx)
    result = recognize(pcm)
    # for key in result:
    #     print "{0} : {1}".format(key, result[key])

    # g = GCM("AIzaSyBJ8Nf5v1z6baoGrtg97b6O4JJZDGZEUI0")

    conn = MySQLdb.connect(**connection_string["Common"])
    cur = conn.cursor()

    cur.execute("""SELECT `user_idx` FROM `IMHM`.`search_session` WHERE `idx` = %s;""", (session_idx,))
    uidx = cur.fetchone()[0]
    cur.execute("""SELECT `uuid` FROM `IMHM`.`user` WHERE `idx` = %s""", (uidx,))
    uuid = cur.fetchone()[0]

    print "AX : {0}, {1}".format(result["idx"], result["confidence"])

    if int(sys.argv[2]) == 0:
        # print "AY"
        # pending
        if result["confidence"] >= 7:
            # print result["confidence"]
            # print "AA"
            sendgcm((uuid,), result["idx"], True)
    elif int(sys.argv[2]) == 1:
        print "AZ"
        # end
        if result["confidence"] >= 5:
            # print result["confidence"]
            # print "AB"
            sendgcm((uuid,), result["idx"], True)
        else:
            # print result["confidence"]
            # print "AC"
            sendgcm((uuid,), 0, False)


    #import time
    #time.sleep(5)
    # import json

    # t = {"status": True, "idx": result["idx"]}
    #
    # _data = unicode(json.dumps(t))
    # g.json_request(registration_ids=uuid, data=t)



