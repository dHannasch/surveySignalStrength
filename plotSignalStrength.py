
from __future__ import print_function,division
import threading
import subprocess
import os
import sys
import time,datetime
import argparse
import re
import numpy
import fractions
import collections
#from numerical import makePlot

if sys.version_info < (3,0):
  input = raw_input

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class listOfMeasurements(list):
  def measureOnce(self):
    self.append(time.time() )
class ListsOfMeasurements(object):
  def __init__(self, location='location'):
    self.timestamps = list()
    self.bitRates = list()
    self.linkQualities = list()
    self.signalLevels = list()
    measurements = get_iwconfig()
    self.location = location
    self.essid = measurements.ESSID
    self.frequency = measurements.Frequency
    self.TXpower = measurements.TXpower
  def measureOnce(self):
    timestamp = time.time()
    measurements = get_iwconfig()
    if self.essid != measurements.ESSID:
      if measurements.ESSID == 'off/any':
        assert measurements.BitRate == 0
        assert measurements.LinkQuality == 0
        assert measurements.SignalLevel == -float('inf')
      else:
        raise RuntimeError(measurements.ESSID)
    else:
      assert self.frequency == measurements.Frequency
    assert self.TXpower == measurements.TXpower
    self.timestamps.append(timestamp)
    self.bitRates.append(measurements.BitRate)
    self.linkQualities.append(measurements.LinkQuality)
    self.signalLevels.append(measurements.SignalLevel)
  def plot(self):
    print(self.essid, ':', self.frequency, 'GHz', self.TXpower, 'dBm')
    #makePlot('Bit Rates', 'time', 'Bit Rate', [(self.timestamps, self.bitRates)])
    #makePlot('Link Qualities', 'time', 'Link Quality', [(self.timestamps, self.linkQualities)])
    #makePlot('Signal Levels', 'time', 'Signal Level', [(self.timestamps, self.signalLevels)])
  def recordSummary(self):
    self.linkQualities = numpy.array(self.linkQualities)
    self.signalLevels = numpy.array(self.signalLevels)
    linkDiffs = numpy.diff(self.linkQualities)
    levelDiffs = numpy.diff(self.signalLevels)
    assert linkDiffs.size == levelDiffs.size
    differencesSameSign = ( (linkDiffs > 0) == (levelDiffs > 0) ).sum()/linkDiffs.size
    print('when Link Quality and Signal Level change, they change in the same direction', differencesSameSign, 'of the time')
    #fracAbove67 = (self.signalLevels >= -67).sum()/self.signalLevels.size
    #fracAbove70 = (self.signalLevels >= -70).sum()/self.signalLevels.size
    #print(fracAbove67, 'above -67 dBm')
    #print(fracAbove70, 'above -70 dBm')
    fracBelow67 = (self.signalLevels < -67).sum()/self.signalLevels.size
    fracBelow70 = (self.signalLevels < -70).sum()/self.signalLevels.size
    print(fracBelow67, 'below -67 dBm')
    print(fracBelow70, 'below -70 dBm')
    startTime = datetime.datetime.fromtimestamp(int(self.timestamps[0]))
    #endTime = datetime.datetime.fromtimestamp(int(self.timestamps[-1]))
    with open(self.location + 'Summary.txt', 'a') as sumFile:
      print(startTime, '+', int(self.timestamps[-1] - self.timestamps[0]), 'seconds', fracBelow67, 'below -67 dBm,', fracBelow70, 'below -70 dBm', file=sumFile)
  def savetxt(self, filename):
    #self.timestamps = numpy.array(self.timestamps)
    #self.timestamps -= self.timestamps[0]
    with open(filename + 'Measurements.txt', 'w') as outfile:
      for l in (self.timestamps, self.bitRates, self.linkQualities, self.signalLevels):
        print(' '.join([str(t) for t in l]), file=outfile)
  def loadtxt(self, filename):
    with open(filename + '.txt', 'r') as infile:
      lines = infile.readlines()
      self.timestamps = numpy.fromstring(lines[0], sep=' ')
      self.bitRates = numpy.fromstring(lines[1], sep=' ')
      self.linkQualities = numpy.fromstring(lines[2], sep=' ')
      self.signalLevels = numpy.fromstring(lines[3], sep=' ')
# Configure the signal strength threshold to whatever signal strength you require, select your network, and walk the desired coverage area.
# If the blue line falls below the dotted line, you know you have a dead spot.

# of course this doesn't capture the whole picture: one room worked great until 11:40am, then stopped working entirely while still showing two bars
# but when it went back up to three bars (up to -60dBm from -78dBm), it started working again, so obviously something's connected to signal strength

"""
some phones may not update the bars on the screen very often. Weve seen in excess of 15 minutes without an update on the number of bars. What youre seeing, versus what is reality, can be two very different things, and that can make it difficult sometimes to use a handset as a measuring tool.
That means, if youve ever walked around with your phone held in the air like a divining rod, staring at those bars, willing them to jump, you may be wasting your time. It depends on what kind of phone you have.
"""

"""
Signal Quality Influences data throughput speeds
https://askubuntu.com/questions/521364/what-is-the-quality-of-a-wi-fi-access-point
I can understand what "signal level" means, it is RSSI (Received Signal Strength Indication).
https://hewlettpackard.github.io/wireless-tools/Linux.Wireless.Extensions.html
the first indicate how good the reception is (for example the percentage of correctly received packets) and the second how strong the signal is.
iwconfig's "Signal Quality" comes from /proc/net/wireless "link" under the "Quality" heading
"""

"""
wlan0     IEEE 802.11bgn  ESSID:"hhonors"  
          Mode:Managed  Frequency:2.462 GHz  Access Point: \w\w:\w\w:\w\w:\w\w:\w\w:\w\w   
          Bit Rate=18 Mb/s   Tx-Power=20 dBm   
          Retry  long limit:7   RTS thr=\d+ B   Fragment thr:off
          Power Management:off
          Link Quality=50/70  Signal level=-60 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:6   Missed beacon:0
"""
"""
wlan0     IEEE 802.11bgn  ESSID:off/any  
          Mode:Managed  Access Point: Not-Associated   Tx-Power=20 dBm   
          Retry  long limit:7   RTS thr=2347 B   Fragment thr:off
          Power Management:off
"""
# https://docs.python.org/3/library/re.html#simulating-scanf
# Bit Rate does vary, between 1 and 18 Mb/s
iwconfigRE = re.compile(r'''wlan0     IEEE 802.11bgn  ESSID:"(\w+)"  
          Mode:Managed  Frequency:(\d\.\d+) GHz  Access Point: \w\w:\w\w:\w\w:\w\w:\w\w:\w\w   
          Bit Rate=(\d+) Mb/s   Tx-Power=(\d+) dBm   
          Retry  long limit:\d   RTS thr=\d+ B   Fragment thr:off
          Power Management:off
          Link Quality=(\d+/\d+)  Signal level=([-+]?\d+) dBm  
          Rx invalid nwid:\d  Rx invalid crypt:\d  Rx invalid frag:\d
          Tx excessive retries:\d  Invalid misc:\d+   Missed beacon:\d
''')
iwconfigFailureRE = re.compile(r'''wlan0     IEEE 802.11bgn  ESSID:(off/any)  
          Mode:Managed  Access Point: Not-Associated   Tx-Power=(\d+) dBm   
          Retry  long limit:\d   RTS thr=\d+ B  Fragment thr:off
          Power Management:off
''')
iwconfigMeasurements = collections.namedtuple('iwconfigMeasurements', ['ESSID', 'Frequency', 'BitRate', 'TXpower', 'LinkQuality', 'SignalLevel'])
def get_iwconfig(interface='wlan0'):
  """
  could get this directly from /proc/net/wireless
  """
  iwconfig = subprocess.Popen(['iwconfig', interface], stdout=subprocess.PIPE)
  stdout,stderr = iwconfig.communicate()
  #print('iwconfig stdout =', stdout)
  matchObj = iwconfigRE.match(stdout)
  if matchObj is None:
    matchObj = iwconfigFailureRE.match(stdout)
    if matchObj is None:
      raise RuntimeError(stdout)
    essid = matchObj.group(1)
    frequency = 0
    bitRate = 0
    TXpower = int(matchObj.group(2) )
    linkQuality = 0
    signalLevel = -float('inf')
  essid = matchObj.group(1)
  frequency = float(matchObj.group(2) )
  #print("Frequency:{} GHz".format(frequency) )
  bitRate = int(matchObj.group(3) )
  #print("Bit Rate={} Mb/s".format(bitRate) )
  TXpower = int(matchObj.group(4) )
  #print("Tx-Power={} dBm".format(TXpower) )
  linkQuality = fractions.Fraction(matchObj.group(5) )
  #print("Link Quality={}".format(linkQuality) )
  signalLevel = int(matchObj.group(6) )
  #print("Signal level={} dBm".format(signalLevel) )
  return iwconfigMeasurements(essid, frequency, bitRate, TXpower, linkQuality, signalLevel)


def measure():
  nice = os.nice(32767)
  prev = None
  while nice != prev:
    prev = nice
    nice = os.nice(32767)
    print('nice =', nice)
  start = time.time()
  i = 0
  while time.time() < start + 1:
    i += 1
  print(i)
  # my computer can count about 4 million per second

# threading.Event.wait

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Display WLAN signal strength.')
  parser.add_argument('location', nargs='?', default='locationName',
                      help='name of the file where the data will be stored (usually the location you are testing)')
  parser.add_argument(dest='seconds', nargs='?', type=int, default=64,
                      help='seconds of time to measure')
  # even at 64seconds, low inter-measurement reliability:
  # 0.0157021085689 below -67 dBm
  # 0.00437415881561 below -70 dBm
  # about to sleep for 64 seconds
  # 0.0513392857143 below -67 dBm
  # 0.01953125 below -70 dBm

  parser.add_argument(dest='interface', nargs='?', default='wlan0',
                      help='wlan interface (default: wlan0)')
  args = parser.parse_args()
  #measure()
  get_iwconfig()
  #times = listOfMeasurements()
  measurements = ListsOfMeasurements(args.location)
  rt = RepeatedTimer(2**-15, measurements.measureOnce) # it auto-starts, no need of rt.start()
  try:
    #print('about to sleep for', args.seconds, 'seconds')
    #time.sleep(args.seconds) # your long-running job goes here...
    # https://stackoverflow.com/questions/983354/how-do-i-make-python-to-wait-for-a-pressed-key
    try:
      input("Press Enter to stop measuring...")
    except SyntaxError as E:
      if str(E) != 'unexpected EOF while parsing':
        raise
    except EOFError: pass
  finally:
    rt.stop() # better in a try/finally block to make sure the program ends!
  #measurements.savetxt(args.location)
  measurements.recordSummary()
  #measurements.plot()
  #times = numpy.array(times)
  #print(len(times) )
  #print(times - times[0])




