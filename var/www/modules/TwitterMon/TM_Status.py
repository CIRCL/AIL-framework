#!/usr/bin/env python3
# -*-coding:UTF-8 -*

#===========================================================================================================
# Author: Alfonso G. Alonso
# Twitter Monitor for AIL Framework
# For license information, see LICENSE.TXT
# ==========================================================================================================


# ========================================= TWEET MONITOR STATUS ===========================================
#
#
# Auxiliary file for TweetsImporter.py
#
# TODO: Bring classes here.
#
# ==========================================================================================================

status = "Not loaded"
statusDescription = "Not loaded"
currentorder = ""
processing = ""
progress = 0
lastLogProgress = 0
maxTweets = 0
realTimeMode = False
maxTimeBW = 600
currentSearch = ""
socket = None


# ========================================= TWEETS PROCESSING STATUS =======================================
#
#
#
#
# ==========================================================================================================

TweetsTooOld = False
maximumReached = False
results = None
resultsAux = None
refreshCursor = None
