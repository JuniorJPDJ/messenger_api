import logging
import argparse

from messenger_api.Messenger import Messenger
from messenger_api import Actions


logging.basicConfig(level=logging.DEBUG)

p = argparse.ArgumentParser()
p.add_argument('email', help="E-Mail/Phone number/Other facebook login")
p.add_argument('password', help="Facebook password")
args = p.parse_args()

msg = Messenger(args.email, args.password)

log = []
idkwtf = []

wtfactions = [Actions.Action, Actions.MessagingAction, Actions.MercuryAction, Actions.LogMessageAction,
              Actions.GenericAdminTextAction, Actions.DeltaAction]


def handle_action(action):
    log.append(action)
    if action.__class__ in wtfactions:
        idkwtf.append(action)
        logging.warning('Unknown action')
    logging.info('[{}] {}'.format(log.index(action), action))


msg._pparser.register_actions_handler(handle_action)


while 1:
    msg._pparser.make_pull()
