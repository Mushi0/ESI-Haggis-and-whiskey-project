from docplex.mp.model import Model
from docplex.util.environment import get_environment
import numpy as np
import pandas as pd
from Network import network

#-----------------------------------------------------------------------------
# Build the model
#-----------------------------------------------------------------------------

class haggis_model:

    def __init__(self, network):
        self.network = network

    def print_result(self, json = False):
        # if the model is infeasible
        if self.mdl.solve_details.status == 'integer infeasible':
            print("*******************Solution*******************")
            print('The model is infeasible! ')
            print("*******************End Solution*******************")
            return 0
        # Print solution
        print("*******************Solution*******************")
        self.assign = []
        if self.msol:
            assign = []
            for j in self.network.candidates_index:
                if self.msol[self.y[j]] >= 0.99:
                    assign.append([i for i in self.network.customer_index if self.msol[self.x[i, j]] >= 0.99])
                    # If a facility is open, print the costumers that is assigned to the facility
                    print("Facility {} open to serve customers: {}"
                          .format(j, ", ".join(str(i) for i in self.network.customer_index if self.msol[self.x[i, j]] >= 0.99)))
                else:
                    assign.append([])
            self.assign.append(assign)
            print()

            print('Penalty applied to customer: {}'.format(", ".join(str(i) for j in self.network.customer_index if self.msol[self.U[j]] >= 0.99)))
            print()

            # Print the costs
            print("Total cost is: {}".format(self.msol[self.total_cost]))
            print("Facility building cost: {}".format(self.result['Facility building cost'][0]))
            print("Transportation cost: {}".format(self.result['Transportation cost'][0]))
            print("Penalty: {}".format(self.result['Penalty'][0]))

            # Save the CPLEX solution as "solution.json" program output
            if json:
                with get_environment().get_output_stream("solution.json") as fp:
                    self.mdl.solution.export(fp, "json")
        else:
            print("No solution found.")
        print("*******************End Solution*******************")

    def run_model(self, time_horizon = 20, print_detail = True, print_log = False, time_limit = 10, mip_gap = 0.01, json = False, clean_before_solve = True):
        self.mdl = Model()

        # self.M = np.max(self.network.dis_suppliers_districts)
        self.time_horizon = time_horizon

        # Create binary variables
        self.x = self.mdl.binary_var_matrix(self.network.candidates_index, self.network.customer_index, name = 'x')
        self.y = self.mdl.binary_var_list(self.network.candidates_index, name = 'y')
        # self.V = self.mdl.binary_var_matrix(self.network.candidates_index, self.network.customer_index, name = 'V')
        # self.U = self.mdl.binary_var_list(self.network.customer_index, name = 'U')
        self.U = self.mdl.continuous_var_list(self.network.customer_index, name = 'U')
        self.z = self.mdl.continuous_var_matrix(self.network.suppliers_index, self.network.candidates_index, name = 'z')

        # Add constraints
        # One customer is assigned to only one facility
        for j in self.network.customer_index:
            self.mdl.add(self.mdl.sum(self.x[i, j] for i in self.network.candidates_index) == 1)
        # A customer i is assigned to j only if a facility is located at j
        for i in self.network.candidates_index:
            for j in self.network.customer_index:
                self.mdl.add(self.x[i, j] <= self.y[i])
        # demand does not exeed supplies
        for i in self.network.candidates_index:
            for t in self.network.food_index:
                self.mdl.add(self.mdl.sum(self.x[i, j]*self.network.demand[j, t] for j in self.network.customer_index) <=
                            (self.mdl.sum(self.z[k, i]*self.network.type[k, t] for k in self.network.suppliers_index)))
        # storage less than capacity
        for i in self.network.candidates_index:
            self.mdl.add(self.mdl.sum(self.z[k, i] for k in self.network.suppliers_index) <=
                        self.network.capacity[i]*self.y[i])
        # less than 150 miles
        for i in self.network.candidates_index:
            for j in self.network.customer_index:
                self.mdl.add(self.x[i, j]*self.network.dis_districts_districts[i, j] <= 150*1.6)
        # # linking constraint for penalty
        # # find the nearest open facility
        # for i in self.network.candidates_index:
        #     for i_prime in self.network.candidates_index:
        #         for j in self.network.customer_index:
        #             self.mdl.add(self.V[i, j]*self.dis_districts_districts[i, j] <=
        #                         self.y[i_prime]*self.dis_districts_districts[i_prime, j] +
        #                         self.M(1 - self.y[i_prime]))
        # # if the customer is assigned to the nearest open facility
        # for i in self.network.candidates_index:
        #     for j in self.network.customer_index:
        #         self.mdl.add(self.U[j] >= self.x[i, j] - self.V[i, j])
        # linking constraint for penalty
        for i in self.network.candidates_index:
            for j in self.network.customer_index:
                self.mdl.add(self.U[j] + self.x[i, j] >= self.y[i] -
                        self.mdl.sum(self.y[i_prime] for i_prime in self.network.candidates_index if \
                        self.network.dis_districts_districts[i_prime, j] < self.network.dis_districts_districts[i, j]))

        self.total_cost = self.mdl.scal_prod(self.y, self.network.fixed_cost) + \
                        self.time_horizon*self.network.cost_customers*self.mdl.sum(self.network.dis_districts_districts[i, j]*self.network.demand[j, t]*self.x[i, j] \
                        for i in self.network.candidates_index for j in self.network.customer_index for t in self.network.food_index) + \
                        self.time_horizon*self.mdl.sum(self.network.cost_suppliers[k]*self.network.dis_suppliers_districts[i, k]*self.z[k, i] \
                        for k in self.network.suppliers_index for i in self.network.candidates_index) + \
                        self.network.penalty*sum(self.U[j] for j in self.network.customer_index)

        # Minimize total cost
        self.mdl.minimize(self.total_cost)
        self.mdl.set_time_limit(time_limit)
        self.mdl.parameters.mip.tolerances.mipgap.set(mip_gap)

        #-----------------------------------------------------------------------------
        # Solve the model and display the result
        #-----------------------------------------------------------------------------

        # Solve model
        if print_detail:
            self.mdl.print_information()
        print("\nSolving model....\n")
        self.msol = self.mdl.solve(log_output = print_log, clean_before_solve = clean_before_solve)
        if self.mdl.solve_details.status == 'time limit exceeded':
            print('time limit exceeded, the best bound is: ', str(self.mdl.solve_details.best_bound))
        if print_detail:
            print(self.mdl.solve_details)
            self.mdl.report()

        # self.result = pd.DataFrame()
        # if the model is not feasible
        if self.mdl.solve_details.status != 'integer infeasible':
            self.result = pd.DataFrame({'No constraints': [self.mdl.number_of_constraints],
                'No binary': [self.mdl.number_of_binary_variables],
                'No continuous': [self.mdl.number_of_continuous_variables],
                'time': [self.mdl.solve_details.time],
                'No iterations': [self.mdl.solve_details.nb_iterations],
                'status': [self.mdl.solve_details.status],
                'gap': [self.mdl.solve_details.gap],
                'best bound': [self.mdl.solve_details.best_bound],
                'objective': [self.msol[self.total_cost]],
                'Facility building cost': [sum([self.msol[self.y[i]]*self.network.fixed_cost[i] for i in self.network.candidates_index])],
                'Transportation cost': [self.time_horizon*self.network.cost_customers*self.mdl.sum(self.network.dis_districts_districts[i, j]*\
                        self.network.demand[j, t]*self.msol[self.x[i, j]] for i in self.network.candidates_index \
                        for j in self.network.customer_index for t in self.network.food_index) + \
                        self.time_horizon*self.mdl.sum(self.network.cost_suppliers[k]*self.network.dis_suppliers_districts[i, k]*self.msol[self.z[k, i]] \
                        for k in self.network.suppliers_index for i in self.network.candidates_index)],
                'Penalty': [self.network.penalty*sum(self.msol[self.U[j]] for j in self.network.customer_index)]})
        # if the model is infeasible
        else:
            self.result = pd.DataFrame({'No constraints': [self.mdl.number_of_constraints],
                'No binary': [self.mdl.number_of_binary_variables],
                'No continuous': [self.mdl.number_of_continuous_variables],
                'time': [self.mdl.solve_details.time],
                'No iterations': [self.mdl.solve_details.nb_iterations],
                'status': [self.mdl.solve_details.status],
                'gap': [self.mdl.solve_details.gap],
                'best bound': [self.mdl.solve_details.best_bound]})

        self.print_result(json = json)
