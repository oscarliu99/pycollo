import abc

import numpy as np
import scipy.sparse as sparse


DEFAULT = "default"
BOUNDS = "bounds"
USER = "user"
GUESS = "guess"
NONE = "none"


class ScalingABC(abc.ABC):

	_NONE_SCALING_DEFAULT = 1
	_STRETCH_DEFAULT = 1
	_SHIFT_DEFAULT = 0
	_METHOD_OPTIONS = {DEFAULT, BOUNDS, USER, GUESS, NONE, None}
	_METHOD_DEFAULT = BOUNDS
	_UPDATE_DEFAULT = True
	_NUMBER_SAMPLES_DEFAULT = 100
	_UPDATE_WEIGHT_DEFAULT = 0.8

	@abc.abstractmethod
	def optimal_control_problem(self): pass



class EndpointScaling(ScalingABC):
	
	def __init__(self, optimal_control_problem):

		self._ocp = optimal_control_problem

		self.parameter_variables = self._NONE_SCALING_DEFAULT
		self.endpoint_constraints = self._NONE_SCALING_DEFAULT

	@property
	def optimal_control_problem(self):
		return self._ocp

	def __repr__(self):
		cls_name = self.__class__.__name__
		string = (f"{cls_name}(optimal_control_problem={self._ocp}, )")
		return string


class PhaseScaling(ScalingABC):
	
	def __init__(self, phase):

		self.phase = phase

		self.time = self._NONE_SCALING_DEFAULT
		self.state_variables = self._NONE_SCALING_DEFAULT
		self.control_variables = self._NONE_SCALING_DEFAULT
		self.integral_variables = self._NONE_SCALING_DEFAULT
		self.path_constraints = self._NONE_SCALING_DEFAULT

	@property
	def optimal_control_problem(self):
		return self.phase.optimal_control_problem

	@property
	def phase(self):
		return self._phase
	
	@phase.setter
	def phase(self, phase):
		self._phase = phase

	def _generate_bounds(self):
		raise NotImplementedError

	def _generate_guess(self):
		raise NotImplementedError

	def _generate_none(self):
		num_needed = self.optimal_control_problem._backend.num_s_vars
		shift = self._SHIFT_DEFAULT * np.ones(num_needed)
		stretch = self._STRETCH_DEFAULT * np.ones(num_needed)
		return shift, stretch

	def _generate_user(self):
		raise NotImplementedError

	def __repr__(self):
		cls_name = self.__class__.__name__
		string = (f"{cls_name}(phase={self.phase}, )")
		return string


class Scaling:

	def __init__(self, backend):

		self.backend = backend
		self.ocp = backend.ocp
		self._GENERATE_DISPATCHER = {
			None: self._generate_none,
			USER: self._generate_user,
			BOUNDS: self._generate_bounds,
			GUESS: self._generate_guess,
			}
		self._generate()

	def _generate(self):
		method = self.ocp.settings.scaling_method
		self.x_shift, self.x_stretch = self._GENERATE_DISPATCHER[method]()

	def _generate_bounds(self):
		x_l = self.backend.bounds.x_bnds_lower
		x_u = self.backend.bounds.x_bnds_upper
		for p, p_slice in zip(self.backend.p, self.backend.phase_variable_slices):
			t_start = p_slice.start + p.t_slice.start
			t_stop = p_slice.start + p.t_slice.stop
			x_l[t_start:t_stop] = -0.5
			x_u[t_start:t_stop] = 0.5
		shift = 0.5 - x_u / (x_u - x_l)
		stretch = 1 / (x_u - x_l)
		return shift, stretch

	def _generate_guess(self):
		raise NotImplementedError

	def _generate_none(self):
		num_needed = self.backend.num_vars
		shift = self._SHIFT_DEFAULT * np.ones(num_needed)
		stretch = self._STRETCH_DEFAULT * np.ones(num_needed)
		return shift, stretch

	def _generate_user(self):
		raise NotImplementedError




class IterationScaling:

	def __init__(self, iteration):
		self.iteration = iteration
		self.backend = self.iteration.backend
		self._GENERATE_DISPATCHER = {
			True: self._generate_from_previous,
			False: self._generate_from_base,
			}
		# self._generate()

	@property
	def optimal_control_problem(self):
		return self.iteration.optimal_control_problem

	@property
	def base_scaling(self):
		return self.optimal_control_problem._backend.scaling

	def _generate(self):
		update_scaling = self.optimal_control_problem.settings.update_scaling
		if self.iteration.number >= 2:
			self._GENERATE_DISPATCHER[update_scaling]()
		else:
			self._generate_from_base()

	def _expand_x_to_mesh(self, base_scaling):
		parts = []
		for p, p_slice, N in zip(self.backend.p, self.backend.phase_variable_slices, self.iteration.mesh.N):
			p_scaling = base_scaling[p_slice]
			yu_scaling = p_scaling[p.yu_slice]
			qt_scaling = p_scaling[p.qt_slice]
			parts.append(np.repeat(yu_scaling, N))
			parts.append(qt_scaling)
		parts.append(base_scaling[self.backend.variable_slice])
		scaling = np.concatenate(parts)
		return scaling

	def _generate_from_base(self):

		x_guess = self.iteration.guess_x

		# Variables scale
		self._x_offset_unexpanded = self.base_scaling.x_shift
		r_vals = self._expand_x_to_mesh(self.base_scaling.x_shift)
		self._x_scaling_unexpanded = self.base_scaling.x_stretch
		V_vals = self._expand_x_to_mesh(self.base_scaling.x_stretch)

		self.x_shift = r_vals
		self.x_stretch = np.reciprocal(V_vals)
		self.x_scaling = V_vals

		# Objective scale
		self.obj_scaling = self._calculate_objective_scaling(x_guess)
		
		# Constraints scale
		c_scaling = self._calculate_constraint_scaling(x_guess)
		parts = []
		for c_defect_slice, c_integral_slice, num_c_path in zip(self.iteration.c_defect_slices, self.iteration.c_integral_slices, self.iteration.num_c_path_per_phase):
			W_defect = V_vals[c_defect_slice]
			W_path = np.ones(num_c_path)
			W_integral = V_vals[c_integral_slice]
			parts.append(W_defect)
			parts.append(W_path)
			parts.append(W_integral)
		W_point = np.ones(self.iteration.num_c_endpoint)
		parts.append(W_point)
		W_vals = np.concatenate(parts)
		
		self.c_scaling = W_vals

	def _generate_from_previous(self):
		x_guess = self.iteration._guess._x

		obj_scaling = self._calculate_objective_scaling(x_guess)
		prev_obj_scalings = [mesh_iter.scaling.obj_scaling for mesh_iter in self.optimal_control_problem._mesh_iterations[:-1]]
		obj_scalings = np.array(prev_obj_scalings + [obj_scaling])
		alpha = self.optimal_control_problem.settings.scaling_weight
		weights = np.array([alpha*(1 - alpha)**i for i, _ in enumerate(obj_scalings)])
		weights = np.flip(weights)
		weights[0] /= alpha
		self.obj_scaling = np.average(obj_scalings, weights=weights)

		yu = x_guess[self.iteration._yu_slice].reshape(self.iteration._mesh._N, -1)
		yu_min = np.min(yu, axis=0)
		yu_max = np.max(yu, axis=0)
		x_shift_yu = 0.5 - yu_max - (yu_max - yu_min)
		x_scaling_yu = 1 / (yu_max - yu_min)
		qts = x_guess[self.iteration._qts_slice]
		x_scaling_qts = 1 / np.abs(qts)
		x_scaling = np.concatenate([x_scaling_yu, x_scaling_qts])
		prev_x_scalings = np.array([mesh_iter.scaling._x_scaling_unexpanded 
			for mesh_iter in self.optimal_control_problem._mesh_iterations[:-1]])
		x_scalings = np.vstack([prev_x_scalings, x_scaling])
		self._x_scaling_unexpanded = np.average(x_scalings, axis=0, weights=weights)
		self.x_scaling = self._expand_x_to_mesh(self._x_scaling_unexpanded)

		self.c_scaling = self._calculate_constraint_scaling(x_guess)
		self.c_scaling[self.iteration._c_defect_slice] = self.x_scaling[self.iteration._c_defect_slice]
		self.c_scaling[self.iteration._c_integral_slice] = self.x_scaling[self.iteration._c_integral_slice]

	def _calculate_objective_scaling(self, x_guess):
		g = self.iteration._gradient_lambda(x_guess)
		g_norm = np.sum(g**2)
		obj_scaling = 1 / g_norm
		return obj_scaling

	def _calculate_constraint_scaling(self, x_guess):
		G = self.iteration._jacobian_lambda(x_guess)
		sG = sparse.coo_matrix((G, self.iteration._jacobian_structure_lambda()), shape=self.iteration._G_shape)
		G_norm = sG.power(2).sum(axis=1)
		c_scaling = np.array(1 / G_norm).squeeze()
		return c_scaling

	def _generate_random_sample_variables(self):
		pass





