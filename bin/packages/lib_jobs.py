import redis, time, sys, os, inspect

from datetime import timedelta, date, datetime

from pubsublogger import publisher

def set_listof_pid(r_serv, filename, name):
    """Create the pid list and it's pid members

    :param r_serv: -- Connexion to redis.
    :param filename: -- the absolute pastes path name.
    :param name: -- the traditionnal argv[0] (The name of the launched script)

    This function create a hashes in redis as follows and a set of pid.

    +------------+------------+---------------------+
    |     Keys   | Fields     | Values              |
    +============+============+=====================+
    | 2045       | startime   | 2014-05-09_11:44:17 |
    +------------+------------+---------------------+
    | ...        | prog       | ./programme         |
    +------------+------------+---------------------+
    | ...        | pid        | 2045                |
    +------------+------------+---------------------+
    | ...        | paste      | /home/folder/aux.gz |
    +------------+------------+---------------------+
    | ...        | kb         | 54.12               |
    +------------+------------+---------------------+

    +------------+------------+
    |     Keys   | Members    |
    +============+============+
    | pid        | 2045       |
    +------------+------------+
    | ...        | 2480       |
    +------------+------------+

    """
    r_serv.sadd("pid", os.getpid())
    r_serv.hmset(os.getpid(),
    {
    "startime":time.strftime("%Y-%m-%d_%H:%M:%S"),
    "prog":name,
    "pid":str(os.getpid()),
    "paste":filename,
    "Kb":round(os.path.getsize(filename)/1024.0,2)
    })




def update_listof_pid(r_serv):
    """Remove pid from the pid list

    :param r_serv: -- Connexion to redis.

    Remove from the list and redis, pid which are terminated.

    """
    r_serv.srem("pid", os.getpid())
    r_serv.delete(os.getpid())




def flush_list_of_pid(r_serv):
    """Flush the datas in redis

    :param r_serv: -- Connexion to redis.

    Clean the redis database from the previous pid and pidlist inserted

    """
    for x in r_serv.smembers("pid"):
        r_serv.delete(x)

    r_serv.delete("pid")




def format_display_listof_pid(dico, arg):
    """Formating data for shell and human

    :param dico: (dict) dictionnary
    :param arg: (str) Choosing argument

    :returns: (str)

    This function provide different displaying formats for the dictionnary's data.

    """
    if arg == 'pid':
        var = "{0}".format(dico['pid'])
    elif arg == 'up':
        var = "{0}".format(dico['uptime'])
    elif arg == 'kb':
        var = "{0}".format(dico['Kb'])
    elif arg == 'paste':
        var = "{0}".format(dico['paste'])
    elif arg == 'startime':
        var = "{0}".format(dico['startime'])
    elif arg == 'prg':
        var = "{0}".format(dico['prog'])
    else:
        var = "PID:{0},uptime:{1},kb:{2},paste:{3},prog:{4},startime:{5}".format(dico['pid'],
        dico['uptime'],
        dico['Kb'],
        dico['paste'],
        dico['prog'],
        dico['startime'])

    return var




def display_listof_pid(r_serv, arg):
    """Display the pid list from redis

    This function display infos in the shell about lauched process

    """
    jobs = {}
    joblist = []
    try:
        for job in r_serv.smembers("pid"):
            jobs = r_serv.hgetall(job)

            if jobs != None:
                start = datetime.strptime(r_serv.hget(job, "startime"), "%Y-%m-%d_%H:%M:%S")

                end = datetime.strptime(time.strftime("%Y-%m-%d_%H:%M:%S"), "%Y-%m-%d_%H:%M:%S")
                jobs['uptime'] = str(abs(start - end))
                joblist.append(jobs)
            else:
                publisher.debug("display_list_of_pid Aborted due to lack of Information in Redis")

        joblist = sorted(joblist, key=lambda k: k['uptime'], reverse=True)

        for job in joblist:
            print format_display_listof_pid(job, arg)

        if arg == "remain":
            print "Remaining: {0}".format(r_serv.llen("filelist"))

        if arg == "processed":
            print "processed: {0}".format(r_serv.llen("processed"))

    except TypeError:
        publisher.error("TypeError for display_listof_pid")
