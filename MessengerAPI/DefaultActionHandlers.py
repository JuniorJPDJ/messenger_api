from .Thread import GroupThread, Thread
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


#@reg(Actions.ThreadImageChangeAction) TODO


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


@reg(Actions.Message)
def message(action):
    assert isinstance(action, Actions.Message)
    action.thread.messages.append(action)
    action.thread.message_count += 1
    action.thread.last_msg_time = action.time


#@reg(Actions.DeliveryAction) TODO


#@reg(Actions.ReadAction) TODO


#@reg(Actions.MakeReadAction) TODO


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
