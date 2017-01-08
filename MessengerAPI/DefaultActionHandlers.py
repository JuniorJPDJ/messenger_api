from .Thread import GroupThread, Thread
from .Message import Message
from .Person import Person
from . import Actions


handlers = {}


def reg(action):
    def decor(handler):
        handlers[handler] = action
        return handler
    return decor


@reg(Actions.LogMessageAction)
def add_log_to_msg_history(action):
    assert isinstance(action, Actions.LogMessageAction)
    action.thread.messages.append(action)
    action.thread.message_count += 1
    action.thread.last_msg_time = action.time


@reg(Actions.ThreadParticipantLeaveAction)
def thread_leave(action):
    assert isinstance(action, Actions.ThreadParticipantLeaveAction)
    action.thread.participants.remove(action.author)


@reg(Actions.ThreadParticipantKickAction)
def thread_kick(action):
    assert isinstance(action, Actions.ThreadParticipantKickAction)
    for p in action.removed_participants:
        action.thread.participants.remove(p)


@reg(Actions.ThreadParticipantAddAction)
def thread_add(action):
    assert isinstance(action, Actions.ThreadParticipantAddAction)
    thread = action.thread
    assert isinstance(thread, GroupThread)
    for p in action.added_participants:
        thread.participants.append(p)


@reg(Actions.ThreadRenameAction)
def thread_rename(action):
    assert isinstance(action, Actions.ThreadRenameAction)
    thread = action.thread
    assert isinstance(thread, GroupThread)
    thread.name = action.name


@reg(Actions.ThreadImageChangeAction)
def thread_image_change(action):
    assert isinstance(action, Actions.ThreadImageChangeAction)
    action.thread.image = action.image.url


@reg(Actions.ThreadParticipantNicknameChangeAction)
def thread_nickname_change(action):
    assert isinstance(action, Actions.ThreadParticipantNicknameChangeAction)
    thread = action.thread
    assert isinstance(thread, Thread)
    participant = action.paticipant
    assert isinstance(participant, Person)
    thread.set_participant_name(participant, action.name)


@reg(Actions.ThreadEmoticonChangeAction)
def thread_emoji_change(action):
    assert isinstance(action, Actions.ThreadEmoticonChangeAction)
    action.thread.custom_emoji = action.emoticon


@reg(Actions.ThreadThemeColorChangeAction)
def thread_color_change(action):
    assert isinstance(action, Actions.ThreadThemeColorChangeAction)
    action.thread.custom_color = action.color


@reg(Message)
def message(action):
    assert isinstance(action, Message)
    action.thread.messages.append(action)
    action.thread.message_count += 1
    action.thread.last_msg_time = action.time


@reg(Actions.DeliveryAction)
def delivered(action):
    assert isinstance(action, Actions.DeliveryAction)
    action.thread.last_delivery = action.time


@reg(Actions.ReadAction)
def read(action):
    assert isinstance(action, Actions.ReadAction)
    action.thread.last_read[action.reader] = action.time


@reg(Actions.MakeReadAction)
def makeread(action):
    assert isinstance(action, Actions.MakeReadAction)
    action.thread.last_read_time = action.time


@reg(Actions.SetMuteAction)
def mute(action):
    assert isinstance(action, Actions.SetMuteAction)
    action.thread.mute = action.mute


@reg(Actions.BuddyListOverlayAction)
def person_activity(action):
    assert isinstance(action, Actions.BuddyListOverlayAction)
    action.person.last_active = action.last_active


def register_handlers(msg):
    for h in handlers:
        msg.register_action_handler(handlers[h], h)
