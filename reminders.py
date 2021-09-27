import smartlog;
import toolbelt;
import configparser;
import butterfly;
import subprocess;
import time;
import os;
import sys;
import queue;
import notebook;
import clientele;
from plyer import notification

QuickDate = toolbelt.quickdate.QuickDate;
log = smartlog.Smartlog();

db     = clientele.client.Clientele();
book   = notebook.notes.Notebook();
todo   = book.todo;
remi   = book.reminder;
client = db.client;

import os



# Somehow we need to deal with firefox afterward
def do_texts(texts):
    gvoice = butterfly.gvoice.GoogleVoiceAgent();
    for text in texts:
        phone, message = text;
        gvoice.text(phone, message);


def do_client(rem):
    query = "select email,phone,skype from client where user='%s'" 
    data  = client.query(query % rem['who']);
    if not data: return None;
    else: return list(data)[0];


def do_notify(rem):
    if rem['how']=='desktop':
         notification.notify(rem['about'], rem['what'], timeout=7200);
         playsound('/home/dominic/.smartlog/info.wav')
         return [];
    data = do_client(rem);
    if not data: return [];
    if rem['how']=='email':
             g = butterfly.gmail.GMailAgent();
             g.send_message({
                 'from'    : 'the.dominicator@gmail.com',
                 'to'      : data['email'],
                 'subject' : rem['about'],
                 'body'    : rem['what'],
             });
    elif rem['how']=='text':
         return [(data['phone'], rem['what'])];
    elif rem['how']=='skype':
         sk = butterfly.skype.SkypeAgent();
         sk.send_message({
            'id'   : data['skype'],
            'msg'  : rem['what'],
         });
    return [];



def quickdates():
    now   = QuickDate('now');
    day   = QuickDate('tomorrow');
    soon  = QuickDate('11 minutes');
    return (now, day, soon);
    

def update_next(rem, withwhat):
    if rem['often'] != 'once':
       remi.update({
            'id'   : rem['id'],
            'next' : withwhat,
       });


def update_reminders(args):
    data  = remi.query("select who,how,time,often,about,what,next from reminder where next >= NOW()");
    data = list(data);
    rems  = []
    texts = []
    j = 0;
    (now, day, soon) = quickdates();
    for i in range(len(data)):
        t = QuickDate(data[i]['time']);
        n = QuickDate();
        n.setbydt(data[i]['next']);
        if n > now and n < day:
           rems += [data[i]];
           if n < soon: 
              update_next(rems[j], t.lex);
              texts += do_notify(rems[j]);
           j = j + 1;
    if texts: do_texts(texts);
    args['queue'].put({
       'reminders' : sorted(rems, 
       key=lambda x: x['next'])
    }); 
    return args;



def print_reminders(args):
    r = "{:<10} {:<10} {:<10} {:<20} {:<20} {:<40}\n".format(
      'who', 'how', 'about', 'time', 'next', 'what',
    )
    log.write(log.incolor('purple', r));
    x = len(args['reminders']);
    x = 5 if x>5 else x;
    for i in range(x):
        reminder = args['reminders'][i];
        r = "{:<10} {:<10} {:<10} {:<20} {:<20} {:<40}\n".format(
            str(reminder['who'])[:10],   str(reminder['how'])[:10],
            str(reminder['about'])[:10], str(reminder['time'])[:20],
            str(reminder['next'])[:20],  str(reminder['what'])[:40],
        )
        log.write(log.incolor('green', r));
    return args;



def update_todos(args):
    data  = todo.query("select author,color,category,subject,deadline,remind,quicknote from todos order by color");
    todos = []
    (now, day, soon) = quickdates();
    data = list(data);
    j = 0;
    for i in range(len(data)):
        r = QuickDate(data[i]['remind']);
        if r > now and r < day:
           todos += [data[i]];
           todos[j]['time'] = r.lex;
           j = j + 1;
        if r > now and r < soon:
           notification.notify(
             data[i]['category'] + '/'  + data[i]['subject'], 
             data[i]['remind']   + ': ' + data[i]['quicknote']);
    args['queue'].put({
       'todos' : sorted(todos, 
       key=lambda x: x['time'])
    }); 
    return args;



def print_todos(args):
    r = "{:<10} {:<10} {:<10} {:<20} {:<20} {:<40}\n".format(
      'author', 'category', 'subject', 'remind', 'time', 'quicknote',
    )
    log.write(log.incolor('purple', r));
    x = len(args['todos']);
    x = 5 if x>5 else x;
    for i in range(x):
        reminder = args['todos'][i];
        r = "{:<10} {:<10} {:<10} {:<20} {:<20} {:<40}\n".format(
            str(reminder['author'])[:10],
            str(reminder['category'])[:10],
            str(reminder['subject'])[:10],
            str(reminder['remind'])[:20],
            str(reminder['time'])[:20],
            str(reminder['quicknote'])[:40],
        )
        log.write(log.incolor(reminder['color'], r));
    log.write('\n');
    return args;



def smartlogout(args):
    try:
      args.update(q.get(False));
    except queue.Empty:
      pass;
    os.system('clear');
    if args['todos']:     args = print_todos(args);
    if args['reminders']: args = print_reminders(args);
    time.sleep(11);
    return args;



q = queue.Queue();
p = toolbelt.poller.Poller( [
    {
      'queue'    : q,
      'function' : update_reminders,
      'naptime'  : 660,
    },
    {
      'queue'    : q,
      'function' : update_todos,
      'naptime'  : 660,
    },
    {
      'queue'    : q,
      'function' : smartlogout,
      'naptime'  :  0,
      'todos'    :  None,
      'reminders':  None,
    },
]);

p.poll();
