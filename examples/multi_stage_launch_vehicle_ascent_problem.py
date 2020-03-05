"""
TODO:
	* Use `collections.namedtuple` for accessing endpoint variables and values.
	* Add checking for state endpoint constraints to ensure that they are only 
		functions of a single state endpoint variable.
	* Allow user-defined phase names and change phase storage to use 
		`collections.namedtuple` to support this.
	* Similarly use `collections.namedtuple` for phases so that these can be 
		indexed by phase name.
	* Rename 'phase numbering' to 'phase naming' and use A, B, C etc. instead 
		of 1, 2, 3 etc. to avoid confusion with Python's zero-based indexing 
		and to make sense with the fact that phases need not be sequential.
	* Provide the `OptimalControlProblem.new_phase_like(Phase)` method 
		involving creating a deep copy of a Phase object, and resetting certain 
		attributes such as `self.auxiliary_data`.
	* Provide a setting for maximising the objective function. Ensure that 
		objective is nonnegative and pair this attribute with 
		`problem.settings.minimise_objective`.
	* Parse endpoint constraints and endpoint time bounds to ensure the correct 
		number of time variables present in the optimal control problem.
	* Allow use of matrix expressions (instead of just scalar expressions like 
		currently supported) to reduce the amount of code needed.

Done:
	* Use `collections.namedtuple` objects for variable storage so that they 
		can be indexed by variable name rather than index.

Pitfalls/Gotchas:
	* Name all symbols the same as their variables are named in your scripts.
"""

import numpy as np
import pycollo
import sympy as sym

# Define all symbols for building problem equations
r_x, r_y, r_z = sym.symbols('r_x r_y r_z')
v_x, v_y, v_z = sym.symbols('v_x v_y v_z')
m = sym.Symbol('m')
u_x, u_y, u_z = sym.symbols('u_x u_y u_z')
D_x, D_y, D_z = sym.symbols('D_x D_y D_z')
T, xi, C_D, S_rho, omega_E = sym.symbols('T xi C_D S_rho omega_E')
v_r_x, v_r_y, v_r_z = sym.symbols('v_r_x v_r_y v_r_z')
omega_x_r_x, omega_x_r_y, omega_x_r_z = sym.symbols('omega_x_r_x omega_x_r_y omega_x_r_z')
mu, R_E, psi_L, g_0, h_0, h, rho, rho_0 = sym.symbols('mu R_E psi_L g_0 h_0 h rho rho_0')
r_vec_norm, u_vec_norm, v_vec_norm, v_r_vec_norm = sym.symbols('r_vec_norm u_vec_norm v_vec_norm v_r_vec_norm')
T_S, T_1, T_2 = sym.symbols('T_S T_1 T_2')
I_S, I_1, I_2 = sym.symbols('I_S I_1 I_2')
m_tot_S, m_tot_1, m_tot_2, m_payload = sym.symbols('m_tot_S m_tot_1 m_tot_2 m_payload')
m_prop_S, m_prop_1, m_prop_2 = sym.symbols('m_prop_S m_prop_1 m_prop_2')
m_struct_S, m_struct_1, m_struct_2 = sym.symbols('m_struct_S m_struct_1 m_struct_2')
tau_burn_S, tau_burn_1, tau_burn_2 = sym.symbols('tau_burn_S tau_burn_1 tau_burn_2')
T_eng_S, T_eng_1, T_eng_2 = sym.symbols('T_eng_S T_eng_1 T_eng_2')

problem = pycollo.OptimalControlProblem(
	name='Multi-stage launch vehicle ascent problem')

phase_A = problem.new_phase('A')
phase_A.state_variables = [
	r_x,   	# Cartesian x-vector position relative to the centre of the earth 
			#     using earth-centered inertial (ECI) coordinates (in m)
	r_y,   	# Cartesian y-vector position using ECI coordinates (in m)
	r_z,   	# Cartesian z-vector position using ECI coordinates (in m)
	v_x,   	# Cartesian x-vector velocity using ECI coordinates (in m/s)
	v_y,   	# Cartesian y-vector velocity using ECI coordinates (in m/s)
	v_z,   	# Cartesian z-vector velocity using ECI coordinates (in m/s)
	m,     	# Total mass (in kg)
	]

phase_A.control_variables = [
	u_x,
	u_y,
	u_z
	]

phase_A.state_equations = [
	v_x,
	v_y,
	v_z,
	- (mu/(r_vec_norm**3))*r_x + (T/m)*u_x + (1/m)*D_x,
	- (mu/(r_vec_norm**3))*r_y + (T/m)*u_y + (1/m)*D_y,
	- (mu/(r_vec_norm**3))*r_z + (T/m)*u_z + (1/m)*D_z,
	- xi,
	]

phase_A.path_constraints = [
	u_vec_norm,
	r_vec_norm,
	]

phase_A.bounds.initial_time = 0
phase_A.bounds.final_time = [75.2, 75.2]
phase_A.bounds.state_variables = {
	r_x: [-2 * R_E, 2 * R_E],
	r_z: [-2 * R_E, 2 * R_E],
	r_y: [-2 * R_E, 2 * R_E],
	v_z: [-10000, 10000],
	v_x: [-10000, 10000],
	v_y: [-10000, 10000],
	m: [9*m_tot_S + m_tot_1 + m_tot_2 + m_payload, phase_A.initial_state_variables.m 
		- (6*m_prop_S + (tau_burn_S/tau_burn_1)*m_prop_1)]
	}
phase_A.bounds.control_variables = {
	u_x: [-10, 10],
	u_y: [-10, 10],
	u_z: [-10, 10],
	}
phase_A.bounds.path_constraints = [
	1,
	[R_E, 'inf'],
	]
phase_A.bounds.initial_state_constraints = {
	r_x: R_E*sym.cos(psi_L),
	r_y: 0,
	r_z: R_E*sym.sin(psi_L),
	v_x: 0,
	v_y: - omega_E*R_E*sym.cos(psi_L),
	v_z: 0,
	m: 9*m_tot_S + m_tot_1 + m_tot_2 + m_payload,
	}

phase_A.guess.time = [0.0, 75.2]
phase_A.guess.state_variables = {
	r_x: [],
	}
phase_A.guess.control = [
	[0, 0],
	[1, 1],
	[0, 0],
	]

phase_A.auxiliary_data = {
	T: 6*T_S + T_1,
	xi: (1/g_0) * (6*T_S/I_S + T_1/I_1),
	}

# print('\n\n\n')
# print(phase_A.scaling)
# raise NotImplementedError

phase_B, phase_C, phase_D = problem.new_phases_like(number=3, 
	phase_for_copying=phase_A,
	names=['B', 'C', 'D'],
	copy_state_variables=True,
	copy_control_variables=True,
	copy_state_equations=True,
	copy_path_constraints=True,
	copy_integrand_functions=True,
	copy_state_endpoint_constraints=False,
	copy_bounds=True,
	copy_mesh=True,

	)

# PHASE 2

phase_B.bounds.initial_time = phase_A.bounds.final_time

phase_B.auxiliary_data = {
	T: 3*T_S + T_1,
	xi: (1/g_0) * (3*T_S/I_S + T_1/I_1),
	}

# PHASE 3

phase_C.auxiliary_data = {
	T: T_1,
	xi: T_1/(g_0*I_1),
	}

# PHASE 4

phase_D.auxiliary_data = {
	T: T_2,
	xi: T_2/(g_0*I_2),
	}

problem.objective_function = problem.phases[2].final_state_variables.m

problem.endpoint_constraints = [
	phase_D.final_time_variable - phase_D.initial_time_variable,
	(phase_A.final_state_variables.m - phase_A.initial_state_variables.m 
		+ 6*m_prop_S + (tau_burn_S/tau_burn_1)*m_prop_1),
	(phase_B.initial_state_variables.m - phase_A.final_state_variables.m 
		+ 6*m_struct_S),
	(phase_B.final_state_variables.m - phase_B.initial_state_variables.m 
		+ 3*m_prop_S + (tau_burn_S/tau_burn_1)*m_prop_1),
	(phase_C.initial_state_variables.m - phase_B.final_state_variables.m 
		+ 3*m_struct_S),
	(phase_C.final_state_variables.m - phase_C.initial_state_variables.m
		+ (1 - 2*(tau_burn_S/tau_burn_1))*m_prop_1),
	(phase_D.initial_state_variables.m - phase_C.final_state_variables.m
		+ m_struct_1),
	]

problem.bounds.endpoint_constraints = [
	961 - 261,
	0,
	0,
	0,
	0,
	0,
	0,
	]

problem.auxiliary_data = {
	mu: 3.986012e14, # 
	R_E: 6378145, # Radius of Earth (in m)
	r_vec_norm: sym.sqrt(r_x**2 + r_y**2 + r_z**2), # Absolute position (in m)
	v_vec_norm: sym.sqrt(v_x**2 + v_y**2 + v_z**2), # Absolute velocity (in m/s)
	u_vec_norm: sym.sqrt(u_x**2 + u_y**2 + u_z**2), # Absolute control (in N)
	D_x: - 0.5 * C_D * S_rho * v_r_vec_norm * v_r_x, # Drag for in x-direction (in N)
	D_y: - 0.5 * C_D * S_rho * v_r_vec_norm * v_r_y, # Drag for in y-direction (in N)
	D_z: - 0.5 * C_D * S_rho * v_r_vec_norm * v_r_z, # Drag for in z-direction (in N)
	C_D: 0.5, # Coefficient of drag (nondimensional)
	S_rho: 4*np.pi, # Surface area (in m^2)
	v_r_vec_norm: sym.sqrt(v_r_x**2 + v_r_y**2 + v_r_z**2),
	v_r_x: v_x - (omega_x_r_x),
	v_r_y: v_y - (omega_x_r_y),
	v_r_z: v_z - (omega_x_r_z),
	omega_x_r_x: - omega_E * r_y,
	omega_x_r_y: omega_E * r_x,
	omega_x_r_z: 0,
	g_0: 9.80665, # Accerlation due to gravity at sea level (in m/s^2)
	h_0: 7200, # Density scale height (in m)
	h: r_vec_norm - R_E, # Absolute altitude above sea level (in m)
	rho: rho_0 * sym.exp(-h/h_0), # Atmospheric density (in kg/m^3)
	rho_0: 1.225, # Atmospheric density at sea level (in kg/m^3)
	omega_E: 7.29211585e-5, # Angular velocity of earth relative to inertial space (in rad/s)
	m_tot_S: 19290, # Total mass of solid boosters (in kg)
	m_tot_1: 104380, # Total mass of stage 1 (in kg)
	m_tot_2: 19300, # Total mass of stage 2 (in kg)
	m_prop_S: 17010, # Propellant mass of solid boosters (in kg)
	m_prop_1: 95550, # Propellant mass of stage 1 (in kg)
	m_prop_2: 16820, # Propellant mass of stage 2 (in kg)
	m_struct_S: 2280, # Structure mass of solid boosters (in kg)
	m_struct_1: 8830, # Structure mass of stage 1 (in kg)
	m_struct_2: 2480, # Structure mass of stage 2 (in kg)
	T_eng_S: 628500, # Engine thrust of solid boosters (in N)
	T_eng_1: 1083100, # Engine thrust of stage 1 (in N)
	T_eng_2: 110094, # Engine thrust of stage 2 (in N)
	I_S: 283.33364, # Specific impulse of solid boosters (in s)
	I_1: 301.68776, # Specific impulse of stage 1 (in s)
	I_2: 467.21311, # Specific impulse of stage 2 (in s)
	tau_burn_S: 75.2, # Burn time of solid boosters (in s)
	tau_burn_1: 261, # Burn time of stage 1 (in s)
	tau_burn_2: 700, # Burn time of stage 2 (in s)
	m_payload: 4146, # Mass of payload (in kg)
	}

problem.settings.nlp_tolerance = 10e-7
problem.settings.mesh_tolerance = 10e-6
problem.settings.maximise_objective = True
problem.settings.backend = "casadi" # problem.settings.backend = "pycollo"
