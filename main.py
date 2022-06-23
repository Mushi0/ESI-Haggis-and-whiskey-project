from Network import network
from HaggisModel import haggis_model

my_network = network()
my_network.read_data()

my_model = haggis_model(my_network)

my_model.run_model()
