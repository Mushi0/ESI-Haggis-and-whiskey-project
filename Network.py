import numpy as np
import pandas as pd

class network:

    def __init__(self, nb_customers = 400, nb_candidates = 400, nb_suppliers = 50, nb_food = 4):
        self.nb_customers = nb_customers
        self.nb_candidates = nb_candidates
        self.nb_suppliers = nb_suppliers
        self.nb_food = nb_food
        self.__set_index_sets()

    def __set_index_sets(self):
        self.customers_index = range(self.nb_customers)
        self.candidates_index = range(self.nb_candidates)
        self.suppliers_index = range(self.nb_suppliers)
        self.food_index = range(self.nb_food)

    def set_size(self, nb_customers, nb_candidates, nb_suppliers, nb_food):
        self.nb_customers = nb_customers
        self.nb_candidates = nb_candidates
        self.nb_suppliers = nb_suppliers
        self.nb_food = nb_food
        self.__set_index_sets()

    def read_data(self, folder_name = 'Data'):
        Suppliers = pd.read_excel(folder_name + '\Suppliers.xlsx', sheet_name = 'SuppliersClass')
        Candidates = pd.read_excel(folder_name + '\Potential Locations.xlsx', sheet_name = 'Postcode Districts - Class')
        Customers = pd.read_excel(folder_name + '\Postcode Districts.xlsx', sheet_name = 'Postcode Districts - Class')
        dis_suppliers_districts = pd.read_excel(folder_name + '\Distance Supplier-District.xlsx', sheet_name = 'Sheet1')
        dis_districts_districts = pd.read_excel(folder_name + '\Distance District-District.xlsx', sheet_name = 'Sheet1')
        self.fixed_cost = np.array(Candidates['Setup cost for 20 yrs'])
        vihecle = [0, 0.09, 0.226]
        self.cost_suppliers = np.array([vihecle[i] for i in Suppliers['Vehicle Type (1=18t, 2=7.5t)']])
        self.cost_customers = 0.362
        self.dis_suppliers_districts = np.array(dis_suppliers_districts.iloc[:, 1:])
        self.dis_districts_districts = np.array(dis_districts_districts.iloc[:, 1:])
        self.production = np.array(Suppliers['Production volume'])
        self.demand = np.array(Customers[['Group 1', 'Group 2', 'Group 3', 'Group 4']])
        self.capacity = np.array(Candidates['Annual capacity'])
        # self.type = np.array(Suppliers['Product group'] - 1)
        self.type = np.zeros([len(np.array(Suppliers['Product group'])), 4])
        for i, t in enumerate(np.array(Suppliers['Product group'] - 1)):
            self.type[i, t] = 1
        self.penalty = 50000
        self.set_size(len(Customers), len(Candidates), len(Suppliers), self.demand.shape[1])

    # def print_network(self):
    #     print(f'Customer coordinates: \n{self.customers}')
    #     print(f'Candidates coordinates: \n{self.candidates}')
    #     print(f'Building cost: \n{self.building_cost}')
    #     print(f'Capacity cost: \n{self.capacity_cost}')
    #     print(f'Capacity Increasing cost: \n{self.capacity_increase_cost}')
    #     print(f'Maximum capacities: \n{self.capacity_max}')
    #     print(f'Minimum capacities: \n{self.capacity_min}')
    #     print(f'M: \n{self.M}')
    #     print(f'Transportation cost: \n{self.transportation_cost}')
