#!/usr/bin/python
# -*- coding: utf-8 -*-

"Core exceptions raised by the PubSub module"

class PubSubError(Exception):
    pass

class InvalidErrorLevel(PubSubError):
    pass

class NoChannelError(PubSubError):
    pass
