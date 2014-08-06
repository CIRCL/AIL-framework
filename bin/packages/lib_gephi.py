import networkx as nx
import xml.sax.saxutils as xlm
import redis

def Gephi_Graph(r_serv, graphpath, mincard, maxcard, insert_type):
    """Create Gephi Graph by calling a "Sub function": Create_Graph

    :param r_serv: -- connexion to redis database
    :param graphpath: -- the absolute path of the .gephi graph created.
    :param mincard: -- the minimum links between 2 nodes to be created
    :param maxcard: -- the maximum links between 2 nodes to be created
    :param insert_type: -- the type of datastructure used to create the graph.

    In fact this function is juste here to be able to choose between two kind of
    Redis database structure: One which is a Sorted set and the other a simple
    set.

    """
    g = nx.Graph()

    if (insert_type == 0):

        for h in r_serv.smembers("hash"):
            Create_Graph(r_serv, g, h, graphpath, mincard, maxcard)

    elif (insert_type == 2):

        for h in r_serv.zrange("hash", 0, -1):
            Create_Graph(r_serv, g, h, graphpath, mincard, maxcard)

    nx.write_gexf(g,graphpath)
    print nx.info(g)




def Create_Graph(r_serv, graph, h, graphpath, mincard, maxcard):
    """Create Gephi Graph.

    :param r_serv: -- connexion to redis database
    :param graph: -- networkx graph object
    :param h: -- (str) the hash which will be transform into a node.
    :param graphpath: -- the absolute path of the .gephi graph created.
    :param mincard: -- the minimum links between 2 nodes to be created
    :param maxcard: -- the maximum links between 2 nodes to be created

    This function link all the pastes with theirs own hashed lines.
    Of course a paste can have multiple hashed lines and an hashed line can be
    contained in multiple paste.
    In this case it's a common hash.

    """
    if (r_serv.scard(h) >= mincard) and (r_serv.scard(h) <= maxcard):

                for filename in r_serv.smembers(h):

                    for line in r_serv.smembers(filename):

                        line = line.decode('UTF-8', errors='ignore')
                        line = xlm.quoteattr(line, {'"':'&quot;', "'":"&apos;"})

                        graph.add_edge(h, line+" -- "+filename)

#OK