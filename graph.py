import networkx as nx
from collections import defaultdict
import csv
import numpy as np
from urllib.parse import urlparse


class Graph:

    def __init__(self, graph_input_filename='results'):
        self.csv_data = None
        self.Graph = nx.DiGraph([])
        self.nodes = np.asarray([])
        self.edges = tuple()
        self.links = np.asarray([])
        self.file_name = graph_input_filename

    def load_graph_from_scv(self):
        with open(self.file_name + '.csv', encoding='utf-8') as csvdata:
            self.csv_data = csv.reader(csvdata)
            self.csv_data = np.array([n for n in self.csv_data][1:])
        self.nodes = self.csv_data[:, 1]  # each scraped url is a node
        self.links = self.csv_data[:, 2]
        self.edges = tuple(
            zip(self.nodes, self.links))  # an edge is defined as a relationship between scraped url and its href links
        self.Graph.add_nodes_from(self.nodes)
        self.Graph.add_edges_from(self.edges)

        print(nx.info(self.Graph))

    def set_edges_attributes(self):
        domain_dict = {}
        emails_dict = {}
        url_dict = {}

        for link in self.links:
            domain_dict[link] = urlparse(link).netloc
            emails_dict[link] = set()
            url_dict[link] = link

        for csv_line in self.csv_data:
            domain_dict[csv_line[1]] = csv_line[0]
            emails_dict[csv_line[1]] = csv_line[3]
            url_dict[csv_line[1]] = csv_line[1]

        nx.set_node_attributes(self.Graph, domain_dict, 'domain')
        nx.set_node_attributes(self.Graph, url_dict, 'url')
        nx.set_node_attributes(self.Graph, emails_dict, 'emails')

        print('finished setting nodes attributes')

    def relabel_nodes_to_integers(self):
        mapping = dict(zip(self.Graph, range(1, len(self.Graph.nodes()) + 1)))
        self.Graph = nx.relabel_nodes(self.Graph, mapping)

    def get_5_main_emails_of_each_domain(self):
        domains_arr = np.unique(self.csv_data[:,0])
        result_dict = dict()
        for domain in domains_arr:
            result_dict[domain] = self.get_5_main_emails_of_domain(domain)
        return result_dict

    def get_5_main_emails_of_domain(self, domain):
        result_dict = defaultdict(set)
        result_list = []
        domain_nodes_list = [n for n in self.Graph.nodes() if self.Graph.nodes[n]['domain'] == domain]
        domain_graph = self.Graph.subgraph(domain_nodes_list)
        for n in domain_graph.nodes:
            if not (domain_graph.nodes[n]['emails'] == 'set()' or domain_graph.nodes[n]['emails'] == set()):
                email_list = (domain_graph.nodes[n]['emails']).split(", ")
                for email in email_list:
                    email = email.translate({ord('{'): None, ord('}'): None, ord("'"): None})
                    result_dict[domain_graph.nodes[n]['domain']].add((email, None))
        if result_dict:
            degree_centrality_dict = nx.degree_centrality(domain_graph)
            closeness_centrality_dict = nx.closeness_centrality(domain_graph)
            betweenness_centrality_dict = nx.betweenness_centrality(domain_graph)

            nx.set_node_attributes(domain_graph, degree_centrality_dict, 'degree_centrality')
            nx.set_node_attributes(domain_graph, closeness_centrality_dict, 'closeness_centrality')
            nx.set_node_attributes(domain_graph, betweenness_centrality_dict, 'betweenness_centrality')

            for email in result_dict[domain]:
                score = round(self.get_email_score(email[0], domain_graph), 3)
                result_dict[domain].remove(email)
                result_dict[domain].add((email[0], score))
            for i in range(5):
                if not result_dict[domain]:
                    break
                max_score = max(result_dict[domain], key=lambda x: x[1])
                result_list.append(max_score)
                result_dict[domain].remove(max_score)
        else:
            return 'No emails found!'
        return result_list

    @staticmethod
    def get_email_score(email, domain_graph):
        score = 0
        for n in domain_graph.nodes:
            if email in (domain_graph.nodes[n]['emails']):
                score += domain_graph.nodes[n]['degree_centrality'] + domain_graph.nodes[n]['closeness_centrality'] + \
                         domain_graph.nodes[n]['betweenness_centrality']
        return score
