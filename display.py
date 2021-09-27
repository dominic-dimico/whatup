import smartlog;
import toolbelt;
import configparser;
log = smartlog.Smartlog();


configs = {};
configs['main'] = configparser.ConfigParser()
configs['main'].read('/home/dominic/.config/notebook/notebook.cfg')
QuickDate = toolbelt.quickdate.QuickDate;



import notebook;
todo = notebook.notes.ToDo();
from plyer import notification
def update_todos(args):
    todo.log.quiet = True;
    data  = todo.query("select author,color,category,subject,deadline,remind,quicknote from todos order by color");
    todo.log.quiet = False;
    todos = []
    now   = QuickDate('now');
    day   = QuickDate('tomorrow');
    soon  = QuickDate('17 minutes');
    data = list(data);
    j = 0;
    for i in range(len(data)):
        r = QuickDate(data[i]['remind']);
        if r > now and r < day:
           todos += [data[i]];
           todos[j]['time'] = r.lex;
           j = j + 1;
        if r > now and r < soon:
           pass
           notification.notify(
             data[i]['category'] + '/'  + data[i]['subject'], 
             data[i]['remind']   + ': ' + data[i]['quicknote']);
    todos = sorted(todos, key=lambda x: x['time'])
    args['queue'].put({
       'todos' : todos,
    }); 
    return args;



import pyowm;
def update_weather(args):
    api_key     = "0303330a21633d2d4ff88868fe35d716"
    owm         = pyowm.OWM(api_key);
    manager     = owm.weather_manager();
    weather     = manager.one_call(30.3322, 81.6557);
    args['queue'].put({
      'weather' : weather
    });
    return args;



import requests;
import pandas;
def update_news(args):
    data = {
        'country'  : 'us',
        'apiKey'   : '37a581e9d84f4bc391543e6e8ef2855a'
    }
    url  = "https://newsapi.org/v2/top-headlines"
    resp = requests.get(url, data);
    args['queue'].put({
      'news' : resp.json()['articles'][:12]
    });
    return args;



def print_weather_line(w):
    t = w.temperature('fahrenheit');
    if 'temp' in t:
       t = t['temp'];
    elif 'day' in t:
       t = t['day'];
    log.outfile.write(
        "%s: %s %s: %s  %s: %s  %s: %s  %s: %s\n" % (
                      "Time",        w.reference_time('iso'),
           log.t.red("Temp"),       t,
           log.t.green("Humidity"), w.humidity,
           log.t.blue("Rain"),      w.precipitation_probability,
           log.t.yellow("Status"),  w.detailed_status,
       )
    );



def print_weather(args):
    w = args['weather'].current;
    print_weather_line(w);
    log.outfile.write("\n");
    return args;



def print_news(args):
    ns = args['news'];
    for i in range(args['a'], args['b']):
        n = ns[i];
        if not n['description']: n['description']='';
        if not n['author']:      n['author']='';
        if not n['title']:       n['title']='';
        log.outfile.write("%s - %s:\n%s\n%s\n\n" % (
          log.t.red(n['source']['name']),
          log.t.blue(n['author']),
          log.incolor('yellow', n['title']),
          log.t.green(n['description']),
        ));
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
    for i in range(x, 10):
        log.write('\n');
    return args;



import os
import time
import queue;
def smartlogout(args):

    try:
      args.update(q.get(False));
    except queue.Empty:
      pass;

    os.system('clear');
    args.update({'a':0,'b':3});
    if args['weather']: args = print_weather(args);
    if args['todos']:   args = print_todos(args);
    if args['news']:    args = print_news(args);
    time.sleep(12);

    os.system('clear');
    args.update({'a':3,'b':7});
    if args['weather']: args = print_weather(args);
    if args['todos']:   args = print_todos(args);
    if args['news']:    args = print_news(args);
    time.sleep(12);

    os.system('clear');
    args.update({'a':7,'b':11});
    if args['weather']: args = print_weather(args);
    if args['todos']:   args = print_todos(args);
    if args['news']:    args = print_news(args);
    time.sleep(12);

    return args;



q = queue.Queue();
p = toolbelt.poller.Poller( [
    {
      'queue'    : q,
      'function' : update_weather,
      'naptime'  : 3600,
    },
    {
      'queue'    : q,
      'function' : update_news,
      'naptime'  : 3600,
    },
    {
      'queue'    : q,
      'function' : update_todos,
      'naptime'  : 60*17,
    },
    {
      'queue'    : q,
      'function' : smartlogout,
      'naptime'  :  0,
      'weather'  :  None,
      'news'     :  None,
      'todos'    :  None,
    },
]);

p.poll();
